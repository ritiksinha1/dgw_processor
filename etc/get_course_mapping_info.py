#! /usr/local/bin/python3
""" Look up the requirements that a course satisfies.
    Be sure to run load_mapping_tables.py after running mapper.
"""

import os
import psycopg
import subprocess
import sys

from datetime import date
from pathlib import Path
from psycopg.rows import namedtuple_row, dict_row


# Be sure course_mapping tables are current wrt the csv files
programs_file = Path('/Users/vickery/Projects/dgw_processor/course_mapper.programs.csv')
stats_info = programs_file.stat()

file_size = stats_info.st_size
if file_size < 100000:
  print(f'course_mapper.programs.csv ({file_size:,} bytes) looks small. Continue (yN)? ', end='')
  if not input().lower().startswith('y'):
    exit('Quitting')

file_date = str(date.fromtimestamp(stats_info.st_mtime))

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:

    # If mapping tables in db are not up to date, refresh them.
    cursor.execute("""
    select update_date from updates where table_name = 'course_mappings'
    """)
    update_date = None
    if cursor.rowcount != 1:
      print('Unable to stat course_mappings date')
    else:
      update_date = str(cursor.fetchone().update_date)
    if update_date != file_date:
      print(f'{update_date=} :: {file_date=} Update course_mapping tables (Yn)? ', end='')
      reply = input()
      if not reply.lower().startswith('n'):
        subprocess.run('./load_mapping_tables.py')
        update_date = str(date.today())
    if update_date is None:
      exit(f'Course mapping tables do not match course_mapping.*.csv\nQuitting')

    # Cache GenEd info
    cursor.execute("""
    select designation, description from designations
     where description ~ 'Flexible Core'
        or description ~ 'Required Core'
    """)
    # for row in cursor:
    #   print(row)
    geneds = {row.designation: row.description for row in cursor}


# get_requirements()
# -------------------------------------------------------------------------------------------------
def get_requirements(course_str: str) -> dict:
  """ Return a dict with course_info and list of requirements the course can satisfy
      Examples of valid course_str values:
        QNS CSCI 100 (institution, discipline, and catalog number)
        123456 (course_id with implied offer_nbr of 1)
        123456:2 (course_id with explicit offer_nbr)
        Malformed course_str raises ValueError
  """
  # Look up the course's catalog information ...
  if ' ' in course_str:
    # ... by [discipline catalog_number]
    institution, discipline, catalog_number = course_str.split()
    course_query = f"""
    select institution, course_id, offer_nbr, discipline, catalog_number, title, designation,
           course_status,
           attributes
      from cuny_courses
     where institution ~* '{institution}'
       and discipline ~* '^{discipline}$'
       and catalog_number ~* '^{catalog_number}$'
       and course_status = 'A'
    """
  else:
    if ':' in course_str:
      # ... by [course_id:offer_nbr]
      course_id, offer_nbr = [int(part) for part in course_str.split(':')]
    else:
      # ... by [course_id and implicit offer_nbr]
      course_id = int(course_str)
      offer_nbr = 1
    course_query = f"""
    select institution, course_id, offer_nbr, discipline, catalog_number, title, designation,
           course_status,
           attributes
      from cuny_courses
     where course_id = '{course_id}'
       and offer_nbr = '{offer_nbr}'
       and course_status = 'A'
    """
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=dict_row) as cursor:
      cursor.execute(course_query)
      if cursor.rowcount != 1:
        raise ValueError(f'{course_str} matches {cursor.rowcount} courses')
      course_info_dict = cursor.fetchone()
      course_id_str = f'{course_info_dict["course_id"]:06}:{course_info_dict["offer_nbr"]}'
      # copt = None
      # course_info = {'course_id': row.course_id,
      #                'offer_nbr': row.offer_nbr,
      #                'course': f'{row.discipline} {row.catalog_number}',
      #                'title': row.title,
      #                'gened': gened}

      cursor.execute(f"""
      select program_name, context
        from requirements r, course_mappings m
       where m.course_id = '{course_id_str}'
         and m.requirement_key = r.requirement_key
      """)
      requirement_list = [row for row in cursor]

  return {'course_info': course_info_dict, 'requirements': requirement_list}


if __name__ == '__main__':
  """ Command line interactive test
  """
  try:
    if len(sys.argv) < 1:
      raise ValueError
    requirements_dict = get_requirements(' '.join(sys.argv[1:]))

    print(f'Course Info')
    course_info = requirements_dict['course_info']
    course = f"{course_info['discipline']} {course_info['catalog_number']}"
    gened = course_info['designation'] if course_info['designation'] in geneds.keys() else None
    print(f"{course_info['course_id']}:{course_info['offer_nbr']} {course} "
          f"{course_info['title']}\nGenEd: {gened}")

    print('Requirements')
    requirements = requirements_dict['requirements']
    for requirement in requirements:
      print(f"  {requirement['program_name']}")
    if len(requirements) == 0:
      print('  None')
  except ValueError as ve:
    print(f"""
Usage: {sys.argv[0]} course_str
Examples:
  QNS CSCI 100  # institution, discipline, and catalog number
  123456        # course_id with implicit offer_nbr = 1
  123456:2      # course_id with explicit offer_nbr
    """)
