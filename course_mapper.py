#! /usr/local/bin/python3
""" List program requirements and courses that satisfy them.
"""

import csv
import os
import json
import psycopg
import sys

from argparse import ArgumentParser
from blockinfo import BlockInfo
from catalogyears import catalog_years
from collections import namedtuple, defaultdict
from pprint import pprint
from psycopg.rows import namedtuple_row
from recordclass import recordclass
from typing import Any

from coursescache import courses_cache
from dgw_parser import parse_block

from quarantine_manager import QuarantineManager

quarantine_dict = QuarantineManager()

# BlockInfo = recordclass('BlockInfo',
#                         'institution requirement_id block_type block_value block_title '
#                         'class_credits max_transfer min_residency min_grade min_gpa '
#                         'max_classes max_credits')


SubplanInfo = namedtuple('SubplanInfo', 'type description cip_code hegis_code')


""" Logging/Development Reports
      analysis_file:      Analsis of as-yet-unhandled constructs.
      blocks_file:        List of blocks processed
      debug_file:         Info written during debugging (to avoid stdout/stderr)
      fail_file:          Blocks that failed for one reason or another
      log_file:           Record of requirements processed successfully. Bigger is better!
      no_courses_file:    Requirements with no course lists.
      todo_file:          Record of all known requirements not yet handled. Smaller is better!

    Data for T-Rex
      programs_file:      Spreadsheet of info about majors, minors, and concentrations
      requirements_file:  Spreadsheet of program requirement names
      mapping_file        Spreadsheet of course-to-requirements mappings

"""
analysis_file = open('analysis.txt', 'w')
blocks_file = open('blocks.txt', 'w')
debug_file = open('debug.txt', 'w')
fail_file = open('fail.txt', 'w')
log_file = open('log.txt', 'w')
no_courses_file = open('no_courses.txt', 'w')
todo_file = open(f'todo.txt', 'w')

programs_file = open(f'{__file__.replace(".py", ".programs.csv")}', 'w', newline='')
requirements_file = open(f'{__file__.replace(".py", ".requirements.csv")}', 'w', newline='')
mapping_file = open(f'{__file__.replace(".py", ".course_mappings.csv")}', 'w', newline='')

programs_writer = csv.writer(programs_file)
requirements_writer = csv.writer(requirements_file)
map_writer = csv.writer(mapping_file)


# def dict_factory():
#   """ Support for three index levels, as in courses_by_institution and subplans_by_institution.
#   """
#   return defaultdict(dict)


# courses_by_institution = defaultdict(dict_factory)
# subplans_by_institution = defaultdict(dict_factory)

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


# expand_course_list()
# -------------------------------------------------------------------------------------------------
def expand_course_list(institution: str, requirement_id: str, course_dict: dict) -> dict:
  """ Generate a dict of active courses that match a scribed list with except courses removed (and
      include courses ignored), taking wildcards and ranges into account. Dict keys are (course_id,
      offer_nbr) tuples; values are with-clause expressions (which may be null).

      With-expressions can appear within the scribed list and/or the except list.
        scribed PHYS @
        except  @ 1@ with dwgrade < 2.0 or dwtransfer = y
      Unable to evaluate except list where there are wildcards and the with-expression is not empty,
      so log those cases. But if there is no with-expression, even with wildcards, the matching
      courses get deleted from the return dict.

  """
  # Check for empty list
  if not course_dict:
    return None

  # Get the scribed list and flatten it
  course_list = course_dict['scribed_courses']
  courses = [course for area in course_list for course in area]

  # Create set of (course_id, offer_nbr) tuples for exclude courses that have no with-expressions
  exclude_list = course_dict['except_courses']
  exclude_set = set()
  for item in exclude_list:
    if with_expression := item[2]:
      # Log and skip cases with with-expressions
      print(f'{institution} {requirement_id} exclude with {with_expression}', file=debug_file)
    else:
      for k, v in courses_cache((institution, item[0].strip(), item[1].strip())).items():
        print(f'{institution} {requirement_id} exclude {k} from {courses}', file=debug_file)
        exclude_set.add(k)

  # Get rid of redundant scribes
  courses_set = set([tuple(course) for course in courses])

  # Dict of active scribed courses
  return_dict = {}
  for discipline, catalog_nbr, with_clause in courses_set:
    for k, v in courses_cache((institution, discipline, catalog_nbr)).items():
      if k not in exclude_set:
        return_dict[(v.course_id, v.offer_nbr)] = (k, with_clause)

  return return_dict


