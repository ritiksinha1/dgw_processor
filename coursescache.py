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
CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr title career')


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
          select institution, course_id, offer_nbr, discipline, catalog_number, title, career
            from cuny_courses
           where institution = %s
             and course_status = 'A'
             and designation not in ('MNL', 'MLA')
             and attributes !~* 'BKCR'
           order by discipline, numeric_part(catalog_number)
        """, (institution, ))
        for row in cursor:
          info = CourseTuple._make([row.course_id, row.offer_nbr, row.title, row.career])
          _courses_cache[row.institution][row.discipline][row.catalog_number] = info

  # Simple Case
  if not ('@' in discipline or '@' in catalog_number):
    try:
      return ({f'{discipline} {catalog_number}':
              _courses_cache[institution][discipline][catalog_number]})
    except KeyError:
      return []

  # Generate list of matching disciplines
  if '@' in discipline:
    regex = f'^{discipline}$'.replace('@', '.+')
    disciplines = [key for key in _courses_cache[institution].keys() if re.match(regex, key)]
  else:
    disciplines = [discipline]

  # For each discipline, look up all the courses with matching catalog numbers.
  regex = f'^{catalog_number}$'.replace('@', '.+')
  return_dict = {}
  for discipline in disciplines:
    for catalog_number in _courses_cache[institution][discipline].keys():
      if re.match(regex, catalog_number):
        return_dict[f'{discipline} {catalog_number}'] = (_courses_cache[institution][discipline]
                                                         [catalog_number])
  return return_dict


# main()
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  print(courses_cache(('QNS01', 'CSCI', '101')))
  for course, info in courses_cache(('QNS01', 'C@', '1@1')).items():
    print(f'{course:10}', info.title)
