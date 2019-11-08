#! /usr/local/bin/python3

""" Look up a degree, major, minor, concentration, or other requirement block, construct a
    Requirements object for it, and output the html/json/string representation.
"""
import argparse
import psycopg2
from psycopg2.extras import NamedTupleCursor

from requirements import Requirements, Catalogs


# Unit test
if __name__ == '__main__':
  # Set up parser
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-f', '--format')
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-t', '--types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-a', '--development', action='store_true', default=False)

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

  # Development: whatever I want to see
  if args.development:
    query = 'select * from requirement_blocks'
  else:
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
    if not args.development:
      print('==================================================\n<h1>', college_name, '</h1>')
      print('<h2>', row.block_value, row.block_type.title(), '</h2>')
    catalogs = Catalogs(row.period_start, row.period_stop)
    num_catalogs = len(catalogs.which_catalogs)
    if num_catalogs == 0:
      catalog_str = 'College catalog.'
    elif num_catalogs == 1:
      catalog_str = f'{catalogs.which_catalogs[0]} Catalog.'
    else:
      catalog_str = f'{catalogs.which_catalogs[0]} and '
      f'{catalogs.which_catalogs[1]} Catalogs.'
    # years_str = ', '.join([f'{year}' for year in years])
    # k = years_str.rfind(',')
    # if k > 0:
    #   k += 1
    #   years_str = years_str[:k] + ' and' + years_str[k:]
    # if self.catalogs.first_academic_year != self.catalogs.last_academic_year:
    #   suffix = 's'
    # else:
    #   suffix = ''
    # returnVal = f"""
    #             <h2>Requirements for Catalog Year{suffix} {str(self.catalogs)}</h2>
    #             <p>Academic years starting in the fall of {years_str}</p>
    #             <p>This program appears in the {catalog_str}</p>
    #             """
    requirements = Requirements(row.requirement_text, row.institution)
    if args.debug:
      print(requirements.debug())
