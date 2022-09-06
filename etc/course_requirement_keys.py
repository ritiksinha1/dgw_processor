#! /usr/local/bin/python3
""" Give a course, look up the keys for the requirements it satisfies.
"""

import csv
import psycopg
import subprocess
import sys

from argparse import ArgumentParser
from pathlib import Path
from psycopg.rows import namedtuple_row

parser = ArgumentParser('Look up mapping keys for a course')
parser.add_argument('course', nargs='*')
args = parser.parse_args()

if len(args.course) == 1:
  if ':' in args.course[0]:
    course_id, offer_nbr = args.course[0].split(':')
    course_id = int(course_id)
  elif args.course[0].isdigit():
    course_id = int(args.course)
    offer_nbr = '1'
  else:
    exit(f'eh? {args.course}')
elif len(args.course) == 3:
  institution, discipline, catalog_number = args.course

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:

      cursor.execute(f"""
      select institution, course_id, offer_nbr, discipline, catalog_number, title
        from cuny_courses
       where institution ~* %s
         and discipline ~* %s
         and catalog_number ~* '^{catalog_number}$'
      """, [institution, discipline])

      match cursor.rowcount:
        case 0:
          exit(f'{institution} {discipline} {catalog_number} not found')
        case 1:
          pass
        case _:
          print(f'{cursor.rowcount} matches:')
          for row in cursor:
            print(row.institution, row.discipline, row.catalog_number, row.title)
          exit()
      row = cursor.fetchone()
      course_id, offer_nbr = (row.course_id, row.offer_nbr)
      institution = row.institution
else:
  exit(f'eh? {args.course}')

target = f'{course_id:06}:{offer_nbr}'
print(f'{target=}')
with open('/Users/vickery/Projects/dgw_processor/course_mapper.course_mappings.csv') as csv_file:
  reader = csv.reader(csv_file)
  for line in reader:
    if line[1] == target:
      requirement_key = line[0]
      subprocess.run([Path('list_requirements.py'), '-k', requirement_key],
                     stdout=sys.stdout)
