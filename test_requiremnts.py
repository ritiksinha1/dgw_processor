#! /usr/local/bin/python3

""" Look up a degree, major, minor, concentration, or other requirement block, construct a
    Requirements object for it, and output the html/json/string representation.
"""
import argparse
import psycopg2
from psycopg2.extras import NamedTupleCursor

from requirements import Requirements


# Unit test
if __name__ == '__main__':
  # Set up parser
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-f', '--format')
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-t', '--types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--values', nargs='+', default=['CSCI-BS'])

  # Parse args and handle default list of institutions
  args = parser.parse_args()
  digits = '0123456789'
  institutions = ', '.join([f"'{i.lower().strip(digits)}'" for i in args.institutions])
  types = ', '.join([f"'{t.upper()}'" for t in args.types])
  values = ', '.join([f"'{v.upper()}'" for v in args.values])
  if args.debug:
    print(f'institutions: {institutions}')
    print(f'types: {types}')
    print(f'values: {values}')

  # Create dict of known colleges
  colleges = dict()
  course_conn = psycopg2.connect('dbname=cuny_courses')
  course_cursor = course_conn.cursor(cursor_factory=NamedTupleCursor)
  course_cursor.execute('select substr(lower(code),0,4) as code, name from institutions')
  for row in course_cursor.fetchall():
    colleges[row.code] = row.name
  course_conn.close()

  # Set up to query program information
  requirements_conn = psycopg2.connect('dbname=cuny_programs')
  requirements_cursor = requirements_conn.cursor(cursor_factory=NamedTupleCursor)
  query = f"""select *
  from requirement_blocks
  where institution in ({institutions})
  and block_type in ({types})
  and block_value in ({values})"""
  requirements_cursor.execute(query)
  # Go through the selected requirement blocks
  for row in requirements_cursor.fetchall():
    college_code = row.institution
    college_name = colleges[college_code]
    print('<h1>', college_name, '</h1>')
    print('<h2>', row.block_value, row.block_type.title(), '</h2>')
    if args.debug:
      print(row.requirement_text)
    requirements = Requirements(row.requirement_text,
                                row.period_start,
                                row.period_stop)
    print(requirements)
