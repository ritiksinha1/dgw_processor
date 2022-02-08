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


log_file = open(f'{__file__.replace(".py", ".log")}', 'w')
csv_file = open(f'{__file__.replace(".py", ".progs.csv")}', 'w')
map_file = open(f'{__file__.replace(".py", ".map.csv")}', 'w')

writer = csv.writer(csv_file)
mapper = csv.writer(map_file)


def dict_factory():
  """ Support for three index levels, as in courses_by_institution.
  """
  return defaultdict(dict)


courses_by_institution = defaultdict(dict_factory)


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
  """ Write a message to the logfile.
  """
  print(f'{block_info.institution} {block_info.requirement_id} {block_info.block_type:6} '
        f'{block_info.block_value:10}', message, file=log_file)


# write_map()
# -------------------------------------------------------------------------------------------------
def write_map(block_info: namedtuple, context_list: list, course_list: dict):
  """ Write courses and their with clauses to the map file.
      Object returned by courses_cache():
        CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr title credits career')
  """
  context_str = '\n'.join(context_list)
  for course_area in range(len(course_list['scribed_courses'])):
    for course_tuple in course_list['scribed_courses'][course_area]:
      discipline, catalog_number, with_clause = course_tuple
      if with_clause is not None:
        with_clause = f'With ({with_clause})'
      for key, value in courses_cache((block_info.institution, discipline, catalog_number)).items():
        mapper.writerow([block_info.institution, block_info.requirement_id, block_info.title,
                        context_str, f'{value.course_id}:{value.offer_nbr}', value.career,
                        f'{key}: {value.title}', with_clause])


# traverse_body()
# -------------------------------------------------------------------------------------------------
def traverse_body(node: Any, context_list: list) -> None:
  """ Extract Requirement names and course lists from body rules. Element 0 of the context list is
      always information about the block, including header restrictions: MaxTransfer, MinResidency,
      MinGrade, and MinGPA. The context list is augmented with requirement names (labels),
      conditions, and residency/grade requirements during recursion.
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

  institution, requirement_id, block_type, block_value = (block_info.institution,
                                                          block_info.requirement_id,
                                                          block_info.block_type,
                                                          block_info.block_value)
  if isinstance(node, list):
    for item in node:
      traverse_body(item, context_list)

  elif isinstance(node, dict):
    node_keys = list(node.keys())
    if num_keys := len(node_keys) != 1:
      print(f'Node with {num_keys} keys: {node_keys}', sys.stderr)
    requirement_type = node_keys[0]
    if isinstance(node[requirement_type], dict):
      try:
        requirement_name = node[requirement_type]['label']
      except KeyError:
        print(f'{requirement_type} with no label', file=sys.stderr)
        return
      try:
        if course_list := node[requirement_type]['course_list']:
          write_map(block_info, context_list + [requirement_name], course_list)
      except KeyError:
        pass

    match requirement_type:
      case 'block':
        pass
      case 'blocktype':
        pass
      case 'class_credit':
        pass
      case 'conditional':
        pass
      case 'course_list_rule':
        pass
      case 'copy_rules':
        pass
      case 'group_requirements':
        pass
      case 'noncourse':
        pass
      case 'proxy_advice':
        pass
      case 'remark':
        pass
      case 'rule_complete':
        pass
      case 'subset':
        pass
      case _:
        print(f'Unexpected requirement_type: {requirement_type}', file=sys.stderr)
  else:
    pass


# traverse_header()
# -------------------------------------------------------------------------------------------------
def traverse_header(block_info: namedtuple) -> None:
  """ Extract program-wide qualifiers: MinGrade (but not MinGPA) and residency requirements,
  """

  try:
    header_list = block_info.parse_tree['header_list']
  except KeyError:
    write_log(block_info, f'No header list in parse tree')
    return

  for header_item in header_list:
    if not isinstance(header_item, dict):
      print(header_item, 'is not a dict')
    else:
      for key, value in header_item.items():
        match key:
          case 'header_class_credit':
            if label_str := value['label']:
              write_log(block_info, f'Class/Credit label: {label_str}')

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
            pass
          case 'copy_rules':
            pass
          case 'header_lastres':
            pass
          case 'header_maxclass':
            # THERE WOULD BE A COURSE LIST HERE
            pass

          case 'header_maxcredit':
            # THERE ARE 641 OF THESE; THEY HAVE COURSE LISTS
            # write_log(block_info, f'MaxCredit: {value}')
            pass

          case 'header_maxpassfail':
            pass
          case 'header_maxperdisc':
            # THERE WOULD BE A COURSE LIST HERE
            pass

          case 'header_maxterm':
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
            pass
          case 'header_mincredit':
            # THERE WOULD BE A COURSE LIST HERE
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
            match  (min_classes, min_credits):
              case [None, None]:
                print(f'Invalid minres {block_info}', file=sys.stderr)
              case [None, credits]:
                block_info.min_residency = f'{float(credits):.1f} credits'
              case [classes, None]:
                block_info.min_residency = f'{int(classes)} classes'
              case _:
                print(f'Invalid minres {block_info}', file=sys.stderr)

          case 'header_minterm':
            pass
          case 'noncourse':
            pass
          case 'optional':
            pass
          case 'proxy_advice':
            pass
          case 'remark':
            pass
          case 'rule_complete':
            pass
          case 'standalone':
            pass
          case 'header_share':
            pass

          case _:
            write_log(block_info, f'Unexpected {key} in header')

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

  writer.writerow(['College',
                   'Requirement ID',
                   'Type',
                   'Code',
                   'Total',
                   'Max Transfer',
                   'Min Residency',
                   'Min Grade',
                   'Min GPA'])

  mapper.writerow(['Institution',
                   'Requirement ID',
                   'Program',
                   'Requirement',
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
      print(f'{cursor.rowcount} parse tree{suffix}')
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

        # Augment db info with default values for class_credits max_transfer min_residency min_grade
        # min_gpa
        block_info = BlockInfo._make(row + ('', '', '', '', ''))
        try:
          traverse_header(block_info)

          writer.writerow([f'{block_info.institution[0:3]}',
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
        try:

          body_list = block_info.parse_tree['body_list']
          traverse_body(body_list, [])
        except KeyError as ke:
          print(ke, block_info.institution, block_info.requirement_id,
                block_info.block_type, block_info.block_value,
                block_info.title, file=sys.stderr)
