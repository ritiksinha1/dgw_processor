#! /usr/local/bin/python3
""" List program requirements and courses that satisfy them.
"""

import csv
import os
import json
import psycopg
import sys

from argparse import ArgumentParser
from collections import namedtuple, defaultdict
from pprint import pprint
from psycopg.rows import namedtuple_row
from recordclass import recordclass
from typing import Any
from uuid import uuid4 as uuid  # debugging aid

from coursescache import courses_cache
from dgw_parser import parse_block

from quarantine_manager import QuarantineManager

quarantine_dict = QuarantineManager()

BlockInfo = recordclass('BlockInfo',
                        'institution requirement_id block_type block_value block_title '
                        'class_credits max_transfer min_residency min_grade min_gpa')
SubplanInfo = namedtuple('SubplanInfo', 'type description cip_code hegis_code')


""" Output Files
      debug_file:         Info written during debugging (to avoid stdout/stderr)
      log_file:           Record of requirements processed successfully. Bigger is better!
      fail_file:          Blocks that failed for one reason or another
      todo_file:          Record of known requirements not yet handled. Smaller is better!
      programs_file:      Spreadsheet of info about majors, minors, and concentrations
      requirements_file:  Spreadsheet of program requirement names
      mapping_file        Spreadsheet of course-to-requirements mappings

"""
debug_file = open(f'{__file__.replace(".py", ".debug.txt")}', 'w')
log_file = open(f'{__file__.replace(".py", ".log.txt")}', 'w')
fail_file = open(f'{__file__.replace(".py", ".fail.txt")}', 'w')
todo_file = open(f'{__file__.replace(".py", ".todo.txt")}', 'w')
no_courses_file = open(f'{__file__.replace(".py", ".no_courses.txt")}', 'w')

programs_file = open(f'{__file__.replace(".py", ".programs.csv")}', 'w', newline='')
requirements_file = open(f'{__file__.replace(".py", ".requirements.csv")}', 'w', newline='')
mapping_file = open(f'{__file__.replace(".py", ".course_mappings.csv")}', 'w', newline='')

programs_writer = csv.writer(programs_file)
requirements_writer = csv.writer(requirements_file)
map_writer = csv.writer(mapping_file)


def dict_factory():
  """ Support for three index levels, as in courses_by_institution and subplans_by_institution.
  """
  return defaultdict(dict)


courses_by_institution = defaultdict(dict_factory)
subplans_by_institution = defaultdict(dict_factory)

requirement_index = 0

# =================================================================================================


# letter_grade()
# -------------------------------------------------------------------------------------------------
def letter_grade(grade_point: float) -> str:
  """ Convert a passing grade_point value to a passing letter grade.
      Treat anything less than 1.0 as "Any" passing grade, and anything above 4.3 as "A+"
        GPA Letter
        4.3    A+
        4.0    A
        3.7    A-
        3.3    B+
        3.0    B
        2.7    B-
        2.3    C+
        2.0    C
        1.7    C-
        1.3    D+
        1.0    D
        0.7    D- => "Any"
  """
  if grade_point < 1.0:
    return 'Any'
  else:
    letter_index, suffix_index = divmod((10 * grade_point) - 7, 10)
  letter = ['D', 'C', 'B', 'A'][min(int(letter_index), 3)]
  suffix = ['-', '', '+'][min(int(suffix_index / 3), 2)]
  return letter + suffix


