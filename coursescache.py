#! /usr/local/bin/python3
""" Manage a cache of information about courses.
    The cache is indexed by [institution][discipline][catalog_number], is populated on demand by
    institution, and includes only active, non-message/non-bkcr courses. Cached info is course_id,
    offer_nbr, title, and career.
"""

import os
import re
import sys
import psycopg

from collections import namedtuple, defaultdict
from psycopg.rows import namedtuple_row


def dict_factory():
  """ Factory needed to support the triple levels of indexing
  """
  return(defaultdict(dict))


_courses_cache = defaultdict(dict_factory)
CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr title credits career')


# courses_cache()
# -------------------------------------------------------------------------------------------------
def courses_cache(idc_tuple: tuple) -> dict:
  """ If the institution hasn't been cached yet, add its courses to the cache.
      Return a possibly-empty dict of the (course_id, offer_nbr, title, career) named tuples for the
      institution/discipline/catalog_nbr. Scribe language wildcards allowed.
  """
  institution, discipline, catalog_number = idc_tuple
  if institution not in _courses_cache.keys():
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("""
          select institution, course_id, offer_nbr,
                discipline, catalog_number, title, max_credits as credits, career
            from cuny_courses
           where institution = %s
             and course_status = 'A'
             and designation not in ('MNL', 'MLA')
             and attributes !~* 'BKCR'
             and max_credits > 0.0
           order by discipline, numeric_part(catalog_number)
        """, (institution, ))
        for row in cursor:
          info = CourseTuple._make([row.course_id,
                                    row.offer_nbr,
                                    row.title,
                                    row.credits,
                                    row.career])
          _courses_cache[row.institution][row.discipline][row.catalog_number] = info

  # Simple Case
  if not ('@' in discipline or '@' in catalog_number or ':' in catalog_number):
    try:
      return ({f'{discipline} {catalog_number}':
              _courses_cache[institution][discipline][catalog_number]})
    except KeyError:
      return {}

  # Generate list of matching disciplines
  if '@' in discipline:
    regex = f'^{discipline}$'.replace('@', '.+')
    disciplines = [key for key in _courses_cache[institution].keys() if re.match(regex, key)]
  else:
    disciplines = [discipline]

  # For each discipline, look up all the courses with matching catalog numbers.

  # Handle range of catalog numbers
  #   "A range of course numbers is indicated by separating two course numbers with a colon. The
  #    course numbers cannot contain any letters or wildcards. The lower bound (left side) must be
  #    less than or equal to the upper bound (right side)."
  if ':' in catalog_number:
    l, h = [int(x) for x in catalog_number.split(':')]
    cat_num_range = range(l, h + 1)
  else:
    cat_num_range = None
  regex = f'^{catalog_number}$'.replace('@', '.+')

  return_dict = {}
  for discipline in disciplines:
    for cat_num in _courses_cache[institution][discipline].keys():
      if ((cat_num_range and cat_num.isdecimal() and int(cat_num) in cat_num_range)
         or re.match(regex, cat_num)):
        return_dict[f'{discipline} {cat_num}'] = _courses_cache[institution][discipline][cat_num]

  return return_dict


# main()
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  """ Interactive test of courses_cache()
  """
  institution = 'QNS01'
  discipline = 'CSCI'
  catalog_number = '101'
  print('? ', end='')
  while command := input():
    if command == '' or command[0].lower() == 'q':
      exit()
    command = command.replace(' ', '=').replace('-', '=')
    cmd, value = command.split('=')
    match cmd[0].lower():
      case 'i':
        institution = value.upper().strip('01') + '01'
      case 'd':
        discipline = value.upper()
      case 'c':
        catalog_number = value
      case q:
        break

    if institution and discipline and catalog_number:
      print(institution, discipline, catalog_number)
      try:
        for course, value in courses_cache((institution, discipline, catalog_number)).items():
          print(f'{course:10}: {value.title}')
      except ValueError as ve:
        print(ve)
      print('\n? ', end='')
