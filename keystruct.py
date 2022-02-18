#! /usr/local/bin/python3
""" List program requirements and courses that satisfy them.
"""

import csv
import os
import psycopg
import sys

from typing import Any
from argparse import ArgumentParser
from collections import namedtuple, defaultdict
from recordclass import recordclass
from psycopg.rows import namedtuple_row

from coursescache import courses_cache

from quarantine_manager import QuarantineManager

quarantine_dict = QuarantineManager()

BlockInfo = recordclass('BlockInfo', 'institution requirement_id block_type block_value title '
                        'parse_tree class_credits max_transfer min_residency min_grade min_gpa')

""" Output Files
      debug_file:         Info written during debugging (to avoid stdout/stderr)
      log_file:           Record of requirements processed successfully. Bigger is better!
      todo_file:          Record of known requirements not yet handled. Smaller is better!
      programs_file:      Spreadsheet of info about majors, minors, and concentrations
      requirements_file:  Spreadsheet of program requirement names
      mapping_file        Spreadsheet of course-to-requirements mappings

"""
debug_file = open(f'{__file__.replace(".py", ".debug.txt")}', 'w')
log_file = open(f'{__file__.replace(".py", ".log")}', 'w')
todo_file = open(f'{__file__.replace(".py", ".todo.txt")}', 'w')
programs_file = open(f'{__file__.replace(".py", ".programs.csv")}', 'w')
requirements_file = open(f'{__file__.replace(".py", ".requirements.csv")}', 'w')
mapping_file = open(f'{__file__.replace(".py", ".course_mappings.csv")}', 'w')

programs_writer = csv.writer(programs_file)
requirements_writer = csv.writer(requirements_file)
map_writer = csv.writer(mapping_file)


def dict_factory():
  """ Support for three index levels, as in courses_by_institution.
  """
  return defaultdict(dict)


courses_by_institution = defaultdict(dict_factory)
requirement_keys = []


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


# write_log()
# -------------------------------------------------------------------------------------------------
def write_log(block_info: namedtuple, message: str):
  """ Log a message about a requirement block.
  """
  print(f'{block_info.institution} {block_info.requirement_id} {block_info.block_type:6} '
        f'{block_info.block_value:10}', message, file=log_file)


# map_courses()
# -------------------------------------------------------------------------------------------------
def map_courses(institution: str, requirement_id: str, requirement_name: str, context_list: list,
                course_list: dict):
  """ Write courses and their With clauses to the map file.
      Object returned by courses_cache():
        CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr title credits career')

      Each program requirement has a unique key based on institution, requirement_id, title, and
      context list.

Programs: Handled by process_block()
Institution, Requirement ID, Type, Code, Total, Max Transfer, Min Residency, Min Grade, Min GPA

Requirements: Handled here
Institution, Requirement ID, Requirement Key, Name, Context, Grade Restriction, Transfer Restriction

Course Mappings: Handled here
Requirement Key, Course ID, Career, Course, With

  """
  # Make the requirement_key a “nice hexadecimal string” (a lot of this is dealing with negative
  # hash values)
  h = int(hash((institution, requirement_id, requirement_name) + tuple(context_list)))
  mask = int(int((h.bit_length() + 3) / 4) * 'F', 16)  # enough hex digits to include leading bits
  requirement_key = f'{(h & mask):0X}'
  if requirement_key not in requirement_keys:
    requirement_keys.append(requirement_key)
    requirements_writer.writerow([institution, requirement_id, requirement_key, requirement_name,
                                  '\n'.join(context_list[2:])])

  for course_area in range(len(course_list['scribed_courses'])):
    for course_tuple in course_list['scribed_courses'][course_area]:
      # Unless there is a With clause, skip "any course" wildcards (@ @)
      if ['@', '@', None] == course_tuple:
        continue
      discipline, catalog_number, with_clause = course_tuple
      if with_clause is not None:
        with_clause = f'With ({with_clause})'
      for key, value in courses_cache((institution, discipline, catalog_number)).items():
        map_writer.writerow([requirement_key,
                             f'{value.course_id:06}:{value.offer_nbr}', value.career,
                             f'{key}: {value.title}', with_clause])


