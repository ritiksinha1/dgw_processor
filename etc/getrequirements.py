#! /usr/local/bin/python3
""" Look up the requirements that a course satisfies.
    Be sure to run load_mapper_tables.py after running mapper.
"""

import os
import psycopg
import sys

from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""
    select designation, description from designations
     where description ~ 'Flexible Core'
        or description ~ 'Required Core'
    """)
    # for row in cursor:
    #   print(row)
    geneds = {row.designation: row.description for row in cursor}


def get_requirements(course_str: str) -> list:
  """ Examples of valid course_str values:
        QNS CSCI 100 (institution, discipline, and catalog number)
        123456 (course_id with implied offer_nbr of 1)
        123456:2 (course_id with explicit offer_nbr)
        Malformed course_str raises ValueError
  """
  if ' ' in course_str:
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
      course_id, offer_nbr = [int(part) for part in course_str.split(':')]
    else:
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
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute(course_query)
      if cursor.rowcount != 1:
        raise ValueError(f'{course_str} matches {cursor.rowcount} courses')
      row = cursor.fetchone()
      gened = row.designation if row.designation in geneds.keys() else None
      copt = None
      course_info = {'course_id': row.course_id,
                     'offer_nbr': row.offer_nbr,
                     'course': f'{row.discipline} {row.catalog_number}',
                     'title': row.title,
                     'gened': gened}
      course_id_str = f'{row.course_id:06}:{row.offer_nbr}'

  with psycopg.connect('dbname=course_mappings') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute(f"""
      select distinct program_name
        from requirements r, course_mappings m
       where m.course_id = '{course_id_str}'
         and m.requirement_key = r.requirement_key
      """)
      requirement_list = [row.program_name for row in cursor]

  return course_info, requirement_list


if __name__ == '__main__':
  try:
    course_info, requirements = get_requirements(' '.join(sys.argv[1:]))
    print(f"{course_info['course_id']}:{course_info['offer_nbr']} {course_info['course']} "
          f"{course_info['title']}\nGenEd: {course_info['gened']}\nRequirements: ")
    for requirement in requirements:
      print(f'  {requirement}')
    if len(requirements) == 0:
      print('  None')
  except ValueError as ve:
    print(ve)