# map_courses()
# -------------------------------------------------------------------------------------------------
def map_courses(institution: str, requirement_id: str, requirement_name: str, context_list: list,
                requirement_dict: dict):
  """ Write courses and their With clauses to the map file.
      Object returned by courses_cache():
        CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr block_title credits career')

      Each program requirement has a unique key based on institution, requirement_id, block_title,
      and context list.

Programs: Handled by process_block()
Institution, Requirement ID, Type, Code, Total, Max Transfer, Min Residency, Min Grade, Min GPA

Requirements: Handled here
Institution, Requirement ID, Requirement Key, Name, Context, Grade Restriction, Transfer Restriction

Course Mappings: Handled here
Requirement Key, Course ID, Career, Course, With

  """

  # The requirement_index is used to join the requirements and the courses that map to them.
  global requirement_index
  requirement_index += 1

  # Find the course_list in the requirement_dict.
  try:
    course_list = requirement_dict['course_list']
  except KeyError:
    # Sometimes the course_list _is_ the requirement. In these cases, all courses in the list are
    # required.
    course_list = requirement_dict
    # Do we need to add min_classes, and all the other class_credit keys to the requirement_dict?
    print(institution, requirement_id, f'Requirement is course_list', file=todo_file)

  # Filter out duplicated courses: people scribe course lists that include the same course(s) more
  # than once.
  courses_set = set()
  for course_area in range(len(course_list['scribed_courses'])):
    for course_tuple in course_list['scribed_courses'][course_area]:
      # Unless there is a With clause, skip "any course" wildcards (@ @)
      if ['@', '@', None] == course_tuple:
        continue
      discipline, catalog_number, with_clause = course_tuple
      if with_clause is not None:
        with_clause = f'With ({with_clause})'

      courses_dict = courses_cache((institution, discipline, catalog_number))
      for key, value in courses_dict.items():
        courses_set.add(f'{value.course_id:06}:{value.offer_nbr}|{value.career}|'
                        f'{key}: {value.title}|{with_clause}')
    requirement_dict['num_courses'] = len(courses_set)
    for course in courses_set:
      map_writer.writerow([requirement_index] + course.split('|'))

  if requirement_dict['num_courses'] == 0:
    print(institution, requirement_id, requirement_name, file=no_courses_file)
  else:
    context_col = {'context': context_list,
                   'requirement': requirement_dict}
    # pprint(context_col, stream=debug_file)
    data_row = [institution, requirement_id, requirement_index, requirement_name,
                json.dumps(context_col, ensure_ascii=False)]
    requirements_writer.writerow(data_row)


# get_restrictions()
# -------------------------------------------------------------------------------------------------
def get_restrictions(node: dict) -> dict:
  """ Return qualifiers that might affect transferability.
  """

  assert isinstance(node, dict)
  return_dict = dict()
  # The maxtransfer restriction puts a limit on the number of classes or credits that can be
  # transferred, possibly with a list of "types" for which the limit applies. I think the type names
  # have to come from a dgw table somewhere.
  try:
    transfer_dict = node.pop('maxtransfer')
    return_dict['maxtransfer'] = transfer_dict
  except KeyError:
    pass

  # The mingrade restriction puts a limit on the minimum required grade for all courses in a course
  # list. It’s a float (like a GPA) in Scribe, but is replaced with a letter grade here.
  mingrade_dict = {}
  try:
    mingrade_dict = node.pop('mingrade')
    number = float(mingrade_dict['number'])
    grade_str = letter_grade(number)
    return_dict['mingrade'] = grade_str
  except KeyError:
    pass

  return return_dict


# process_block()
# =================================================================================================
def process_block(row: namedtuple, context_list: list = []):
  """ Given (parts of) a row from the requirement_blocks db table, traverse the header and body
      lists.
  """
  # Augment db info with default values for class_credits max_transfer min_residency min_grade
  # min_gpa
  try:
    enrollment = active_blocks[(row.institution, row.requirement_id)]
  except KeyError:
    print(row.institution, row.requirement_id, 'Not an active block', file=fail_file)
    return

  block_info = BlockInfo._make(row[0:5] + ('', '', '', '', ''))

  # traverse_header() is a one-pass procedure that updates the block_info record with parameters
  # found in the header list.
  try:
    header_list = row.parse_tree['header_list']
    if len(header_list) > 0:
      traverse_header(block_info, header_list)
    else:
      print(row.institution, row.requirement_id, 'Empty Header', file=log_file)
  except KeyError:
    print(row.institution, row.requirement_id, 'Missing Header', file=fail_file)

  programs_writer.writerow([f'{block_info.institution[0:3]}',
                            f'{block_info.requirement_id}',
                            f'{block_info.block_type}',
                            f'{block_info.block_value}',
                            f'{block_info.block_title}',
                            f'{block_info.class_credits}',
                            f'{block_info.max_transfer}',
                            f'{block_info.min_residency}',
                            f'{block_info.min_grade}',
                            f'{block_info.min_gpa}'])

  # traverse_body() is a recursive procedure that handles nested requirements, so to start, it has
  # to be primed with the root node of the body tree: the body_list. process_block() itself may be
  # invoked from within traverse_body() to handle block, blocktype and copy_rules constructs.
  try:
    body_list = row.parse_tree['body_list']
    if len(body_list) > 0:
      # Use block_info as a marker for a new (nested) block
      traverse_body(body_list, context_list + [{'block_info': block_info._asdict()}])
    else:
      print(row.institution, row.requirement_id, 'Empty Body', file=log_file)
  except KeyError as ke:
    print(row.institution, row.requirement_id, 'Missing Body', file=fail_file)