# get_restrictions()
# -------------------------------------------------------------------------------------------------
def get_restrictions(node: dict) -> str:
  """ Return qualifiers that might affect transferability.
  """

  assert isinstance(node, dict)

  # The maxtransfer restriction puts a limit on the number of classes or credits that can be
  # transferred, possibly with a list of disciplines for which the limit applies.
  try:
    max_xfer_str = 'Max xfer '
    transfer_dict = node.pop('maxtransfer')
    number = float(transfer_dict['number'])
    match transfer_dict['class_or_credit']:
      case 'class':
        suffix = 'es' if number != 1 else ''
        max_xfer_str += f'{int(number)} class{suffix}'
      case 'credit':
        suffix = 's' if number != 1.0 else ''
        max_xfer_str += f'{number:0.1f} credit{suffix}'
    try:
      max_xfer_types = ', '.join(transfer_dict['transfer_types'])
      max_xfer_str += f' of type {max_xfer_types}'
    except KeyError:
      pass
  except KeyError:
    max_xfer_restriction = 'Xfer OK'

  # The mingrade restriction puts a limit on the minimum required grade for all courses in a course
  # list. It’s a float (like a GPA) in Scribe, but is returned as a letter grade here.
  try:
    mingpa_dict = node.pop('mingrade')
    number = float(mingpa_dict['number'])
    min_grade_str = f'At least {letter_grade(number)}'
  except KeyError:
    min_grade_str = 'Any grade'

  return f'[{min_grade_str}; {max_xfer_str}]'


# process_block()
# -------------------------------------------------------------------------------------------------
def process_block(row: namedtuple, context_list: list = []):
  """ Given (parts of) a row from the requirement_blocks db table, traverse the header and body
      lists.
  """
  # Augment db info with default values for class_credits max_transfer min_residency min_grade
  # min_gpa
  (institution, requirement_id, block_type, block_value, title, parse_tree) = row
  block_info = BlockInfo._make(row + ('', '', '', '', ''))

  # traverse_header() is a one-pass procedure that extracts the header_list from the parse_tree that
  # it gets from the block_info passed to it.
  try:
    traverse_header(block_info)

    programs_writer.writerow([f'{block_info.institution[0:3]}',
                              f'{block_info.requirement_id}',
                              f'{block_info.block_type}',
                              f'{block_info.block_value}',
                              f'{block_info.class_credits}',
                              f'{block_info.max_transfer}',
                              f'{block_info.min_residency}',
                              f'{block_info.min_grade}',
                              f'{block_info.min_gpa}'])
  except KeyError:
    print(f'No header_list for', institution, requirement_id, block_type, block_value,
          title, file=sys.stderr)

  # traverse_body() is a recursive procedure that handles nested requirements, so to start, it has
  # to be primed with the root node of the body tree: the body_list. process_block() itself may be
  # invoked from within traverse_body() to handle block and copy_rules constructs.
  try:
    body_list = block_info.parse_tree['body_list']

    # Use context_list[0] for debugging; context_list[1] is the name of the block
    local_context_list = [f'{institution} {requirement_id}',
                          f'{title}']
    traverse_body(body_list, context_list + local_context_list)

  except KeyError as ke:
    print('No body_list for', institution, requirement_id, block_type, block_value, title,
          file=sys.stderr)