# map_courses()
# -------------------------------------------------------------------------------------------------
def map_courses(institution: str, requirement_id: str, requirement_name: str, context_list: list,
                requirement_dict: dict):
  """ Write courses and their With clauses to the map file.
      Object returned by courses_cache():
        CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr title credits career')

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
    try:
      # Ignore context_path, if it is present. (It makes the course list harder to read)
      del course_list['context_path']
    except KeyError:
      pass
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
    # The requirement_id has to come from the first block_info in the context
    # list (is this ever actually used?).
    requirement_id = context_list[0]['block_info']['requirement_id']
    data_row = [institution, requirement_id, requirement_index, requirement_name,
                json.dumps(context_list + [{'requirement': requirement_dict}], ensure_ascii=False)]
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
def process_block(row: namedtuple, context_list: list = [], top_level: bool = False):
  """ Given (parts of) a row from the requirement_blocks db table, traverse the header and body
      lists.
  """

  # Be sure the block is available
  if quarantine_dict.is_quarantined((row.institution, row.requirement_id)):
    print(row.institution, row.requirement_id, 'Quarantined block', file=fail_file)
    return

  # Be sure the block is for an active program
  try:
    enrollment = active_blocks[(row.institution, row.requirement_id)]
  except KeyError:
    print(row.institution, row.requirement_id, 'Not an active program', file=fail_file)
    return

  # Be sure the block was parsed successfully (Quarantined should have handled this.)
  if 'error' in row.parse_tree.keys():
    print(row.institution, row.requirement_id, 'Parser Error', file=fail_file)
    return

  # Characterize blocks as top-level or nested for reporting purposes; use capitalization to sort
  # top-level before nested.
  toplevel_str = 'Top-level' if top_level else 'nested'
  print(f'{row.institution} {row.requirement_id} {toplevel_str}', file=blocks_file)

  # A BlockInfo object contains block metadata from the requirement_blocks table, and will be
  # augmented with additional information found in the block’s header

  # The single catalog_years string is built from period_start and period_end values
  args_dict = {}
  # Other metadata for the block, except catalog_years and parse_tree.
  for key, value in row._asdict().items():
    if key in ['period_start', 'period_stop', 'parse_tree']:
      continue
    args_dict[key] = value
  # Catalog years string is based on period_start and period_stop
  args_dict['catalog_years'] = catalog_years(row.period_start, row.period_stop)._asdict()
  # Empty strings for default values that might or might not be found in the header.
  for key in ['class_credits', 'min_residency', 'min_grade', 'min_gpa']:
    args_dict[key] = ''
  # Empty lists as default limits that might or might not be specified in the header.
  for key in ['max_transfer', 'max_classes', 'max_credits']:
    args_dict[key] = []
  block_info = BlockInfo(**args_dict)

  # traverse_header() is a one-pass procedure that updates the block_info record with parameters
  # found in the header list.
  try:
    header_list = row.parse_tree['header_list']
    if len(header_list) > 0:
      try:
        traverse_header(block_info, header_list)
      except KeyError as ke:
        exit(f'{row.institution} {row.requirement_id} Header KeyError {ke}')
    else:
      print(row.institution, row.requirement_id, 'Empty Header', file=log_file)
  except KeyError:
    print(row.institution, row.requirement_id, 'Missing Header', file=fail_file)

  # Only top-level blocks get entries in the programs table.
  if top_level:
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

  # But but all blocks get added to the context list.
  context_list.append({'block_info': block_info._asdict()})

  # traverse_body() is a recursive procedure that handles nested requirements, so to start, it has
  # to be primed with the root node of the body tree: the body_list. process_block() itself may be
  # invoked from within traverse_body() to handle block, blocktype and copy_rules constructs.
  try:
    body_list = row.parse_tree['body_list']
  except KeyError as ke:
    print(row.institution, row.requirement_id, 'Missing Body', file=fail_file)
    return
  if len(body_list) == 0:
    print(row.institution, row.requirement_id, 'Empty Body', file=log_file)
  else:
    item_context = context_list + [{'block_info': block_info._asdict()}]
    for body_item in body_list:
      # traverse_body(body_item, item_context)
      traverse_body(body_item, context_list)


# traverse_header()
# =================================================================================================
def traverse_header(block_info: namedtuple, header_list: list) -> None:
  """ Extract program-wide qualifiers: MinGrade (but not MinGPA) and residency requirements,
  """

  institution, requirement_id, block_type, *_ = (block_info.institution,
                                                 block_info.requirement_id,
                                                 block_info.block_type)
  for header_item in header_list:

    if not isinstance(header_item, dict):
      print(header_item, 'is not a dict', file=sys.stderr)

    else:
      for key, value in header_item.items():
        match key:

          case 'header_class_credit':
            if label_str := value['label']:
              print(f'{institution} {requirement_id}: Header class_credit label: {label_str}',
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
            print(f'{institution} {requirement_id} Header conditional', file=todo_file)

            conditional_dict = header_item['conditional']
            condition_str = conditional_dict['condition_str']
            # print(f'{institution} {requirement_id} Header conditional: {condition_str}')
            if_true_list = conditional_dict['if_true']
            try:
              if_false_list = conditional_dict['if_false']
            except KeyError:
              if_false_list = []
            """ There are two cases to consider:
                  (1) updates/additions to block-wide residency and grade restrictions, which
                  update/augment the programs table
                  (2) course requirements, which presumably should be added to the requirements and
                  mapping tables.
            """
            # map_courses(institution,
            #             requirement_id,
            #             requirement_name,
            #             context_list,
            #             requirement_dict)

          case 'copy_rules':
            print(f'{institution} {requirement_id}: Header copy_rules', file=todo_file)
            pass

          case 'header_lastres':
            pass

          case 'header_maxclass':
            print(f'{institution} {requirement_id} Header maxclass', file=log_file)
            for cruft_key in ['institution', 'requirement_id']:
              del(value['maxclass']['course_list'][cruft_key])

            number = int(value['maxclass']['number'])
            course_list = value['maxclass']['course_list']
            course_list['courses'] = [{'course_id': f'{k[0]:06}:{k[1]}',
                                       'course': v[0],
                                       'with': v[1]}
                                      for k, v in expand_course_list(institution,
                                                                     requirement_id,
                                                                     course_list).items()]
            limit_dict = {'number': number,
                          'courses': course_list
                          }
            block_info.max_classes.append(limit_dict)

          case 'header_maxcredit':
            print(f'{institution} {requirement_id} Header maxcredit', file=log_file)
            for cruft_key in ['institution', 'requirement_id']:
              del(value['maxcredit']['course_list'][cruft_key])

            number = float(value['maxcredit']['number'])
            course_list = value['maxcredit']['course_list']
            course_list['courses'] = [{'course_id': f'{k[0]:06}:{k[1]}',
                                       'course': v[0],
                                       'with': v[1]}
                                      for k, v in expand_course_list(institution,
                                                                     requirement_id,
                                                                     course_list).items()]
            limit_dict = {'number': number,
                          'courses': course_list
                          }
            block_info.max_credits.append(limit_dict)

          case 'header_maxpassfail':
            pass

          case 'header_maxperdisc':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Header maxperdisc', file=todo_file)
            pass

          case 'header_maxtransfer':
            print(f'{institution} {requirement_id} Header maxtransfer', file=log_file)
            if label_str := value['label']:
              print(f'{institution} {requirement_id} Header maxtransfer label', file=todo_file)

            transfer_limit = {}
            number = float(value['maxtransfer']['number'])
            class_or_credit = value['maxtransfer']['class_or_credit']
            if class_or_credit == 'credit':
              transfer_limit['limit'] = f'{number:3.1f} credits'
            else:
              suffix = '' if int(number) == 1 else 'es'
              transfer_limit['limit'] = f'{int(number):3} class{suffix}'
            try:
              transfer_limit['transfer_types'] = value['transfer_types']
            except KeyError:
              pass
            block_info.max_transfer.append(transfer_limit)

          case 'header_minclass':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Header minclass', file=todo_file)
            pass

          case 'header_mincredit':
            # THERE WOULD BE A COURSE LIST HERE
            print(f'{institution} {requirement_id} Header mincredit', file=todo_file)
            pass

          case 'header_mingpa':
            print(f'{institution} {requirement_id} Header mingpa', file=log_file)
            if label_str := value['label']:
              print(f'{institution} {requirement_id} Header mingpa label', file=todo_file)
            mingpa = float(value['mingpa']['number'])
            block_info.min_gpa = f'{mingpa:4.2f}'

          case 'header_mingrade':
            print(f'{institution} {requirement_id} Header mingrade', file=log_file)
            if label_str := value['label']:
              print(f'{institution} {requirement_id} Header mingrade label', file=todo_file)
            block_info.min_grade = letter_grade(float(value['mingrade']['number']))

          case 'header_minperdisc':
            pass

          case 'header_minres':
            print(f'{institution} {requirement_id} Header minres', file=log_file)
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
               'remark' | 'rule_complete' | 'standalone' | 'header_share' | 'header_tag':
            # Intentionally ignored
            print(f'{institution} {requirement_id} Header {key} Ignored', file=log_file)
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
      adds this info to the BlockInfo object in the context_list.)

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

  global do_remarks, args

  # Find the containing block’s context.
  # Ir’s the last block_info item in the context_list
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

  elif isinstance(node, dict):
    # A dict should have one key that identifies the requirement type, and a sub-dict that gives the
    # details about that requirement, including the label that gives it its name.

    assert len(node) == 1
    requirement_type, requirement_value = list(node.items())[0]

    # String values are remarks: add to context, and continue. Can be suppressed from command line.
    if isinstance(requirement_value, str):
      assert requirement_type == 'remark'
      if do_remarks:
        print(f'{institution} {requirement_id} Body remark',
              file=log_file)
        context_list += [{requirement_type: requirement_value}]
      else:
        pass

    # Lists happen in requirement_values because of how the grammar handles requirements that can
    # occur in different orders. (“This or that, zero or more times.”)
    # Lists of the following object types have been observed here:
    #   402 group_requirement
    #   257 class_credit
    #    76 remark
    #    20 subset
    #    11 conditional
    #     5 group_requirements  Nested groups(?)
    elif isinstance(requirement_value, list):
      for list_item in requirement_value:
        traverse_body(list_item, context_list)

    elif isinstance(requirement_value, dict):
      context_dict = get_restrictions(requirement_value)
      try:
        context_dict['requirement_name'] = requirement_value['label']
      except KeyError:
        if context_dict:
          # If there are restrictions but no name, add a placeholder name, and log it
          print(f'{institution} {requirement_id} Requirement with restrictions but no label',
                file=debug_file)

      if context_dict:
        requirement_context = [context_dict]
      else:
        # If there are no restrictions and no name, there's nothing to add to the context.
        if requirement_type != 'conditional':
          # None expected for conditional, but make a note for any others
            print(f'{institution} {requirement_id} {requirement_type.title()} with no label and no '
                  'qualifiers', file=log_file)
        requirement_context = []

      if args.debug:
        print(f'{institution} {requirement_id} {requirement_type} from Body =>',
              get_context_names(context_list + requirement_context), file=sys.stderr)

      match requirement_type:

        case 'block':
          print(institution, requirement_id, 'Body block', file=log_file)

          # The number of blocks has to be 1
          number = int(requirement_value['number'])
          assert number == 1

          block_args = [requirement_value['institution'],
                        requirement_value['block_type'],
                        requirement_value['block_value']]
          with psycopg.connect('dbname=cuny_curriculum') as conn:
            with conn.cursor(row_factory=namedtuple_row) as cursor:
              blocks = cursor.execute("""
              select institution, requirement_id, block_type, block_value, title as block_title,
                     period_start, period_stop, parse_tree
                from requirement_blocks
               where institution = %s
                 and block_type = %s
                 and block_value = %s
                 and period_stop ~* '^9'
              """, block_args)

              if cursor.rowcount == 0:
                print(f'{institution} {requirement_id} Body block: no active block',
                      file=fail_file)
              else:
                num_blocks = cursor.rowcount
                block_num = 0
                for row in cursor:
                  block_num += 1
                  if num_blocks == 1:
                    process_block(row, context_list + requirement_context)
                  else:
                    choice_context = {'choice': {'num_choices': num_blocks,
                                                 'num_required': number,
                                                 'index': block_num,
                                                 'block_type': block_args[1]}}
                    process_block(row,
                                  context_list + requirement_context + [choice_context])

        case 'blocktype':
          number = int(requirement_value['number'])
          if number != 1:
            print(institution, requirement_id, f'blocktype with number ({number}) not equal 1',
                  file=todo_file)
          else:
            req_type = requirement_value['block_type']
            if '-' in block_value:
              target_value, degree = block_value.split('-')
              with psycopg.connect('dbname=cuny_curriculum') as conn:
                with conn.cursor(row_factory=namedtuple_row) as cursor:
                  blocks = cursor.execute(f"""
                  select institution, requirement_id, block_type, block_value, title as block_title,
                         period_start, period_stop, parse_tree
                    from requirement_blocks
                   where institution = '{institution}'
                     and block_type = '{req_type}'
                     and block_value ~* '^{target_value}'
                     and period_stop ~* '^9'
                  """)
                  if cursor.rowcount == 0:
                    print(f'{institution} {requirement_id} Body blocktype: no matching {req_type}',
                          file=fail_file)
                  else:
                    print(institution, requirement_id, 'Body blocktype', file=log_file)
                    # Catch observed circularities
                    requirement_ids = [requirement_id]
                    for row in cursor:
                      if row.requirement_id not in requirement_ids:
                        requirement_ids.append(row.requirement_id)
                        process_block(row, context_list + requirement_context)
                      else:
                        print(f'{institution} {requirement_id} Circular blocktype', file=fail_file)
                        break

            else:
              print(institution, requirement_id, block_value, 'Block value failed to split',
                    file=fail_file)

        case 'class_credit':
          print(institution, requirement_id, 'Body class_credit', file=log_file)
          # This is where course lists turn up, in general.
          try:
            if course_list := requirement_value['course_list']:
              map_courses(institution, requirement_id, block_title,
                          context_list + requirement_context, requirement_value)
          except KeyError:
            # Course List is an optional part of ClassCredit
            pass

        case 'conditional':
          print(institution, requirement_id, 'Body conditional', file=log_file)

          # Use the condition as the pseudo-name of this requirement
          # UNABLE TO HANDLE RULE_COMPLETE UNTIL THE CONDITION IS EVALUATED
          condition = requirement_value['condition_str']
          for if_true_dict in requirement_value['if_true']:
            condition_dict = {'requirement_name': 'if_true', 'condition': condition}
            condition_list = [condition_dict]
            traverse_body(if_true_dict, context_list + condition_list)
          try:
            for if_false_dict in requirement_value['if_false']:
              condition_dict = {'requirement_name': 'if_false', 'condition': condition}
              condition_list = [condition_dict]
              traverse_body(if_false_dict, context_list + condition_list)
          except KeyError:
            # Scribe Else clause is optional
            pass

        case 'copy_rules':
          print(institution, requirement_id, 'Body copy_rules', file=log_file)
          # Use the title of the block as the label.
          with psycopg.connect('dbname=cuny_curriculum') as conn:
            with conn.cursor(row_factory=namedtuple_row) as cursor:
              cursor.execute("""
              select institution, requirement_id, block_type, block_value, title as block_title,
                     period_start, period_stop, parse_tree
                from requirement_blocks
               where institution = %s
                 and requirement_id = %s
                 and period_stop ~* '^9'
              """, (requirement_value['institution'],
                    requirement_value['requirement_id']))
              if cursor.rowcount != 1:
                print(f'{institution} {requirement_id} Body copy_rules: {cursor.rowcount} active '
                      f'blocks', file=fail_file)
                return

              row = cursor.fetchone()

              is_circular = False
              for context_dict in context_list:
                try:
                  # Assume there are no cross-institutional course requirements
                  if row.requirement_id == context_dict['requirement_id']:
                    print(institution, requirement_id, 'Body circular copy_rules', file=fail_file)
                    is_circular = True
                except KeyError:
                  pass
              if not is_circular:

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
                  local_dict = {'requirement_block': row.requirement_id,
                                'requirement_name': row.block_title}
                  local_context = [local_dict]
                  traverse_body(body_list,
                                context_list + requirement_context + local_context)

        case 'course_list_rule':
          print(institution, requirement_id, 'Body course_list_rule', file=log_file)

          try:
            if course_list := requirement_value['course_list']:
              map_courses(institution, requirement_id, block_title,
                          context_list + requirement_context, requirement_value)
          except KeyError:
            # Can't have a Course List Rule w/o a course list
            print(f'{institution} {requirement_id}: Course List Rule w/o a Course List',
                  file=sys.stderr)

        case 'rule_complete':
          print(institution, requirement_id, 'Body rule_complete', file=todo_file)
          # is_complete may be T/F
          # rule_tag is followed by a name-value pair. If the name is RemarkJump, the value is a URL
          # for more info. Otherwise, the name-value pair is used to control formatting of the rule.
          # This happens only inside conditionals, where the idea will be to look at what whether
          # it's in the true or false leg, what the condition is, and whether this is True or False
          # to infer what requirement must or must not be met. We're looking at YOU, Lehman ACC-BA.

        case 'course_list':
          print(institution, requirement_id, 'Body course_list', file=todo_file)
          map_courses(institution, requirement_id, block_title, context_list + requirement_context,
                      requirement_value)

        case 'group_requirements':
          # Group requirements is a list , so it should not show up here.
          exit(f'{institution} {requirement_id} Error: unexpected group_requirements',
               file=sys.stderr)

        case 'group_requirement':
          print(institution, requirement_id, 'Body group_requirement', file=log_file)
          # ---------------------------------------------------------------------------------------
          """ Each group requirement has a group_list, label, and number (num_required)
              A group_list is a list of groups (!)
              Each group is one of: block, blocktype, class_credit, course_list,
                                    group_requirement(s), noncourse, or rule_complete)
          """
          groups = requirement_value['group_list']
          context_dict['num_groups'] = len(groups)
          context_dict['num_required'] = int(requirement_value['number'])
          for group_num, group in enumerate(groups):
            context_dict['group_number'] = group_num + 1

            assert len(group.keys()) == 1

            for key, value in group.items():
              match key:
                case 'block':
                  try:
                    block_name = value['label']
                    block_num_required = int(value['number'])
                    suffix = '' if block_num_required == 1 else 's'
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
                                    period_start, period_stop, parse_tree
                               from requirement_blocks
                              where institution = %s
                                and block_type =  %s
                                and block_value = %s
                                and period_stop ~* '^9'
                        """, [institution, block_type, block_value])
                        if cursor.rowcount != block_num_required:
                          # HOW TO HANDLE THIS (if it occurs)?
                          suffix = '' if cursor.rowcount == 1 else 's'
                          print(f'{institution} {requirement_id} Group block found '
                                f'{cursor.rowcount} row{suffix} ({block_num_required} needed)',
                                file=todo_file)
                        else:
                          for row in cursor:
                            process_block(row, context_list + requirement_context)
                          print(institution, requirement_id,
                                f'Group block {cursor.rowcount} of '
                                f'{block_num_required} required block{suffix}',
                                file=log_file)
                  except KeyError as ke:
                    exit(ke)
                  continue

                case 'blocktype':
                  print(institution, requirement_id, 'Group blocktype', file=todo_file)
                  continue

                case 'class_credit':
                  print(institution, requirement_id, 'Group class_credit', file=log_file)
                  # This is where course lists turn up, in general.
                  try:
                    map_courses(institution, requirement_id, block_title,
                                context_list + requirement_context, value)
                  except KeyError as ke:
                    # Course List is an optional part of ClassCredit
                    pass
                  continue

                case 'course_list_rule':
                  print(institution, requirement_id, 'Group course_list_rule', file=todo_file)
                  continue

                case 'group_requirements':
                  print(institution, requirement_id, 'Body nested group_requirements',
                        file=log_file)
                  assert isinstance(value, list)
                  for group_requirement in value:
                    traverse_body(value, context_list + requirement_context)
                  continue

                case 'noncourse':
                  continue

                case 'rule_complete':
                  continue

                case _:
                  exit(f'{institution} {requirement_id} Unexpected Group {key}')

        case 'subset':
          print(institution, requirement_id, 'Body subset', file=log_file)
          # ---------------------------------------------------------------------------------------
          # Process the valid rules in the subset

          # Track MaxTransfer and MinGrade restrictions (qualifiers).
          context_dict = get_restrictions(requirement_value)

          try:
            context_dict['requirement_name'] = requirement_value.pop('label')
            subset_context = [context_dict]
          except KeyError:
            pass
          if context_dict:
            subset_context = [context_dict]
          else:
            subset_context = []

          for key, rule in requirement_value.items():

            match key:

              case 'block':
                # label number type value
                for block_dict in rule:
                  num_required = int(block_dict['block']['number'])
                  suffix = '' if num_required == 1 else 's'
                  block_label = block_dict['block']['label']
                  required_block_type = block_dict['block']['block_type']
                  required_block_value = block_dict['block']['block_value']
                  with psycopg.connect('dbname=cuny_curriculum') as conn:
                    with conn.cursor(row_factory=namedtuple_row) as cursor:
                      cursor.execute("""
                      select institution, requirement_id, block_type, block_value,
                             title as block_title, period_start, period_stop, parse_tree
                        from requirement_blocks
                       where institution = %s
                         and block_type = %s
                         and block_value = %s
                         and period_stop ~* '^9'
                      """, [institution, required_block_type, required_block_value])
                      if cursor.rowcount < num_required:
                        suffix = '' if cursor.rowcount == 1 else 's'
                        print(f'{institution} {requirement_id} Subset block: {cursor.rowcount} '
                              f'active block{suffix}; {num_required} required ',
                              file=fail_file)
                      else:
                        local_context = [{'requirement_name': block_label}]
                        num_found = 0
                        num_extra = 0
                        for row in cursor:
                          # Heuristic: if there are more rows than needed, select just the ones
                          # where the major1 field matches the referencing block value. Any left
                          # over are a problem. But this problem remains: the heuristic is not
                          # sufficient. Given the type, the valid blocks will have to be determined
                          # from CUNYfirst info about plans and their subplans.
                          if cursor.rowcount == num_required:  # or (cursor.rowcount > num_required
                                                               # and row.major1 == block_value):
                            num_found += 1
                            if num_found <= num_required:
                              process_block(row, context_list + subset_context + local_context)
                            else:
                              num_extra += 1
                        if num_extra:
                          print(institution, requirement_id, f'Subset block needed {num_required}; '
                                                             f'found {num_extra} extra',
                                                             file=todo_file)
                        elif num_found == num_required:
                          print(institution, requirement_id, f'Subset block {num_found} of '
                                f'{num_required} required block{suffix}', file=log_file)
                        else:
                          print(institution, requirement_id, f'Subset block {num_required=} '
                                                             f'{cursor.rowcount=} {num_found=} '
                                                             f'{num_extra=}', file=debug_file)
                continue

              case 'blocktype':
                print(f'{institution} {requirement_id} Subset blocktype', file=todo_file)

              case 'conditional':
                print(f'{institution} {requirement_id} Subset conditional', file=log_file)
                assert isinstance(rule, list)
                for conditional_dict in rule:
                  conditional = conditional_dict['conditional']
                  # Use the condition as the pseudo-name of this requirement
                  condition = conditional['condition_str']
                  for if_true_dict in conditional['if_true']:
                    condition_list = [{'requirement_name': 'if_true', 'condition': condition}]
                    traverse_body(if_true_dict, context_list + subset_context + condition_list)
                  try:
                    for if_false_dict in conditional['if_false']:
                      condition_list = [{'requirement_name': 'if_true', 'condition': condition}]
                      traverse_body(if_true_dict, context_list + subset_context + condition_list)
                  except KeyError:
                    # Scribe Else clause is optional
                    pass

              case 'copy_rules':
                print(institution, requirement_id, 'Subset copy_rules', file=log_file)
                try:
                  target_requirement_id = rule['requirement_id']
                except KeyError as ke:
                  exit(f'Missing key {ke} in Subset copy_rules')
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
                        print(f'{institution} {requirement_id} Subset copy_rules: '
                              f'{cursor.rowcount} active blocks',
                              file=fail_file)
                      else:
                        row = cursor.fetchone()
                        is_circular = False
                        for context_dict in context_list:
                          try:
                            # Assume there are no cross-institutional course requirements
                            if row.requirement_id == context_dict['requirement_id']:
                              print(institution, requirement_id, 'Subset circular CopyRules',
                                    file=fail_file)
                              is_circular = True
                          except KeyError:
                            pass
                        if not is_circular:
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
                                          'requirement_name': row.block_title}
                            local_context = [local_dict]
                            traverse_body(body_list,
                                          context_list + requirement_context + local_context)

              case 'course_lists':
                print(f'{institution} {requirement_id} Subset {key}', file=todo_file)

              case 'class_credit_list':
                print(f'{institution} {requirement_id} Subset {key}', file=log_file)
                assert isinstance(rule, list)
                for rule_dict in rule:
                  # There is only one item per rule_dict, but this is a convenient way to get it
                  assert len(rule_dict) == 1
                  for k, v in rule_dict.items():
                    local_dict = get_restrictions(v)
                    try:
                      local_dict['requirement_name'] = v['label']
                    except KeyError as ke:
                      print(f'{institution} {requirement_id} '
                            f'Subset class_credit_list {k} with no label', file=todo_file)

                    if local_dict:
                      local_context = [local_dict]
                    else:
                      local_context = []
                    try:
                      map_courses(institution, requirement_id, block_title,
                                  context_list + subset_context + local_context,
                                  rule_dict['class_credit'])
                    except KeyError as ke:
                      print(institution, requirement_id, block_title,
                            f'{ke} in subset class_credit_list', file=sys.stderr)
                      pprint(rule_dict, stream=sys.stderr)
                      exit()

              case 'group_requirements':
                # This is a list of group_requirement dicts
                print(f'{institution} {requirement_id} Subset {key}', file=log_file)
                assert isinstance(rule, list)
                for group_requirement in rule:
                  traverse_body(group_requirement, context_list + subset_context)

              case 'maxpassfail' | 'maxperdisc' | 'mingpa' | 'minspread' | 'noncourse' | 'share':
                # Ignored Qualifiers and rules
                pass

              case 'proxy_advice':
                # Ignored for now
                pass

              case _:
                print(f'{institution} {requirement_id} Unhandled Subset key: {key:20} '
                      f'{str(type(rule)):10} {len(rule)}', file=sys.stderr)

        case 'remark':
          if do_remarks:
            print(institution, requirement_id, 'Unhandled remark', file=todo_file)

        case 'noncourse' | 'proxy_advice':
          # Ignore These
          pass

        case _:
          exit(f'{institution} {requirement_id} Unhandled Requirement Type: {requirement_type}'
               f' {requirement_value}')
    else:
      exit(f'{institution} {requirement_id} Unhandled Requirement Type {type(requirement_value)} '
           f'({requirement_value})')
  else:
    # Not a list, str, or dict (??)
    exit(f'{institution} {requirement_id} Unhandled node type {type(node)} ({node})')