# traverse_header()
# =================================================================================================
def traverse_header(block_info: namedtuple, header_list: list) -> None:
  """ Extract program-wide qualifiers: MinGrade (but not MinGPA) and residency requirements,
  """

  institution, requirement_id, *_ = (block_info.institution, block_info.requirement_id)
  for header_item in header_list:

    if not isinstance(header_item, dict):
      print(header_item, 'is not a dict', file=sys.stderr)

    else:
      for key, value in header_item.items():
        match key:

          case 'header_class_credit':
            if label_str := value['label']:
              print(f'{institution} {requirement_id}: Class/Credit label: {label_str}',
                    file=debug_file)
            min_classes = None if value['min_classes'] is None else int(value['min_classes'])
            min_credits = None if value['min_credits'] is None else float(value['min_credits'])
            max_classes = None if value['max_classes'] is None else int(value['max_classes'])
            max_credits = None if value['max_credits'] is None else float(value['max_credits'])
            assert not (min_credits and max_credits is None), f'{min_credits} {max_credits}'
            assert not (min_credits is None and max_credits), f'{min_credits} {max_credits}'
            assert not (min_classes and max_classes is None), f'{min_classes} {max_classes}'
            assert not (min_classes is None and max_classes), f'{min_classes} {max_classes}'
            class_credit_list = []
            if min_classes and max_classes:
              if min_classes == max_classes:
                class_credit_list.append(f'{max_classes} classes')
              else:
                class_credit_list.append(f'{min_classes}-{max_classes} classes')

            if min_credits and max_credits:
              if min_credits == max_credits:
                class_credit_list.append(f'{max_credits:.1f} credits')
              else:
                class_credit_list.append(f'{min_credits:.1f}-{max_credits:.1f} credits')
            block_info.class_credits = ' and '.join(class_credit_list)

          case 'conditional':
            # There could be a block requirement and/or a class_credit requirement; perhaps others.
            print(f'{institution} {requirement_id} Conditional in header', file=todo_file)
            pass

          case 'copy_rules':
            print(f'{institution} {requirement_id}: Copy Rules in header', file=todo_file)
            pass

          case 'header_lastres':
            pass

          case 'header_maxclass':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Max Classes in header', file=todo_file)
            pass

          case 'header_maxcredit':
            # THERE ARE 1357 OF THESE; THEY HAVE COURSE LISTS
            print(f'{institution} {requirement_id} Max Credits in header', file=todo_file)
            pass

          case 'header_maxpassfail':
            pass

          case 'header_maxperdisc':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Max PerDisc in header', file=todo_file)
            pass

          case 'header_maxtransfer':
            if label_str := value['label']:
              print(f'{institution} {requirement_id} Label in header MaxTransfer', file=todo_file)
            number = float(value['maxtransfer']['number'])
            class_or_credit = value['maxtransfer']['class_or_credit']
            if class_or_credit == 'credit':
              block_info.max_transfer = f'{number:3.1f} credits'
            else:
              suffix = '' if int(number) == 1 else 'es'
              block_info.max_transfer = f'{int(number):3} class{suffix}'

          case 'header_minclass':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Min Classes in header', file=todo_file)
            pass

          case 'header_mincredit':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Min Credits in header', file=todo_file)
            pass

          case 'header_mingpa':
            if label_str := value['label']:
              print(f'{institution} {requirement_id} Label in header MinGPA', file=todo_file)
            mingpa = float(value['mingpa']['number'])
            block_info.min_gpa = f'{mingpa:4.2f}'

          case 'header_mingrade':
            if label_str := value['label']:
              print(f'{institution} {requirement_id} Label in header MainGrade', file=todo_file)
            block_info.min_grade = letter_grade(float(value['mingrade']['number']))

          case 'header_minperdisc':
            pass

          case 'header_minres':
            min_classes = value['minres']['min_classes']
            min_credits = value['minres']['min_credits']
            # There must be a better way to do an xor check ...
            match (min_classes, min_credits):
              case [None, None]:
                print(f'Invalid minres {block_info}', file=sys.stderr)
              case [None, credits]:
                block_info.min_residency = f'{float(credits):.1f} credits'
              case [classes, None]:
                block_info.min_residency = f'{int(classes)} classes'
              case _:
                print(f'Invalid minres {block_info}', file=sys.stderr)

          case 'header_maxterm' | 'header_minterm' | 'noncourse' | 'optional' | 'proxy_advice' | \
               'remark' | 'rule_complete' | 'standalone' | 'header_share':
            # Intentionally ignored
            pass

          case _:
            print(f'{institution} {requirement_id}: Unexpected {key} in header', file=sys.stderr)

  return


