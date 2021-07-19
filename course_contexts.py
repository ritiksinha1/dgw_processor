#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?

    The goal is to extract both the context (the label structure) and the specificity (how many
    alternatives there are) for each course.

    Block, blocktype, copy_rules, noncourse, and remarks are all irrelevant for present purposes.
    Specificity depends on the structure of the course_list, the group (and area) structure, and
    conditional factors.

    This code is modeled on htmlificization, and assumes that the header and body lists in the
    database never need to be interpreted unless they are missing.
"""

import os
import sys

import csv
import json

from argparse import ArgumentParser
from collections import namedtuple
from pgconnection import PgConnection
from dgw_interpreter import dgw_interpreter
from quarantined_blocks import quarantine_dict

from pprint import pprint
from keystruct import key_struct

DEBUG = os.getenv('DEBUG_CONTEXTS')
log_file = open('./course_contexts.log', 'w')

# Information about active courses found in course lists.
ActiveCourse = namedtuple('ActiveCourse',
                          'course_id offer_nbr discipline catalog_number title credits qualifiers')

# A Requirement’s context is a list of labels, conditions, and group info; active_courses is a list
# of ActiveCourse tuples. If the Requirement is disjunctive (OR), the length of the active_courses
# list gives the number of alternative courses that can satisfy the requirement (“may take”). But if
# the Requirement is conjunctive (AND), the course is required (“must take”). But note that this
# doesn’t tell whether the requirement itself is required or optional: that depends on its group and
# conditional contexts, if any.
Requirement = namedtuple('Requirement',
                         'institution requirement_id requirement_name '
                         'num_classes num_credits is_disjunctive active_courses')


# emit()
# -------------------------------------------------------------------------------------------------
def emit(requirement: Requirement, context: list) -> None:
  """ Update the database.
      -- Program requirements
      --  The name is the name of the requirement (not the title of the program, which is in the
      --  requirement_blocks table)
      --  XXX_required: How many classes/credits are required
      --  XXX_alternatives: Totals for all the courses that can satisfy this requirement.
      --  conjunction: classes AND credits versus classes OR credits
      --  The context is a list of containing requirement names, super-names, super-super-names, ...
      create table program_requirements (
      id integer primary key,
      institution text,
      requirement_id text,
      requirement_name text,
      courses_required integer,
      course_alternatives integer,
      conjunction text,
      credits_required real,
      credit_alternatives real,
      context jsonb,
      foreign key (institution, requirement_id) references requirement_blocks
      );

      -- Map courses to program requirements.
      create table course_program_mappings (
      course_id integer,
      offer_nbr integer,
      requirement_id integer references program_requirements(id),
      qualifiers text,
      foreign key (course_id, offer_nbr) references cuny_courses,
      primary key (course_id, offer_nbr, requirement_id)
      );
  """
  if DEBUG:
    print(f'*** emit({requirement=}, {context=})', file=sys.stderr)

  assert len(context) > 0, f'emit with no context'
  conn = PgConnection()
  cursor = conn.cursor()
  institution, requirement_id, block_type, block_value = context.pop(0).split()

  and_or = 'OR' if requirement.is_disjunctive else 'AND'
  course_alternatives = len(requirement.active_courses)
  credit_alternatives = sum([float(course.credits) for course in requirement.active_courses])

  print(institution, requirement_id, requirement.requirement_name, requirement.num_classes,
        course_alternatives, and_or, requirement.num_credits, credit_alternatives, context)
  cursor.execute(f"""delete from program_requirements
                     where institution = '{institution}'
                       and requirement_id = 'requirement_id'
                  """)
  cursor.execute("""insert into program_requirements values
                      (default, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id
                 """, (institution, requirement_id, requirement.requirement_name,
                       requirement.num_classes, course_alternatives, and_or,
                       requirement.num_credits, credit_alternatives, json.dumps(context)))
  assert cursor.rowcount == 1
  program_requirement_id = int(cursor.fetchone().id)
  for course in requirement.active_courses:
    cursor.execute(f"""insert into course_program_mappings values(
                       {course.course_id},
                       {course.offer_nbr},
                       {program_requirement_id},
                       '{course.qualifiers}') on conflict do nothing
                    """)
    if cursor.rowcount == 0:
      cursor.execute(f"""select qualifiers
                           from course_program_mappings
                           where program_requirement_id = {program_requirement_id}
                             and course_id = {course.course_id}
                             and offer_nbr = {course.offer_nbr}
                      """)
      old_qualifiers = cursor.fetchone().qualifiers
      new_qualifiers = course.qualifiers
      print(f'{institution} {requirement_id} {requirement.requirement_name} duplicated: '
            f'{old_qualifiers=} {new_qualifiers=}', file=log_file)
  conn.commit()
  conn.close()


# iter_list()
# -------------------------------------------------------------------------------------------------
def iter_list(items: list, calling_context: list) -> None:
  """
  """
  if DEBUG:
    print(f'*** iter_list({len(items)=}, {calling_context=})', file=sys.stderr)

  local_context = calling_context + []

  for value in items:
    if isinstance(value, list):
      iter_list(value, local_context)
    elif isinstance(value, dict):
      iter_dict(value, local_context)
    else:
      print(f'iter_list: Neither list nor dict: {value=} {len(local_context)=}', file=sys.stderr)

  return None


# iter_dict()
# -------------------------------------------------------------------------------------------------
def iter_dict(item: dict, calling_context: list) -> None:
  """ If there is a course list, emit the context in which it occurs, the nature of the requirement,
      and the courses.
      Otherwise, augment the context and process sub-lists and sub-dicts.
  """
  if DEBUG:
    print(f'*** iter_dict({item.keys()=}, {calling_context=})', file=sys.stderr)

  local_context = calling_context + []

  # Subsets, Groups, and Conditionals add to the local context
  try:
    subset = item.pop('subset')
    label_str = subset.pop('label')
    if label_str:
      local_context += [label_str]
      print(f'\nSubset Name: {label_str}', file=sys.stderr)
    requirements = subset.pop('requirements')
    print(f'{len(requirements)} Requirements', file=sys.stderr)
    iter_list(requirements, local_context)
    assert len(item) == 0
  except KeyError as ke:
    if ke.args[0] != 'subset':
      local_context += [f'Rule Subset “{ke.args[0]}” Not Implemented Yet']

  try:
    conditional = item.pop('conditional')
    conditional_str = 'Conditional Not Implemented Yet'
    iter_dict(conditional, local_context + [conditional_str])
  except KeyError as ke:
    pass

  try:
    groups = item.pop('group')
    assert len(groups) == 1
    group = groups[0]
    assert isinstance(group, dict)
    label_str = group['label']
    num_required = group['num_groups_required']
    num_groups = len(group['group_items'])
    suffix = '' if int(num_groups) == 1 else 's'
    group_str = f'{num_required} of {num_groups} group{suffix}'
    print(f'\nGroup Requirement: {group_str}', file=sys.stderr)
    iter_dict(group, local_context + [group_str])
  except KeyError as ke:
    if ke.args[0] != 'group':
      print(f'Group KeyError: {ke=}', file=sys.stderr)

  try:
    requirement_name = item.pop('label')
  except KeyError as ke:
    requirement_name = None

  if 'course_list' in item.keys():
    # If there is a course_list, there's also info about num classes/credits,as well as whether
    # the list is disjunctive of conjunctive.
    try:
      min_credits = item.pop('min_credits')
      max_credits = item.pop('max_credits')
      min_classes = item.pop('min_classes')
      max_classes = item.pop('max_classes')
      conjunction = item.pop('conjunction')  # This is the credit/classes conjunction
    except KeyError as ke:
      exit(f'{local_context=}: {ke=}')

    # Build requirement description
    if min_credits:
      if min_credits == max_credits:
        num_credits = f'{float(min_credits):0.1f}'
      else:
        num_credits = f'{float(min_credits):0.1f}-{float(max_credits):0.1f}'
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
      class_credit_str = None

    # Discard course_list['allow_xxx'] entries.
    item.pop('allow_credits')
    item.pop('allow_classes')

    # Process the course_list itself
    course_list = item.pop('course_list')
    try:
      label_str = course_list['label']
    except KeyError as ke:
      label_str = None

    # If the list has a name and there is already a requirement name, emit the latter as a
    # separate part of the context.
    if requirement_name:
      if label_str:
        local_context.append(requirement_name)
        print(f'Requirement Name: {requirement_name=} with {label_str=}', file=sys.stderr)
        requirement_name = label_str
    else:
      if label_str:
        requirement_name = label_str
      else:
        requirement_name = 'NO NAME'

    try:
      list_type = course_list['list_type']
    except KeyError as ke:
      list_type = None

    active_courses = course_list['active_courses']
    assert list_type or len(active_courses) < 2, (f'No list_type for list length '
                                                  f'{len(active_courses)}')

    # The requirement starts with an empty list of courses ...
    institution, requirement_id, *rest = local_context[0].split()
    requirement = Requirement._make([institution, requirement_id, requirement_name, num_classes,
                                    num_credits, list_type == 'OR', []])
    # ... and now add in the active courses that can/do satisfy the requirement.
    for active_course in active_courses:
      requirement.active_courses.append(ActiveCourse._make(active_course))
    suffix = ' satisfies' if len(requirement.active_courses) == 1 else 's satisfy'
    print(f'\n{len(requirement.active_courses)} active course{suffix} '
          f'“{requirement.requirement_name}”\n  {class_credit_str}',
          file=sys.stderr)
    if len(requirement.active_courses) > 1:
      any_all = 'Any' if requirement.is_disjunctive else 'All'
      print(f'  {any_all} of the following courses:', file=sys.stderr)
    for active_course in requirement.active_courses:
      if active_course.qualifiers:
        qualifiers_str = f' with {active_course.qualifiers}'
      else:
        qualifiers_str = ''
      print(f'  {active_course.course_id}:{active_course.offer_nbr} {active_course.discipline} '
            f'“{active_course.title}”{qualifiers_str}', file=sys.stderr)
    emit(requirement, local_context)

  # That should be all we‘re intersted in, but double-check
  for key, value in item.items():
    if isinstance(value, list):
      iter_list(value, local_context)
    elif isinstance(value, dict):
      iter_dict(value, local_context)
    else:
      print(f'iter_dict: Not label, condition, group, list, or dict: {key=} {value=}',
            file=sys.stderr)

  return


# __main__()
# =================================================================================================
if __name__ == '__main__':
  parser = ArgumentParser('Look up course list contexts')
  parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
  parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
  parser.add_argument('-v', '--block_values', nargs='*', default=['csci-ba'])
  parser.add_argument('-f', '--force', action='store_true', default=False)
  parser.add_argument('-p', '--period', default='current')
  args = parser.parse_args()
  period = args.period.lower()

  # Allowable values for period
  assert period in ['all', 'current']

  with open('./debug', 'w') as debug:
    conn = PgConnection()
    cursor = conn.cursor()
    institutions = [inst.upper().strip('01') for inst in args.institutions]
    for institution in institutions:
      institution = institution + '01'
      block_types = [arg.upper() for arg in args.block_types]
      for block_type in block_types:
        assert block_type in ['MAJOR', 'CONC', 'MINOR']
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
        select requirement_id, period_stop, requirement_text, header_list, body_list
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
           and block_value ~* '^{block_value}$'
    """)
          for row in cursor.fetchall():
            if (institution, row.requirement_id) in quarantine_dict:
              print(f'{institution}, {row.requirement_id} is quarantined')
              continue
            if period == 'current' and row.period_stop != '99999999':
              continue
            print(f'{institution} {block_type} {block_value} {period}')
            header_list, body_list = (row.header_list, row.body_list)
            if (len(header_list) == 0 and len(body_list) == 0) or args.force:
              print(f'{len(header_list)=}] {args.force=} Reinterpreting')
              header_list, body_list = dgw_interpreter(institution, block_type, block_value,
                                                       period_range=period)

            print(f'*** {institution} {block_type} {block_value} {period}', file=debug)
            pprint(body_list, stream=debug)
            # key_struct(body_list)
            print('\n', file=debug)

            # Iterate over the body
            iter_list(body_list, [f'{institution} {row.requirement_id} {block_type} {block_value}'])
