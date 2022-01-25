#! /usr/local/bin/python3
""" List program requirements and courses that satisfy them.
"""

import os
import psycopg
import sys
from argparse import ArgumentParser
from collections import namedtuple, defaultdict
from recordclass import recordclass
from psycopg.rows import namedtuple_row

BlockInfo = recordclass('BlockInfo', 'institution requirement_id block_type block_value title '
                        'parse_tree class_credits max_transfer min_grade')

log_file = open(f'{__file__.replace(".py", ".log")}', 'w')


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
  """ Write a message to the logfile
  """
  print(f'{block_info.institution} {block_info.requirement_id} {block_info.block_type:6} '
        f'{block_info.block_value:10}', message, file=log_file)


# key_struct()
# -------------------------------------------------------------------------------------------------
def key_struct(arg, depth=0):
  """ Treewalk, where the tree structure is implemented using nested dicts, but nodes can be lists.
  """
  # print(f'key_struct({arg=}, {depth=}')
  leader = f'..' * depth
  if isinstance(arg, list):
    print(f'{leader}[{len(arg)}]', end='')
    for value in arg:
      if isinstance(value, dict):
        key_struct(value, 1 + depth)
      elif isinstance(value, list):
        for item in value:
          key_struct(item, 1 + depth)
      else:
        print(f' {value}')
  elif isinstance(arg, dict):
    for key, value in arg.items():
      print(f'{leader}{key}:', end='')
      if isinstance(value, list) or isinstance(value, dict):
        print()
        key_struct(value, 1 + depth)
      else:
        print(f' {value}')


# traverse_body()
# -------------------------------------------------------------------------------------------------
def traverse_body(block_info: namedtuple, context: list) -> None:
  """ Extract Requirement names and course lists from body rules.
  """

  try:
    body_list = block_info.parse_tree['body_list']
  except KeyError:
    write_log(block_info, f'No body list in parse tree')
    return

  for body_item in body_list:
    if isinstance(body_item, list):
      pass
    elif isinstance(body_item, dict):
      pass
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

            if value['min_classes'] is None and value['max_classes'] is None:
              if value['min_credits'] == value['max_credits']:
                class_credits = float(value['max_credits'])
                block_info.class_credits = f'{class_credits:5.1f} Credits'
              else:
                min_credits = float(value['min_credits'])
                max_credits = float(value['max_credits'])
                block_info.class_credits = f'{min_credits:5.1f}-{max_credits:4.1f} Credits'
            elif value['min_credits'] is None and value['max_credits'] is None:
              if value['min_classes'] == value['max_classes']:
                class_credits = int(value['max_classes'])
                block_info.class_credits = f'{class_credits:5} Classes'
              else:
                min_classes = int(value['min_classes'])
                max_classes = int(value['max_classes'])
                block_info.class_credits = f'{min_classes:5}-{max_classes} Classes'
            else:
              # *** THERE IS AN AND LIST WITH BOTH CLASSES AND CREDITS ***
              write_log(block_info, f'Class/Credit: {value}')

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
              block_info.max_transfer = f'{number:0.1f} credits'
            else:
              suffix = '' if int(number) == 1 else 'es'
              block_info.max_transfer = f'{int(number)} class{suffix}'

          case 'header_minclass':
            # THERE WOULD BE A COURSE LIST HERE
            pass
          case 'header_mincredit':
            # THERE WOULD BE A COURSE LIST HERE
            pass
          case 'header_mingpa':
            pass
          case 'header_mingrade':
            if label_str := value['label']:
              write_log(block_info, f'MinGrade label: {label_str}')

            block_info.min_grade = letter_grade(float(value['mingrade']['number']))

          case 'header_minperdisc':
            pass
          case 'header_minres':
            pass
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
  """ Get a parse tree from the requirements_table and walk it.
  """
  parser = ArgumentParser()
  parser.add_argument('-i', '--institution', default='qns')
  parser.add_argument('-r', '--requirement_id')
  parser.add_argument('-t', '--type', default='major')
  parser.add_argument('-v', '--value', default='csci-bs')
  args = parser.parse_args()

  empty_tree = "'{}'"

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
        # Augment db info with default values for total credits, max transfer, and min grade
        block_info = BlockInfo._make(row + (' ----        ', 'No Limit', 'Any'))
        try:
          traverse_header(block_info)
          print(f'{block_info.institution[0:3]} {block_info.requirement_id} '
                f'{block_info.block_type:6} {block_info.block_value:10} {block_info.class_credits};'
                f' Min Grade: {block_info.min_grade:3}; Max Transfer: '
                f'{block_info.max_transfer}')
          traverse_body(block_info, [])
        except KeyError:
          print(f'No header_list for', institution, requirement_id, block_type, block_value,
                title, file=sys.stderr)
          pass