# traverse_body()
# =================================================================================================
def traverse_body(node: Any, context_list: list) -> None:
  """ Extract Requirement names and course lists from body rules. Unlike traverse_header(), which
      makes a single pass over all the elements in the header list for a Scribe Block, this is a
      recursive function to handle nested requirements.

      Element 0 of the context list is always information about the block, including header
      restrictions: MaxTransfer, MinResidency, MinGrade, and MinGPA. (See traverse_header(), which
      set this up.)

      If there is a label, that becomes the requirement_name to add to the context_list when
      entering sub-dicts.

      Block, Conditional, CopyRules, Groups, and Subsets all have to be handled individually here.

      If a node's subdict has a course_list, that becomes an output.

        body_rule       : block
                        | blocktype
                        | class_credit
                        | conditional
                        | course_list_rule
                        | copy_rules
                        | group_requirement
                        | noncourse
                        | proxy_advice
                        | remark
                        | rule_complete
                        | subset
  """
  # Containing Block Context.
  # Use last block_info item in the context_list
  for ctx in reversed(context_list):
    try:
      block_info = ctx['block_info']
      institution = block_info['institution']
      requirement_id = block_info['requirement_id']
      block_type = block_info['block_type']
      block_value = block_info['block_value']
      block_title = block_info['block_title']
      break
    except KeyError as ke:
      continue

  # Handle lists
  if isinstance(node, list):
    for item in node:
      traverse_body(item, context_list)

  # A dict should have one key that identifies the requirement type, and a sub-dict that gives the
  # details about that requirement, including the label that gives it its name.
  elif isinstance(node, dict):
    node_keys = list(node.keys())
    if num_keys := len(node_keys) != 1:
      print(f'Node with {num_keys} keys: {node_keys}', sys.stderr)

    requirement_type = node_keys[0]
    requirement_value = node[requirement_type]
    if isinstance(requirement_value, dict):
      context_dict = get_restrictions(node[requirement_type])
      try:
        requirement_name = node[requirement_type].pop('label')
      except KeyError:
        requirement_name = None
      if context_dict:
        context_dict['name'] = requirement_name
        requirement_context = [context_dict]
      else:
        requirement_context = []

      match requirement_type:

        case 'block':
          print(institution, requirement_id, 'block', file=log_file)
          id = str(uuid())[0:8].upper()
          print(f'\nBLOCK {id} ENTER')

          # The number of blocks has to be 1
          number = int(requirement_value['number'])
          assert number == 1

          args = [requirement_value['institution'],
                  requirement_value['block_type'],
                  requirement_value['block_value']]
          with psycopg.connect('dbname=cuny_curriculum') as conn:
            with conn.cursor(row_factory=namedtuple_row) as cursor:
              blocks = cursor.execute("""
              select institution, requirement_id, block_type, block_value, title as block_title,
                     parse_tree
                from requirement_blocks
               where institution = %s
                 and block_type = %s
                 and block_value = %s
                 and period_stop ~* '^9'
              """, args)

              if cursor.rowcount == 0:
                print(f'{institution} {requirement_id} Block: found no active blocks',
                      file=fail_file)
                return

              num_blocks = cursor.rowcount
              block_num = 0
              for row in cursor:
                print(f'BLOCK {id} FETCH {row.requirement_id}')
                block_num += 1
                if num_blocks == 1:
                  process_block(row, context_list + requirement_context)
                else:
                  choice_context = {'choice': {'num_choices': num_blocks,
                                               'num_required': number,
                                               'index': block_num,
                                               'block_type': args[1]}}
                  print(institution, requirement_id, choice_context, file=debug_file)
                  process_block(row,
                                context_list + requirement_context + [choice_context])
          print(f'BLOCK {id} EXIT')
          return

        case 'blocktype':
          print(institution, requirement_id, 'blocktype', file=log_file)
          # No observed cases where the number of blocks is other than one and the type of block is
          # other than Concentration. But in two cases (LEH 1298 and 1300), the containing block
          # type is CONC instead of MAJOR.
          number = int(node[requirement_type]['number'])
          if number != 1:
            print(institution, requirement_id, f'blocktype with number ({number}) not equal 1',
                  file=todo_file)
            return
          req_type = node[requirement_type]['block_type']
          # if institution == 'LEH01' and requirement_id == 'RA002329':
          #   print(f'{institution} {requirement_id} {block_type} {block_value}: {req_type}')
          #   for key, value in subplans_by_institution[institution][block_value].items():
          #     print(f'{key:12}: {value}')

        case 'class_credit':
          print(institution, requirement_id, 'class_credit', file=log_file)
          # This is where course lists turn up, in general.
          try:
            if course_list := node[requirement_type]['course_list']:
              map_courses(institution, requirement_id, block_title,
                          context_list + requirement_context, node[requirement_type])
          except KeyError:
            # Course List is an optional part of ClassCredit
            return

        case 'conditional':
          import pdb; pdb.set_trace()
          print(institution, requirement_id, 'conditional', file=log_file)
          print('\n', node['conditional'])

          # Use the condition as the pseudo-name of this requirement
          # UNABLE TO HANDLE RULE_COMPLETE UNTIL THE CONDITION IS EVALUATED
          condition = node[requirement_type]['condition']
          for if_true_dict in node[requirement_type]['if_true']:
            id = str(uuid())[0:8].upper()
            print(f'\nIF_TRUE_DICT {id} ENTER')
            print(if_true_dict)
            condition_dict = {'name': 'if_true', 'condition': condition}
            condition_list = [condition_dict]
            traverse_body(if_true_dict, context_list + condition_list)
            print(f'IF_TRUE_DICT {id} RETURN')
          try:
            id = str(uuid())[0:8].upper()
            for if_false_dict in node[requirement_type]['if_false']:
              print(f'\nIF_FALSE_DICT {id} ENTER')
              print(if_false_dict)
              condition_dict = {'name': 'if_false', 'condition': condition}
              condition_list = [condition_dict]
              traverse_body(if_true_dict, context_list + condition_list)
              print(f'IF_FALSE_DICT {id} RETURN')
          except KeyError:
            # Scribe Else clause is optional

            pass
          return

        case 'copy_rules':
          print(institution, requirement_id, 'copy_rules', file=log_file)
          # Use the title of the block as the label.
          with psycopg.connect('dbname=cuny_curriculum') as conn:
            with conn.cursor(row_factory=namedtuple_row) as cursor:
              cursor.execute("""
              select institution, requirement_id, block_type, block_value, title as block_title,
                     parse_tree
                from requirement_blocks
               where institution = %s
                 and requirement_id = %s
                 and period_stop ~* '^9'
              """, (node[requirement_type]['institution'],
                    node[requirement_type]['requirement_id']))
              if cursor.rowcount != 1:
                print(f'{institution} {requirement_id} CopyRules found {cursor.rowcount} active '
                      f'blocks', file=fail_file)
                return
              row = cursor.fetchone()
              is_circular = False
              for context_dict in context_list:
                try:
                  if f'{row.institution} {row.requirement_id}' == context_dict['requirement_block']:
                    print(institution, requirement_id, 'Circular CopyRules', file=fail_file)
                    is_circular = True
                except KeyError:
                  pass
              if not is_circular:
                process_block(row, context_list)
          return

        case 'course_list_rule':
          print(institution, requirement_id, 'course_list_rule', file=log_file)
          # There might be a remark associated with the course list (ignored, but could be added to
          # context)

          try:
            if course_list := requirement_value['course_list']:
              map_courses(institution, requirement_id, block_title,
                          context_list + requirement_context, requirement_value)
          except KeyError:
            # Can't have a Course List Rule w/o a course list
            print(f'{institution} {requirement_id}: Course List Rule w/o a Course List',
                  file=sys.stderr)
          return

        case 'group_requirements':
          # Group requirements is a list, so it should not show up here.
          exit(f'{institution} {requirement_id} Error: unexpected group_requirements',
               file=sys.stderr)

        case 'rule_complete':
          print(institution, requirement_id, 'rule_complete', file=log_file)
          # is_complete may be T/F
          # rule_tag is followed by a name-value pair. If the name is RemarkJump, the value is a URL
          # for more info. Otherwise, the name-value pair is used to control formatting of the rule.
          # This happens only inside conditionals, where the idea will be to look at what whether
          # it's in the true or false leg, what the condition is, and whether this is True or False
          # to infer what requirement must or must not be met. We're looking at YOU, Lehman ACC-BA.

          print(f'{institution} {requirement_id} RuleComplete in body', file=todo_file)
          return

        case 'course_list':
          print(institution, requirement_id, 'course_list', file=log_file)
          map_courses(institution, requirement_id, block_title, context_list + requirement_context,
                      requirement_value)
          return

        case 'group_requirement':
          print(institution, requirement_id, 'group_requirement', file=log_file)
          number = int(requirement_value['number'])
          groups = requirement_value['group_list']['groups']
          num_groups = len(groups)
          group_num = 0
          for group in groups:
            group_num += 1
            group_name = group.pop('label')
            context_dict = {'name': group_name}
            context_dict['group_number'] = group_num
            context_dict['num_groups'] = num_groups
            context_dict['num_required'] = number
            group_context = [context_dict]
            group_context = requirement_context + group_context

            assert len(list(group.keys())) == 1

            key, value = group.popitem()
            match key:

              case 'block':
                print(institution, requirement_id, 'Group block', file=log_file)
                try:
                  block_name = value['label']
                  block_num_required = int(value['number'])
                  block_type = value['block_type']
                  block_value = value['block_value']
                  block_institution = value['institution']
                  with psycopg.connect('dbname=cuny_curriculum') as conn:
                    with conn.cursor(row_factory=namedtuple_row) as cursor:
                      cursor.execute("""
                      select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title as block_title,
                                  parse_tree
                             from requirement_blocks
                            where institution = %s
                              and block_type =  %s
                              and block_value = %s
                              and period_stop ~* '^9'
                      """, [institution, block_type, block_value])
                      if cursor.rowcount != block_num_required:
                        # HOW TO HANDLE THIS?
                        suffix = '' if cursor.rowcount == 1 else 's'
                        print(f'{institution} {requirement_id} Block requirement found '
                              f'{cursor.rowcount} row{suffix} ({block_num_required} needed)',
                              file=todo_file)
                        return
                      else:
                        for row in cursor:
                          process_block(row, context_list + group_context)
                        return
                except KeyError as ke:
                  exit(ke)

              case 'blocktype':
                print(institution, requirement_id, 'Group blocktype', file=todo_file)
                pass

              case 'class_credit':
                print(institution, requirement_id, 'Group class_credit', file=log_file)
                # This is where course lists turn up, in general.
                try:
                  map_courses(institution, requirement_id, block_title,
                              context_list + group_context, value)
                except KeyError as ke:
                  # Course List is an optional part of ClassCredit
                  pass

                return

              case 'course_list_rule':
                pass

              case 'group_requirements':
                # Don't log this: it's an artifact because group requirements appear as lists even
                # when there is only one group requirement.
                assert isinstance(value, list)
                for group_requirement in value:
                  traverse_body(value, context_list + group_context)
                return

              case 'noncourse':
                pass
              case 'rule_complete':
                pass
              case _:
                exit(f'{institution} {requirement_id} Unexpected Group {key}')

            print(f'{institution} {requirement_id} Unhandled Key {key} {type(value)}',
                  file=todo_file)

          return

        case 'subset':
          # ---------------------------------------------------------------------------------------
          # Process the valid rules in the subset

          # Track MaxTransfer and MinGrade restrictions (qualifiers).
          subset_name = requirement_name
          context_dict = get_restrictions(requirement_value)
          context_dict['name'] = subset_name
          subset_context = [context_dict]

          for key, rule in requirement_value.items():

            match key:

              case 'block':
                # label number type value
                for block_dict in rule:
                  num_required = int(block_dict['block']['number'])
                  block_label = block_dict['block']['label']
                  required_block_type = block_dict['block']['block_type']
                  required_block_value = block_dict['block']['block_value']
                  with psycopg.connect('dbname=cuny_curriculum') as conn:
                    with conn.cursor(row_factory=namedtuple_row) as cursor:
                      cursor.execute("""
                      select institution, requirement_id, block_type, block_value,
                             title as block_title, parse_tree
                        from requirement_blocks
                       where institution = %s
                         and block_type = %s
                         and block_value = %s
                         and period_stop ~* '^9'
                      """, [institution, required_block_type, required_block_value])
                      if cursor.rowcount != num_required:
                        suffix = '' if cursor.rowcount == 1 else 's'
                        if cursor.rowcount == 0:
                          print(f'{institution} {requirement_id} Subset block: need '
                                f'{num_required}, found none', file=fail_file)
                        else:
                          print(f'{institution} {requirement_id} Subset block: need '
                                f'{num_required}, found {cursor.rowcount} active block{suffix}',
                                file=todo_file)
                      else:
                        local_context = [{'name': block_label}]
                        for row in cursor:
                          process_block(row, context_list + subset_context + local_context)
                          print(f'{institution} {requirement_id} Subset block', file=log_file)
                return

              case 'blocktype':
                print(f'{institution} {requirement_id} Subset blocktype', file=todo_file)
                return

              case 'class_credit_list' | 'conditional' | 'course_lists' | 'group_requirements':
                # These are lists of class_credit, conditional, course_list, group_requirement
                print(f'{institution} {requirement_id} Subset {key}', file=log_file)
                assert isinstance(rule, list)

                for rule_dict in rule:
                  # There is only one item per rule_dict, but this is a convenient way to get it
                  for k, v in rule_dict.items():
                    local_dict = get_restrictions(v)
                    try:
                      local_dict['name'] = v.pop('label')
                    except KeyError:
                      pass
                    local_context = [local_dict]
                    # if institution == 'LEH01' and requirement_id == 'RA001503':
                    #   print(f'\n{rule_dict=}\n{context_list=}\n{subset_context=}\n{local_context=}')
                    traverse_body(rule_dict, context_list + subset_context + local_context)
                return

              case 'copy_rules':
                try:

                  target_requirement_id = rule['requirement_id']
                except KeyError as ke:
                  print(f'Missing key {ke} in Subset copy_rules')
                else:
                  target_block = f'{institution} {target_requirement_id}'
                  if target_block in requirement_context:
                    print(target_block, 'Subset copy_rules: Circular target', file=fail_file)
                  else:
                    with psycopg.connect('dbname=cuny_curriculum') as conn:
                      with conn.cursor(row_factory=namedtuple_row) as cursor:
                        cursor.execute("""
                        select institution,
                               requirement_id,
                               block_type,
                               block_value,
                               title as block_title,
                               period_start,
                               period_stop,
                               parse_tree
                          from requirement_blocks
                         where institution = %s
                           and requirement_id = %s
                           and period_stop ~* '^9'
                        """, [institution, target_requirement_id])
                        if cursor.rowcount != 1:
                          print(f'{institution} {requirement_id} Subset copy_rules found '
                                f'{cursor.rowcount} active blocks',
                                file=fail_file)
                        else:
                          row = cursor.fetchone()
                          parse_tree = row.parse_tree
                          if parse_tree == '{}':
                            print(f'Parsing {row.institution} {row.requirement_id}')
                            parse_tree = parse_block(row.institution, row.requirement_id,
                                                     row.period_start, row.period_stop)
                          try:
                            body_list = parse_tree['body_list']
                          except KeyError as ke:
                            if 'error' in parse_tree.keys():
                              problem = 'compile error'
                            else:
                              problem = 'no body_list'
                            print(f'{institution} {requirement_id} Subset copy_rules target: '
                                  f'{problem}', file=fail_file)
                            print(f'{institution} {requirement_id} Subset copy_rules target, '
                                  f'{row.requirement_id}, compile error: {parse_tree["error"]} ',
                                  file=debug_file)
                          else:
                            local_dict = {'requirement_block': target_block,
                                          'name': row.block_title}
                            local_context = [local_dict]
                            traverse_body(body_list,
                                          context_list + requirement_context + local_context)
                            print(f'{institution} {requirement_id} Subset copy_rules',
                                  file=log_file)

                return

              case 'maxpassfail' | 'maxperdisc' | 'mingpa' | 'minspread' | 'noncourse' | 'share':
                # Ignored Qualifiers and rules
                return

              case _:
                print(f'{institution} {requirement_id} Unhandled Subset key: {key:20} '
                      f'{str(type(rule)):10} {len(rule)}', file=sys.stderr)
                return

            print(institution, requirement_id, f'Unexpected Subset: {key}', file=sys.stderr)

        case 'noncourse' | 'proxy_advice' | 'remark':
          # Ignore These
          return

        case _:
          print(f'Unhandled Requirement Type: {requirement_type}', file=sys.stderr)
          return

  else:
    # Not a dict or list
    print(f'Unhandled node of type {type(node)} ({node})', file=sys.stderr)
    return


