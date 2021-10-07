#! /usr/local/bin/python3

import argparse
import os
import sys

import datetime

from pgconnection import PgConnection

if __name__ == '__main__':

  parser = argparse.ArgumentParser('Look at parse tree properties')
  parser.add_argument('--timeouts', action='store_true')

  args = parser.parse_args()

  conn = PgConnection()
  cursor = conn.cursor()

  if args.timeouts:
    with open('rerun.sh', 'a') as reruns:
      print(f'# {datetime.datetime.now().isoformat()}', file=reruns)

      # Get timeout blocks
      cursor.execute(f"""
                     select institution, requirement_id, parse_tree
                       from requirement_blocks
                      where parse_tree->'error' is not null
                      """)
      if cursor.rowcount == 0:
        print('No error blocks found')
      else:
        for row in cursor.fetchall():
          parse_tree = row.parse_tree
          error_message = parse_tree['error']
          if 'Timeout' in error_message:
            print(f'dgw_parser.py -i {row.institution} -ra {row.requirement_id} -ti 1800',
                  file=reruns)
          print(f'{row.institution} {row.requirement_id} {error_message}')
      print('# end', file=reruns)
      exit()

  cursor.execute("""
  select institution, requirement_id, block_type, block_value, parse_tree
    from requirement_blocks
   where period_stop ~* '^9'
     and block_type in ('MAJOR', 'MINOR', 'CONC')
     and parse_tree->'error' is null
order by institution, block_type, block_value
  """)
  print(f'{cursor.rowcount} blocks')
  for row in cursor.fetchall():
    parse_tree = row.parse_tree
    try:
      header_list = parse_tree['header_list']
      header_types = ' '.join([type(item).__name__ for item in header_list])
    except KeyError:
      header_types = 'None'
    try:
      body_list = parse_tree['body_list']
      body_types = ' '.join([type(item).__name__ for item in body_list])
    except KeyError:
      body_types = 'None'
    print(row.institution, row.requirement_id, header_types, '\n              ', body_types)