# main()
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  """ Get a parse tree from the requirements_table and walk it.
  """
  parser = ArgumentParser()
  parser.add_argument('-a', '--all', action='store_true')
  parser.add_argument('-d', '--debug', action='store_true')
  parser.add_argument('--do_degrees', action='store_true')
  parser.add_argument('--do_hunter', action='store_true')
  parser.add_argument('--no_remarks', action='store_true')
  parser.add_argument('-i', '--institution', default='qns')
  parser.add_argument('-r', '--requirement_id')
  parser.add_argument('-t', '--types', default=['major'])
  parser.add_argument('-v', '--value', default='csci-bs')
  args = parser.parse_args()
  do_degrees = args.do_degrees
  do_hunter = args.do_hunter
  do_remarks = not args.no_remarks

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
                            'Min GPA', 'Other'])

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
        block_types = [block_type.upper() for block_type in args.types]
        if args.all or 'ALL' in block_types:
          block_types = ['MAJOR', 'MINOR', 'CONC']
          if do_degrees:
            block_types.append('DEGREE')

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
                                  period_start,
                                  period_stop,
                                  parse_tree
                             from requirement_blocks
                            where institution {institution_op} %s
                              and block_type =  Any(%s)
                              and block_value {value_op} %s
                              and period_stop ~* '^9'
                              and parse_tree::text != {empty_tree}
                            order by institution, block_type, block_value""",
                       (institution, block_types, block_value))

      suffix = '' if cursor.rowcount == 1 else 's'
      print(f'{cursor.rowcount:,} parse tree{suffix}')

      hunter_count = 0
      mhc_count = 0
      quarantine_count = 0
      inactive_count = 0
      block_types = defaultdict(int)
      for row in cursor:
        if row.institution == 'HTR01':
          hunter_count += 1
          if not do_hunter:
            continue
        if quarantine_dict.is_quarantined((row.institution, row.requirement_id)):
          quarantine_count += 1
          continue
        if row.block_value.upper().startswith('MHC'):
          mhc_count += 1
          continue
        try:
          enrollment = active_blocks[(row.institution, row.requirement_id)]
        except KeyError:
          inactive_count += 1
          continue

        process_block(row, context_list=[], top_level=True)
        block_types[row.block_type] += 1

  for k, v in block_types.items():
    print(f'{v:5,} {k.title()}')
  print(f'{hunter_count:5,} Hunter\n'
        f'{mhc_count:5,} Macaulay\n'
        f'{quarantine_count:5,} Quarantined\n'
        f'{inactive_count:5,} Inactive')