# main()
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  """ Get a parse tree from the requirements_table and walk it.
  """
  parser = ArgumentParser()
  parser.add_argument('-a', '--all', action='store_true')
  parser.add_argument('-i', '--institution', default='qns')
  parser.add_argument('-r', '--requirement_id')
  parser.add_argument('-t', '--type', default='major')
  parser.add_argument('-v', '--value', default='csci-bs')
  args = parser.parse_args()

  empty_tree = "'{}'"

  programs_writer.writerow(['Institution',
                            'Requirement ID',
                            'Type',
                            'Code',
                            'Title',
                            'Total Credits',
                            'Max Transfer',
                            'Min Residency',
                            'Min Grade',
                            'Min GPA'])

  requirements_writer.writerow(['Institution',
                                'Requirement ID',
                                'Requirement Key',
                                'Program Name',
                                'Context'])

  map_writer.writerow(['Requirement Key',
                       'Course ID',
                       'Career',
                       'Course',
                       'With'])

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute("""
      select institution, requirement_id, sum(total_students) as total_students
      from ra_counts where active_term >= 1172
       and total_students > 4
      group by institution, requirement_id
      order by institution, requirement_id
      """)
      active_blocks = {(row.institution, row.requirement_id): row.total_students for row in cursor}

      if args.all or args.institution.upper() == 'ALL':
        institution = '^.*$'
        institution_op = '~*'
      else:
        institution = args.institution.strip('01').upper() + '01'
        institution_op = '='

      if args.requirement_id:
        try:
          requirement_id = f'RA{int(args.requirement_id.lower().strip("ra")):06}'
        except ValueError:
          exit(f'{args.requirement_id} is not a valid requirement id')
        cursor.execute(f""" select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title as block_title,
                                  parse_tree
                             from requirement_blocks
                            where institution {institution_op} %s
                              and requirement_id = %s
                            order by institution
                       """, (institution, requirement_id))
      else:
        block_type = [args.type.upper()]
        if args.all or 'ALL' in block_type:
          block_type = ['MAJOR', 'MINOR', 'CONC']

        block_value = args.value.upper()
        if args.all or block_value == 'ALL':
          block_value = '^.*$'
          value_op = '~*'
        else:
          value_op = '='
        cursor.execute(f"""select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title as block_title,
                                  parse_tree
                             from requirement_blocks
                            where institution {institution_op} %s
                              and block_type =  Any(%s)
                              and block_value {value_op} %s
                              and period_stop ~* '^9'
                              and parse_tree::text != {empty_tree}
                            order by institution, block_type, block_value""",
                       (institution, block_type, block_value))

      suffix = '' if cursor.rowcount == 1 else 's'
      print(f'{cursor.rowcount:,} parse tree{suffix}')
      quarantine_count = 0
      inactive_count = 0
      for row in cursor:
        if quarantine_dict.is_quarantined((row.institution, row.requirement_id)):
          quarantine_count += 1
          continue
        try:
          enrollment = active_blocks[(row.institution, row.requirement_id)]
        except KeyError:
          inactive_count += 1
          continue

        # If this is the first time this instution has been encountered, create a dict mapping
        # this institution's courses to their course_id:offer_nbr values
        if row.institution not in courses_by_institution:
          with conn.cursor(row_factory=namedtuple_row) as course_cursor:
            course_cursor.execute("""
            select institution, course_id, offer_nbr,discipline, catalog_number, career
              from cuny_courses
             where institution = %s
               and designation not in ('MNL', 'MLA')
               and course_status = 'A'
               and attributes !~* 'BKCR'
             order by discipline, numeric_part(catalog_number)
            """, (row.institution, ))
            for course in course_cursor:
              institution, discipline, catalog_number = (course.institution,
                                                         course.discipline,
                                                         course.catalog_number)
              value = (course.course_id, course.offer_nbr, course.career)
              courses_by_institution[institution][discipline][catalog_number] = value

            # And cache the institution's subplan info
            course_cursor.execute("""
            select institution, plan, subplan, subplan_type, description, cip_code, hegis_code
            from cuny_subplans
            """)
            for subplan in course_cursor:
              subplan_info = SubplanInfo._make([subplan.subplan_type, subplan.description,
                                                subplan.cip_code, subplan.hegis_code])
              subplans_by_institution[row.institution][subplan.plan][subplan.subplan] = subplan_info

        process_block(row)
  print(f'{quarantine_count:5,} Quarantined\n{inactive_count:5,} Inactive')
