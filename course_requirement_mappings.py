#! /usr/local/bin/python3
""" Populate tables of program requirements and mappings of courses to those requirements.
    A "program" is a requirement block with a block_type of MAJOR, MINOR, or CONC, but these blocks
    may reference OTHER blocks. DEGREE, LIBL, REQUISITE, and SCHOOL blocks are not handled here.
    [There are eight active LIBL blocks at Baruch, one active REQUISITE block at Baruch, and one
    active SCHOOL block ("Hold for future use") at BMCC.]
    Extract both the context (the label structure) and the specificity (how many alternatives there
    are) for each course.

    Block and CopyRules augment the top-level document when encountered.
    BlockType, noncourse, and Remarks are all irrelevant for present purposes.

    For Conditionals, the condition string serves as the name of the requirements; for bare Else
    clauses, the complement of the If clause's condition serves as the name.

    Specificity depends on the structure of the course_list, the group (and area) structure, and
    conditional factors.

    Assumes that all parse_trees for the institution are up to date.
    Ignores blocks that are not current and trees with an 'error' key.
"""

import os
import sys

import csv
import json

from argparse import ArgumentParser
from collections import namedtuple
from pgconnection import PgConnection
from dgw_parser import dgw_parser
from body_qualifiers import format_body_qualifiers
from header_productions import format_header_productions
from quarantine_manager import QuarantineManager

from pprint import pprint

DEBUG = os.getenv('DEBUG_REQUIREMENT_MAPPINGS')

