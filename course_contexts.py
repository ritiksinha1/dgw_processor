#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?
"""

from argparse import ArgumentParser
from pgconnection import PgConnection

parser = ArgumentParser('Look up course list contexts')
parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
parser.add_argument('-n', '--names', nargs='*', default=['all'])
parser.add_argument('-p', '--period', default='current')
args = parser.parse_args()
period = args.period.lower()
assert period in ['all', 'latest', 'current']

conn = PgConnection()
cursor = conn.cursor()
institutions = [inst.upper().strip('01') for inst in args.institutions]
for institution in institutions:
  institution = institution + '01'
  block_types = [arg.upper() for arg in args.block_types]
  for block_type in block_types:
    assert block_type in ['MAJOR', 'CONC', 'MINOR']
    names = [name.lower() for name in args.names]
    if 'all' in names:
      cursor.execute(f"""
    select block_value
      from requirement_blocks
     where institution = '{institution}'
       and block_type = '{block_type}'
""")
      names = [row.block_value.lower() for row in cursor.fetchall()
               if not row.block_value.isdigit()]
    for name in names:
      cursor.execute(f"""
    select period_stop, header_list, body_list
      from requirement_blocks
     where institution = '{institution}'
       and block_type = '{block_type}'
       and block_value ~* '^{name}$'
""")
      for row in cursor.fetchall():
        print(cursor.query)
        if period == 'current' and row.period_stop != '99999999':
          continue
        print(f'{institution} {block_type} {name} {period}')
