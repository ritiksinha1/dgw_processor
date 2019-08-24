#! /usr/local/bin/python3

import argparse
import psycopg2
from psycopg2.extras import NamedTupleCursor

import re
from requirements import Requirements


def parse_catalog_years(period_start, period_stop):
  """ First Year = CCYY-YY or CCYY-CCYY if centuries differ
      Last Year = CCYY-YY or CCYY-CCYY or 'Now'
      Other values: 'Missing', 'Unknown', or 'Unused'
      Catalogs: list which will be either empty, Undergraduate, Graduate, or both

  """
  catalogs = set()
  first_academic_year = ''
  last_academic_year = ''

  m_start = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_start)
  if m_start is None:
    first_academic_year = 'Unknown'
  else:
    century_1, year_1, century_2, year_2, catalog = m_start.groups()
    if century_1 != century_2:
      first_academic_year = f'{century_1}{year_1}-{century_2}{year_2}'
    else:
      first_academic_year = f'{century_1}{year_1}-{year_2}'
    if catalog == 'U':
      catalogs.add('Undergraduate')
    if catalog == 'G':
      catalogs.add('Graduate')

  if re.search(r'9999+', period_stop):
    last_academic_year = 'Now'
  else:
    m_stop = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_stop)
    if m_stop is None:
      last_academic_year = 'Unknown'
    else:
      century_1, year_1, century_2, year_2, catalog = m_stop.groups()
      if century_1 != century_2:
        last_academic_year = f'{century_1}{year_1}-{century_2}{year_2}'
      else:
        last_academic_year = f'{century_1}{year_1}-{year_2}'
      if catalog == 'U':
        catalogs.add('Undergraduate')
      if catalog == 'G':
        catalogs.add('Graduate')

  if first_academic_year != last_academic_year:
    return f'{first_academic_year} to {last_academic_year}', catalogs
  else:
    return f'{first_academic_year}', catalogs


def parse_requirements(requirement_text):
  """ Return Requirements object
      This is going to be a class with a json member and a __str__() method.
  """
  requirements = Requirements(requirement_text)
  return requirements.html()


# Unit test
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('programs', nargs='+')
  parser.add_argument('-i', '--institution', default='QNS01')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-v', '--verbose', action='store_true', default=False)
  args = parser.parse_args()

  # Put arguments in canonical form
  query_base = 'select requirement_text from requirement_blocks where '
  institution = f'{args.institution.lower()[0:3]}'

  type_list = ['major1 = %s', 'major2 = %s', 'minor = %s', 'concentration = %s']
  type_clause = f" and ({' or '.join(type_list)})"

  conn = psycopg2.connect('dbname=cuny_programs')
  cursor = conn.cursor(cursor_factory=NamedTupleCursor)
  for program in args.programs:
    program_code = program.upper()
    types = [f'{program}'] * type_clause.count('%s')
    query = f"""
              select * from requirement_blocks
              where institution = '{institution}'
              {type_clause}
              order by period_start desc
            """
    cursor.execute(query, types)
    for row in cursor.fetchall():
      request_block = {}
      request_block['institution'] = row.institution
      (request_block['catalog_years'],
       request_block['catalogs']) = parse_catalog_years(row.period_start, row.period_stop)
      request_block['program_type'] = row.block_type
      request_block['program'] = row.block_value
      request_block['requirements'] = parse_requirements(row.requirement_text)
      print(request_block)