quarantined_dict = QuarantineManager()
number_names = ['none', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve']

# Create list of active programs
active_programs = []
conn = PgConnection()
cursor = conn.cursor()
cursor.execute("""
    select institution, academic_plan, plan_type from cuny_programs where program_status = 'A'
    """)
for row in cursor.fetchall():
  plan_type = ('MAJOR' if row.plan_type == 'MAJ'
               else 'MINOR' if row.plan_type == 'MIN' else 'row.plan_type')
  active_programs.append((row.institution, plan_type, row.academic_plan))

cursor.execute("select institution, subplan, subplan_type from cuny_subplans where status = 'A'")
for row in cursor.fetchall():
  subplan_type = 'CONC' if row.subplan_type in ['MIN', 'OPT', 'SPC', 'TRK'] else row.subplan_type
  active_programs.append((row.institution, subplan_type, row.subplan))
conn.close()

# Information about active courses found in course lists.
ActiveCourse = namedtuple('ActiveCourse',
                          'course_id offer_nbr discipline catalog_number title credits '
                          'course_qualifiers')

# A Requirement’s context is a list of labels, conditions, and group info; active_courses is a list
# of ActiveCourse tuples. If the Requirement is disjunctive (OR), the length of the active_courses
# list gives the number of alternative courses that can satisfy the requirement (“may take”). But if
# the Requirement is conjunctive (AND), the course is required (“must take”). But note that this
# doesn’t tell whether the requirement itself is required or optional: that depends on its group and
# conditional contexts, if any.
Requirement = namedtuple('Requirement',
                         'institution requirement_id requirement_name '
                         'num_classes num_credits is_disjunctive active_courses '
                         'program_qualifiers requirement_qualifiers')


# emit()
# -------------------------------------------------------------------------------------------------
def emit(requirement: Requirement, program_qualifiers: list, context: list) -> None:
  """ Update the database.

      TABLE program_requirements (
        id serial primary key,
        institution text not null,
        requirement_id text not null,
        requirement_name text not null,
        num_courses_required text not null,
        course_alternatives text not null,
        conjunction text,
        num_credits_required text not null,
        credit_alternatives text not null,
        context jsonb not null,
        program_qualifiers jsonb not null,
        requirement_qualifiers jsonb not null, ...

      TABLE course_requirement_mappings (
        course_id integer,
        offer_nbr integer,
        program_requirement_id integer references program_requirements(id) on delete cascade,
        course_qualifiers jsonb not null, ...

  """
  if DEBUG:
    print(f'*** emit({requirement=}, {context=})', file=sys.stderr)

  assert len(context) > 0, f'emit with no context'
  conn = PgConnection()
  cursor = conn.cursor()

  # The first item in the context list is the name of the requirement.
  try:
    context_0 = context.pop(0)
    institution, requirement_id, block_type, block_value = context_0.split()
  except ValueError as ve:
    exit(f'“{context_0}” does not split into 4 parts')

  and_or = 'OR' if requirement.is_disjunctive else 'AND'
  course_alternatives = len(requirement.active_courses)

  # The number of credit alternatives can be a range 'cause of courses where there is a range.
  min_credit_alternatives = 0.0
  max_credit_alternatives = 0.0
  for course in requirement.active_courses:
    if ':' in course.credits:
      min_credits, max_credits = course.credits.split(':')
      min_credit_alternatives += float(min_credits)
      max_credit_alternatives += float(max_credits)
    else:
      num_credits = float(course.credits)
      min_credit_alternatives += num_credits
      max_credit_alternatives += num_credits
  if min_credit_alternatives == max_credit_alternatives:
    credit_alternatives = f'{min_credit_alternatives:0,.1f}'
  else:
    credit_alternatives = f'{min_credit_alternatives:0,.1f} to {max_credit_alternatives:0,.1f}'

  if DEBUG:
    print(institution, requirement_id, requirement.requirement_name, requirement.num_classes,
          course_alternatives, and_or, requirement.num_credits, credit_alternatives, context,
          file=sys.stderr)

  # See if the requirement already exists
  assert isinstance(requirement.requirement_name, str), (f'Not a string: '
                                                         f'{requirement.requirement_name}')
  cursor.execute(f"""
  select id
   from program_requirements
  where institution = %s
    and requirement_id = %s
    and requirement_name = %s
  """, (institution, requirement_id, requirement.requirement_name))
  if cursor.rowcount == 0:
    # Not yet: add it:
    # Note that the same requirement can appear in different contexts, such as when there are
    # different ways of satisfying it depending on a student's concentration. This is normal.
    cursor.execute(f"""insert into program_requirements values
                        (default, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on conflict do nothing
                        returning id
                   """, (institution, requirement_id, requirement.requirement_name,
                         requirement.num_classes, course_alternatives, and_or,
                         requirement.num_credits, credit_alternatives, json.dumps(context),
                         json.dumps(requirement.program_qualifiers),
                         json.dumps(requirement.requirement_qualifiers)))
    assert cursor.rowcount == 1

  program_requirement_id = int(cursor.fetchone().id)

  for course in requirement.active_courses:

    # Convert the with-clause expression string into a list
    if course.course_qualifiers is None:
      course_qualifiers = []
    else:
      course_qualifiers = course.course_qualifiers.split(',')

    # Check if the course mapping already exists
    cursor.execute(f"""select course_qualifiers
                         from course_requirement_mappings
                         where program_requirement_id = {program_requirement_id}
                           and course_id = {course.course_id}
                           and offer_nbr = {course.offer_nbr}
                    """)
    if cursor.rowcount > 0:
      # Yes, check for anomalies
      if cursor.rowcount == 1:
        row = cursor.fetchone()
        if row.course_qualifiers != course_qualifiers:
          print(f'{institution} {requirement_id} “{requirement.requirement_name}” '
                f'{row.course_qualifiers=} <> {course_qualifiers=}', file=sys.stderr)
      else:
        print(f'Impossible situation: {cursor.rowcount} rows in course_requirement_keys with'
              f'same {institution=}, {requirement_id=} {requirement.requirement_name=}',
              file=sys.stderr)
    else:
      # Safe to insert the mapping for this course
      cursor.execute(f"""insert into course_requirement_mappings values(
                         {course.course_id},
                         {course.offer_nbr},
                         {program_requirement_id},
                         %s) on conflict do nothing
                      """, (json.dumps(course_qualifiers), ))
      assert cursor.rowcount == 1
  conn.commit()
  conn.close()


# iter_list()
# -------------------------------------------------------------------------------------------------
def iter_list(items: list,
              program_qualifiers: list,
              requirement_qualifiers: list,
              calling_context: list) -> None:
  """
  """
  if DEBUG:
    print(f'*** iter_list({len(items)=}, {program_qualifiers}, {requirement_qualifiers=}, '
          f'{calling_context=})',
          file=sys.stderr)

  local_context = calling_context + []

  for value in items:
    if isinstance(value, list):
      iter_list(value, program_qualifiers, requirement_qualifiers, local_context)
    elif isinstance(value, dict):
      iter_dict(value, program_qualifiers, requirement_qualifiers, local_context)
    else:
      # Mebbe its a remark?
      print(f'iter_list: Neither list nor dict: {value=} {len(local_context)=}', file=sys.stderr)

  return None


# iter_dict()
# -------------------------------------------------------------------------------------------------
def iter_dict(item: dict,
              program_qualifiers: list,
              requirement_qualifiers: list,
              calling_context: list) -> None:
  """ If there is a course list, emit the context in which it occurs, the nature of the requirement,
      and the courses. The context is a list of labels (no remarks), augmented with information
      for conditionals (condition, if-true, if-false) and groups (m of n groups required; this is
      group # i of n)
      Otherwise, augment the context and process sub-lists and sub-dicts.
  """
  assert isinstance(item, dict), (f'{type(item)} is not dict in iter_dict. {item=}')
  if DEBUG:
    print(f'*** iter_dict({item.keys()=}, {program_qualifiers=}, {requirement_qualifiers=}, '
          f'{calling_context=})',
          file=sys.stderr)

  local_qualifiers = requirement_qualifiers + format_body_qualifiers(item)
  local_context = calling_context + []
  if 'label' in item.keys():
    requirement_name = item.pop('label')
  else:
    requirement_name = None

  ignored_keys = ['allow_credits', 'allow_classes', 'blocktype', 'copy_rules', 'remark']
  for key in item.keys():
    if key in ignored_keys:
      continue

    # Subsets, Groups, and Conditionals
    if key == 'subset':
      """ subset            : BEGINSUB
                  ( conditional_body    => conditional
                    | block             => ignore
                    | blocktype         => ignore
                    | class_credit_body => requirements
                    | copy_rules        => ignore
                    | course_list
                    | group_requirement => group_requirements
                    | noncourse         => ignore
                    | rule_complete     => ignore
                  )+
                  ENDSUB qualifier* (remark | label)*;
      """
      subset = item['subset']

      # There should be a non-empty label naming the subset requirement.
      subset_context = []
      if 'label' in subset.keys():
        label_str = subset.pop('label')
        if label_str:
          subset_context = [label_str]
      if len(subset_context) == 0:
        print(f'Subset with no label {calling_context}', file=sys.stderr)

      # There might be qualifiers: format will pop them
      subset_qualifiers = format_body_qualifiers(subset)
      # Now see what else is there
      for subset_key, subset_value in subset.items():
        if subset_key in ['conditional', 'course_list', 'group_requirements', 'requirements']:
          if isinstance(subset_value, dict):
            iter_dict(subset_value,
                      program_qualifiers,
                      local_qualifiers + subset_qualifiers,
                      local_context + subset_context)
          elif isinstance(subset_value, list):
            iter_list(subset_value,
                      program_qualifiers,
                      local_qualifiers + subset_qualifiers,
                      local_context + subset_context)
          else:
            print(f'{subset_key} is neither list nor dict in {local_context + subset_context}',
                  file=sys.stderr)

    if key == 'conditional':
      conditional = item['conditional']
      condition_label = []
      condition = conditional['condition']
      label = conditional['label']
      if label:
        condition_label.append(label)
      if_true = conditional['if_true']
      iter_list(if_true,
                program_qualifiers,
                local_qualifiers,
                local_context + condition_label + [f'{condition} is true'])
      # Else clause is optional
      if 'if_false' in conditional.keys():
        if_false = conditional['if_false']
        iter_list(if_false,
                  program_qualifiers,
                  local_qualifiers,
                  local_context + condition_label + [f'{condition} is not true'])

    if key == 'group_requirements':
      group_requirements = item['group_requirements']
      # Each group requirement provides its own context
      for group_requirement_dict in group_requirements:
        group_requirement = group_requirement_dict['group_requirement']
        group_context = []
        if 'label' in group_requirement.keys():
          group_context.append(group_requirement['label'])
        num_required = int(group_requirement['number'])
        if num_required < len(number_names):
          num_required = number_names[num_required]
        group_list = group_requirement['group_list']['groups']
        num_groups = len(group_list)
        if num_groups < len(number_names):
          num_groups = number_names[num_groups]
        group_context.append(f'Any {num_required} of {num_groups} groupa')
        for group in group_list:
          iter_dict(group, program_qualifiers, local_qualifiers,
                    local_context + [group_context])

    if key == 'course_list':
      # If there is a course_list, there's also info about num classes/credits,as well as whether
      # the list is disjunctive or conjunctive.

      # Class/Credit string
      min_credits = min_classes = num_credits = num_classes = None
      try:
        min_credits = item['min_credits']
        max_credits = item['max_credits']
        min_classes = item['min_classes']
        max_classes = item['max_classes']
        conjunction = item['conjunction']  # This is the credit/classes conjunction
      except KeyError as ke:
        print(f'{local_context=}: {ke=}', file=sys.stderr)

      # Build requirement description
      if min_credits:
        if min_credits == max_credits:
          num_credits = f'{float(min_credits):0.1f}'
        else:
          num_credits = f'{float(min_credits):0.1f}—{float(max_credits):0.1f}'
      else:
        num_credits = 0
      cr_sfx = '' if num_credits == '1.0' else 's'

      if min_classes:
        if min_classes == max_classes:
          num_classes = f'{min_classes}'
        else:
          num_classes = f'{min_classes}-{max_classes}'
      else:
        num_classes = 0
      cl_sfx = '' if num_classes == '1' else 'es'

      if num_classes and num_credits:
        assert conjunction, f'classes and credits with no conjunction'
        class_credit_str = f'{num_classes} class{cl_sfx} {conjunction} {num_credits} credit{cr_sfx}'
      elif num_classes:
        class_credit_str = f'{num_classes} class{cl_sfx}'
      elif num_credits:
        class_credit_str = f'{num_credits} credit{cr_sfx}'
      else:
        class_credit_str = ''

      # Process the course_list itself
      course_list = item['course_list']
      try:
        label_str = course_list['label']
      except KeyError as ke:
        label_str = None

      # If the course_list has a label and there is already a requirement name, emit the latter as a
      # separate part of the context.
      if requirement_name:
        if label_str:
          local_context.append(requirement_name)
          if DEBUG:
            print(f'Requirement Name: {requirement_name=} with {label_str=}', file=sys.stderr)
          requirement_name = label_str
      else:
        if label_str:
          requirement_name = label_str
        else:
          # There is no label and no requirement name. If the local context has anything other
          # than element 0, use the last item in local context as the requirement name
          if len(local_context) > 1:
            requirement_name = local_context.pop()
          else:
            # This looks like a bad Scribe block to me.
            requirement_name = 'NO NAME'

      try:
        list_type = course_list['list_type']
      except KeyError as ke:
        list_type = None

      active_courses = course_list['active_courses']
      assert list_type or len(active_courses) < 2, (f'No list_type for list length '
                                                    f'{len(active_courses)}')

      # The requirement starts with an empty list of courses ...
      if 'qualifiers' in course_list.keys():
        requirement_qualifiers = requirement_qualifiers + course_list['qualifiers']
      institution, requirement_id, *rest = local_context[0].split()
      requirement = Requirement._make([institution, requirement_id, requirement_name, num_classes,
                                      num_credits, list_type == 'OR', [],
                                      program_qualifiers, requirement_qualifiers])

      # ... and now add in the active courses that can/do satisfy the requirement.
      for active_course in active_courses:
        requirement.active_courses.append(ActiveCourse._make(active_course))

      # Add info for this requirement to the db
      emit(requirement, program_qualifiers, local_context)
  return


# __main__()
# =================================================================================================
if __name__ == '__main__':
  parser = ArgumentParser('Look up course list contexts')
  parser.add_argument('-f', '--force', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
  parser.add_argument('-p', '--period', default='current')
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
  parser.add_argument('-v', '--block_values', nargs='*', default=['csci-ba'])
  parser.add_argument('-ve', '--verbose', action='store_true', default=False)
  args = parser.parse_args()
  period = args.period.lower()

  # Allowable values for period
  assert period in ['all', 'current']

  # Specifiy block to process
  if args.requirement_id:
    institution = args.institutions[0].strip('10').upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')
    requirement_id = f'RA{int(requirement_id):06}'
    # Look up the block type and value
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f'select block_type, block_value, parse_tree from requirement_blocks'
                   f"  where institution = '{institution}'"
                   f"    and requirement_id = '{requirement_id}'")
    assert cursor.rowcount == 1, (f'Found {cursor.rowcount} block_type/block_value pairs '
                                  f'for {institution} {requirement_id}')
    block_type, block_value, parse_tree = cursor.fetchone()
    conn.close()
    # Iterate over the body, emitting db updates as a side effect.
    # There are spaces in some block values
    block_value = block_value.strip().replace(' ', '*')
    iter_list(parse_tree['body_list'],
              [f'{institution} {requirement_id} {block_type} {block_value}'])
    exit()

  conn = PgConnection()
  cursor = conn.cursor()
  institutions = [inst.upper().strip('01') for inst in args.institutions]
  if 'ALL' in institutions:
    cursor.execute('select code from cuny_institutions')
    institutions = [row.code.upper().strip('01') for row in cursor.fetchall()]
  for institution in institutions:
    institution = institution + '01'
    block_types = [arg.upper() for arg in args.block_types]
    for block_type in block_types:
      assert block_type in ['MAJOR', 'CONC', 'MINOR']
      program_type = 'concentration' if block_type == 'CONC' else block_type.lower()
      block_values = [value.upper() for value in args.block_values]
      if 'ALL' in block_values:
        cursor.execute(f"""
      select distinct block_value
        from requirement_blocks
       where institution = '{institution}'
         and block_type = '{block_type}'
      order by block_value
  """)
        block_values = [row.block_value.upper() for row in cursor.fetchall()
                        if not row.block_value.isdigit()
                        and '?' not in row.block_value]
      for block_value in block_values:
        if block_value.startswith('MHC') or block_value.isdigit():
          continue
        cursor.execute(f"""
      select requirement_id, period_stop, requirement_text, parse_tree
        from requirement_blocks
       where institution = '{institution}'
         and block_type = '{block_type}'
         and block_value ~* '^{block_value}$'
  """)
        for row in cursor.fetchall():
          # Skip miscreants and indifferents
          if quarantined_dict.is_quarantined((institution, row.requirement_id)):
            if args.verbose:
              print(f'{institution} {row.requirement_id} is quarantined.')
            continue
          if period == 'current' and row.period_stop != '99999999':
            if args.verbose:
              print(f'{institution} {row.requirement_id} is not currently offered.')
            continue

          if period == 'current':
            # Check if program or subprogram is active in CUNYfirst
            if (institution, block_type, block_value) in active_programs:
              pass
            else:
              if args.verbose:
                print(f'{institution} {row.requirement_id} {block_type} {block_value} is not '
                      f'currently active in CUNYfirst.')
              continue

          parse_tree = row.parse_tree
          if (len(parse_tree.keys()) == 0):
            if args.force:
              print(f'{institution} {row.requirement_id} {block_type} {block_value}: Parsing')
              parse_tree = dgw_parser(institution, block_type, block_value, period_range=period)
            else:
              print(f'{institution} {row.requirement_id} {block_type} {block_value} '
                    f'has not been parsed and “force” is False.')
              continue
          if 'error' in parse_tree.keys():
            err_msg = parse_tree['error']
            # Next stage: make this subject to args.verbose
            print(f'{institution} {row.requirement_id} {block_type} {block_value}: '
                  f'Parsing failure ({err_msg})')
            continue

          # Non-miscreant handler
          print(f'{institution} {row.requirement_id} {block_type} {block_value} {period}')
          header_list = parse_tree['header_list']
          body_list = parse_tree['body_list']

          # Clear out any requirements/mappings for this Scribe block that might be in place.
          # Deleting a requirement cascades to the mappings that reference it.
          # (During development, the same block might be processed multiple times.)
          cursor.execute(f"""delete from program_requirements
                             where institution = '{institution}'
                               and requirement_id = '{row.requirement_id}'
                          """)
          conn.commit()
          # Get block-level qualifiers from the header
          program_qualifiers = []
          requirement_qualifiers = []
          for item in header_list:
            if isinstance(item, dict):
              program_qualifiers += format_header_productiond(item)

          # Iterate over the body, emitting db updates as a side effect.
          # There are spaces in some block values
          block_value = block_value.strip().replace(' ', '*')
          iter_list(body_list,
                    program_qualifiers, requirement_qualifiers,
                    [f'{institution} {row.requirement_id} {block_type} {block_value}'])

  # Done
  conn.commit()
  conn.close()