# traverse_header()
# -------------------------------------------------------------------------------------------------
def traverse_header(block_info: namedtuple) -> None:
  """ Extract program-wide qualifiers: MinGrade (but not MinGPA) and residency requirements,
  """

  institution, requirement_id, *_ = (block_info)
  try:
    header_list = block_info.parse_tree['header_list']
  except KeyError:
    print(f'{institution} {requirement_id}: No header list in parse tree', file=sys.stderr)
    return

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
              write_log(block_info, f'MaxTransfer label: {label_str}')
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
              write_log(block_info, f'MinGPA label: {label_str}')
            mingpa = float(value['mingpa']['number'])
            block_info.min_gpa = f'{mingpa:4.2f}'

          case 'header_mingrade':
            if label_str := value['label']:
              write_log(block_info, f'MinGrade label: {label_str}')
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
# -------------------------------------------------------------------------------------------------
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
  # Debugging Info
  institution, requirement_id = context_list[0].split()
  title = context_list[1]

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
      if requirement_type not in ['conditional', 'copy_rules']:
        try:
          requirement_name = node[requirement_type].pop('label')
        except KeyError:
          requirement_name = ''

      match requirement_type:

        case 'block':
          print(institution, requirement_id, 'block', file=log_file)
          # The number has to be 1
          number = int(requirement_value['number'])
          assert number == 1

          institution = requirement_value['institution']
          block_type = requirement_value['block_type']
          block_value = requirement_value['block_value']
          with psycopg.connect('dbname=cuny_curriculum') as conn:
            with conn.cursor(row_factory=namedtuple_row) as cursor:
              blocks = cursor.execute("""
              select institution, requirement_id, block_type, block_value, title, parse_tree
                from requirement_blocks
               where institution = %s
                 and block_type = %s
                 and block_value = %s
                 and period_stop ~* '^9'
              """, (institution, block_type, block_value))
              if cursor.rowcount != number:
                # HOW TO HANDLE THIS?
                suffix = '' if cursor.rowcount == 1 else 's'
                print(f'{institution} {requirement_id} Block requirement found '
                      f'{cursor.rowcount} row{suffix} ({number} needed)', file=todo_file)
                return
              for row in cursor:
                process_block(row, context_list + [requirement_name])
          return

        case 'blocktype':
          print(institution, requirement_id, 'blocktype', file=log_file)
          # No observed cases where the number of blocks is other than one and the type of block is
          # other than Concentration. But in two cases (LEH 1298 and 1300), the containing block
          # type is CONC instead of MAJOR. (The exclamation point in the log message is to make
          # these cases easier to find! It's not excitement!!)
          number = int(node[requirement_type]['number'])
          suffix = '' if number == 1 else 's'
          req_type = node[requirement_type]['block_type']
          req_type = 'Concentration' if req_type.upper() == 'CONC' else req_type.title()
          print(f'{institution} {requirement_id} BlockType {req_type} in body', file=todo_file)
          return

        case 'class_credit':
          print(institution, requirement_id, 'class_credit', file=log_file)
          # This is where course lists turn up, in general.
          try:
            if course_list := node[requirement_type]['course_list']:
              map_courses(institution, requirement_id, title,
                          context_list + [requirement_name], course_list)
          except KeyError:
            # Course List is an optional part of ClassCredit
            return

        case 'conditional':
          print(institution, requirement_id, 'conditional', file=log_file)
          # Use the condition as the pseudo-name of this requirement
          # UNABLE TO HANDLE RULE_COMPLETE UNTIL THE CONDITION IS EVALUATED
          condition = node[requirement_type]['condition']
          for if_true_dict in node[requirement_type]['if_true']:
            traverse_body(if_true_dict, context_list + ['IF ' + condition])
          try:
            for if_false_dict in node[requirement_type]['if_false']:
              traverse_body(if_true_dict, context_list + ['IF NOT ' + condition])
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
              select institution, requirement_id, block_type, block_value, title, parse_tree
                from requirement_blocks
               where institution = %s
                 and requirement_id = %s
                 and period_stop ~* '^9'
              """, (node[requirement_type]['institution'],
                    node[requirement_type]['requirement_id']))
              if cursor.rowcount != 1:
                print(f'{institution} {requirement_id} Copy Rules found {cursor.rowcount} current '
                      f'blocks.', file=log_file)
                return
              row = cursor.fetchone()
              if f'{row.institution} {row.requirement_id}' in context_list:
                print(f'{context_list[0]} Circular Copy Rules', file=log_file)
              else:
                process_block(row, context_list)
          return

        case 'course_list_rule':
          print(institution, requirement_id, 'course_list_rule', file=log_file)
          # There might be a remark associated with the course list
          local_context_list = [requirement_name]
          try:
            local_context_list.append(node[requirement_type]['remark'])
          except KeyError:
            pass

          try:
            if course_list := node[requirement_type]['course_list']:
              map_courses(institution, requirement_id, title,
                          context_list + local_context_list, course_list)
          except KeyError:
            # Can't have a Course List Rule w/o a course list
            print(f'{institution} {requirement_id}: Course List Rule w/o a Course List',
                  file=sys.stderr)
          return

        case 'group_requirements':
          # Group requirements is a list, so it should not show up here.
          exit(f'{institution} {requirement_id}: Group Requirements')
          # A list of group requirements, each of which contains a list of groups, each of which
          # contains a list of requirements, each of which contains a list of courses. :-)
          assert isinstance(node[requirement_type], list)
          for group_requirement in node[requirement_type]:
            try:
              label_str = group_requirement['label']
              number = int(group_requirement['number'])
              group_list = group_requirement['group_list']
              num_groups = len(group_list)
            except (KeyError, ValueError) as err:
              exit(f'{institution} {requirement_id}: missing/invalid {err}\n{node}')
            for index, group in enumerate(group_list):
              print(institution, requirement_id, 'Group', label_str, number, num_groups, index,
                    list(groupkeys()), file=debug_file)

        case 'rule_complete':
          print(institution, requirement_id, 'rule_complete', file=log_file)
          # is_complete may be T/F
          # rule_tag is followed by a name-value pair. If the name is RemarkJump, the value is a URL
          # for more info. Otherwise, the name-value pair is used to control formatting of the rule.
          # This happens only inside conditionals, where the idea will be to look at what whether
          # it's in the true or false leg, what the condition is, and whether this is True or False
          # to infer what requirement must or must not be met. We're looking at YOU, Lehman ACC-BA.

          print(f'{institution} {requirement_id} rule_complete in body', file=todo_file)
          return

        case 'course_list':
          print(institution, requirement_id, 'course_list in body', file=todo_file)
          return

        case 'group_requirement':
          print(institution, requirement_id, 'group_requirement in body', file=todo_file)
          return

        case 'subset':
          print(institution, requirement_id, 'Subset', file=log_file)
          # Process the valid rules in the subset

          # Track MaxTransfer and MinGrade restrictions (qualifiers).
          restrictions = get_restrictions(requirement_value)

          for key, rule in node[requirement_type].items():

            match key:

              case 'block':
                print(f'{institution} {requirement_id} Subset block', file=todo_file)
                for block_dict in rule:
                  assert isinstance(block_dict, dict)
                return

              case 'blocktype':
                print(f'{institution} {requirement_id} Subset blocktype', file=todo_file)
                return

              case 'class_credit_list' | 'conditional' | 'course_lists' | 'group_requirements':
                print(f'{institution} {requirement_id} Subset {key}', file=log_file)
                assert isinstance(rule, list)
                for rule_dict in rule:
                  try:
                    local_requirement_name = rule_dict.pop('label')
                  except KeyError:
                    local_requirement_name = None
                  local_context = [] if requirement_name == '' else [requirement_name]
                  if local_requirement_name:
                    local_context.append(local_requirement_name + restrictions)
                  # if len(local_context) == 0:
                  #   print(f'{institution} {requirement_id}: Rule with no name.', file=sys.stderr)
                  traverse_body(rule_dict, context_list + local_context)
                return

              case 'copy_rules':
                print(f'{institution} {requirement_id} Subset copy_rules', file=todo_file)
                assert isinstance(rule, dict)
                return

              case 'maxperdisc' | 'mingpa' | 'minspread' | 'noncourse' | 'share':
                # Ignored Qualifiers and rules
                return

              case _:
                print(f'Unhandled Subset key: {key:20} {str(type(rule)):10} {len(rule)}',
                      file=sys.stderr)
                return

            print(institution, requirement_id, f'Unimplemented {key}', file=sys.stderr)

        case 'noncourse' | 'proxy_advice' | 'remark':
          # Ignore These
          return

        case _:
          print(f'Unhandled requirement_type: {requirement_type}', file=sys.stderr)
          return

  else:
    # Not a dict or list
    print(f'Unhandled node of type {type(node)} ({node})', file=sys.stderr)
    return


# main()
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  """ Get a parse tree from the requirements_table and walk it. If no
  """
  parser = ArgumentParser()
  parser.add_argument('-i', '--institution', default='qns')
  parser.add_argument('-r', '--requirement_id')
  parser.add_argument('-t', '--type', default='major')
  parser.add_argument('-v', '--value', default='csci-bs')
  args = parser.parse_args()

  empty_tree = "'{}'"

  programs_writer.writerow(['Institution',
                            'Requirement ID',
                            'Type',
                            'Code Credits',
                            'Total',
                            'Max Transfer',
                            'Min Residency',
                            'Min Grade',
                            'Min GPA'])

  requirements_writer.writerow(['Insteitution',
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
      if args.institution.upper() == 'ALL':
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
        cursor.execute(""" select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title,
                                  parse_tree
                             from requirement_blocks
                            where institution {institution_op} %s
                              and requirement_id = %s
                            order by institution
                       """, (institution, requirement_id))
      else:
        block_type = [args.type.upper()]
        if 'ALL' in block_type:
          block_type = ['MAJOR', 'MINOR', 'CONC']

        block_value = args.value.upper()
        if block_value == 'ALL':
          block_value = '^.*$'
          value_op = '~*'
        else:
          value_op = '='
        cursor.execute(f"""select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title,
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
      for row in cursor:
        if quarantine_dict.is_quarantined((row.institution, row.requirement_id)):
          continue

        # If this is the first time this instution has been encountered, create a dict mapping
        # courses to their course_id:offer_nbr values
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

        process_block(row)
