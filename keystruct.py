#! /usr/local/bin/python3
""" List program requirements and courses that satisfy them.
"""

import os
import psycopg
import sys
from argparse import ArgumentParser
from collections import namedtuple, defaultdict
from psycopg.rows import namedtuple_row

log_file = open(f'{__file__.replace(".py", ".log")}', 'a')


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


def traverse_header(block_info: namedtuple) -> list:
  """ Extract program-wide qualifiers: MinGrade (but not MinGPA) and residency requirements,
  """

  return_list = []

  try:
    header_list = block_info.parse_tree['header_list']
  except KeyError:
    return return_list

  for header_item in header_list:
    if not isinstance(header_item, dict):
      print(header_item, 'is not a dict')
    else:
      for key, value in header_item.items():
        match key:
          case 'header_maxcredit':
            return_list.append('MaxCredit')
          case _:
            print(f'{block_info.institution} {block_info.requirement_id}: {key}', file=log_file)
            pass
  return return_list


if __name__ == "__main__":
  """ Get a parse tree from the requirements_table and walk it.
  """
  parser = ArgumentParser()
  parser.add_argument('-i', '--institution', default='qns')
  parser.add_argument('-r', '--requirement_id')
  parser.add_argument('-t', '--type', default='major')
  parser.add_argument('-v', '--value', default='csci-bs')
  args = parser.parse_args()

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      institution = args.institution.strip('01').upper() + '01'
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
                            where institution = %s
                              and requirement_id = %s
                       """, (institution, requirement_id))
      else:
        block_type = args.type.upper()
        assert block_type in ['MAJOR', 'MINOR', 'CONC'], f'{args.type} is not MAJOR, MINOR, or CONC'
        block_value = args.value.upper()
        if block_value == 'ALL':
          block_value = '^.*$'
          op = '~*'
        else:
          op = '='
        cursor.execute(f"""select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title,
                                  parse_tree
                             from requirement_blocks
                            where institution = %s
                              and block_type = %s
                              and block_value {op} %s
                              and period_stop ~* '^9'
                            order by block_value""", (institution, block_type, block_value))

      suffix = '' if cursor.rowcount == 1 else 's'
      print(f'{cursor.rowcount} parse tree{suffix}')
      for block_info in cursor:
        try:
          header_context = [block_info.title] + traverse_header(block_info)
          print(f'{header_context=}')
        except KeyError:
          # print(f'No header_list for', institution, requirement_id, block_type, block_value,
          #       title)
          pass
