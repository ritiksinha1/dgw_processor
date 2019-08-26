#! /usr/local/bin/python3

import argparse
import psycopg2
from psycopg2.extras import NamedTupleCursor

from requirements import Requirements


# Unit test
if __name__ == '__main__':
  # Set up parser
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-p', '--programs', nargs='+')
  parser.add_argument('-i', '--institutions', nargs='*')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-v', '--verbose', action='store_true', default=False)

  # Parse args and handle default list of institutions
  args = parser.parse_args()
  if args.institutions is None:
    institutions = ['QNS01']
  else:
    institutions = args.institutions
  if args.debug:
    print('programs:', args.programs)
    print('institutions:', institutions)

  # Create dict of known colleges
  colleges = dict()
  crse_conn = psycopg2.connect('dbname=cuny_courses')
  crse_cursor = crse_conn.cursor(cursor_factory=NamedTupleCursor)
  crse_cursor.execute('select substr(lower(code),0,4) as code, name from institutions')
  for row in crse_cursor.fetchall():
    colleges[row.code] = row.name
  crse_conn.close()

  # Set up to query program information
  prog_conn = psycopg2.connect('dbname=cuny_programs')
  prog_cursor = prog_conn.cursor(cursor_factory=NamedTupleCursor)
  query_base = 'select requirement_text from requirement_blocks where '
  type_list = ['major1 = %s', 'major2 = %s', 'minor = %s', 'concentration = %s']
  type_clause = f" and ({' or '.join(type_list)})"

  # Go through the selected programs for each college
  for institution in institutions:
    college_code = institution.lower()[0:3]
    college_name = colleges[college_code]
    print('<h1>', college_name, '</h1>')
    for program in args.programs:
      program_code = program.upper()
      types = [f'{program}'] * type_clause.count('%s')
      query = f"""
                select * from requirement_blocks
                where institution = '{college_code}'
                {type_clause}
                order by period_start desc
              """
      prog_cursor.execute(query, types)
      for row in prog_cursor.fetchall():
        print('<h2>', row.block_value, row.block_type.title(), '</h2>')
        if args.debug:
          print(row.requirement_text)
        requirements = Requirements(row.requirement_text, row.period_start, row.period_stop).html()
        print(requirements)
