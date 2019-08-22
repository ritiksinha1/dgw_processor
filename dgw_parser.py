#! /usr/local/bin/python3

import argparse
import psycopg2
from psycopg2.extras import NamedTupleCursor

# Unit test
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('programs', nargs='+')
  parser.add_argument('-i', '--institution', default='QNS01')
  parser.add_argument('-t', '--program_types', nargs='*', required=True)
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-v', '--verbose', action='store_true', default=False)
  args = parser.parse_args()

  type_names = {'maj': 'major', 'con': 'concentration', 'min': 'minor'}
  # Put arguments in canonical form
  query_base = 'select requirement_text from requirement_blocks where '
  institution = f'{args.institution.lower()[0:3]}'

  program_types = [type_names[t.lower()[0:3]] for t in args.program_types]
  type_list = []
  for program_type in program_types:
    if program_type == 'major':
      type_list += ['major1 = %s', 'major2 = %s']
    else:
      type_list.append(f"{program_type} = %s")
  type_clause = ' or '.join(type_list)

  conn = psycopg2.connect('dbname=cuny_programs')
  cursor = conn.cursor(cursor_factory=NamedTupleCursor)
  for program in args.programs:
    program_code = program.upper()
    types = [f'{program}'] * type_clause.count('%s')
    query = f"""
              select * from requirement_blocks
              where institution = '{institution}'
              and ({type_clause})
              order by period_start desc
            """
    cursor.execute(query, types)
    print(cursor.rowcount)
    for row in cursor.fetchall():
      print(row.block_type, row.block_value, row.period_start, row.period_stop,
            len(row.requirement_text))
