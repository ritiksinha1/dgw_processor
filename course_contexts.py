#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?
"""

from argparse import ArgumentParser
from pgconnection import PgConnection
from dgw_interpreter import dgw_interpreter

from pprint import pprint

parser = ArgumentParser('Look up course list contexts')
parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
parser.add_argument('-v', '--block_values', nargs='*', default=['all'])
parser.add_argument('-f', '--force', action='store_true')
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
      select block_value
        from requirement_blocks
       where institution = '{institution}'
         and block_type = '{block_type}'
  """)
        block_values = [row.block_value.upper() for row in cursor.fetchall()
                        if not row.block_value.isdigit()
                        and '?' not in row.block_value]
      for block_value in block_values:
        cursor.execute(f"""
      select period_stop, requirement_text, header_list, body_list
        from requirement_blocks
       where institution = '{institution}'
         and block_type = '{block_type}'
         and block_value ~* '^{block_value}$'
  """)
        for row in cursor.fetchall():
          print(f'\n{institution} {block_type} {block_value}\n{row.requirement_text}', file=debug)
          if period == 'current' and row.period_stop != '99999999':
            continue
          print(f'{institution} {block_type} {block_value} {period}')
          header_list, body_list = (row.header_list, row.body_list)
          if len(header_list) == 0 or len(body_list) == 0 or args.force:
            header_list, body_list = dgw_interpreter(institution, block_type, block_value,
                                                     period_range=period)

          # Find course lists and show their sizes and contexts
          print(f'\nHEADER')
          pprint(header_list, sort_dicts=False)
          print('\nBODY')
          pprint(body_list, sort_dicts=False)
          # for node in header_list:
          #   for key in node.keys():
          #     print('Header', key)
          # for node in body_list:
          #   for key in node.keys():
          #     print('Body', key)
