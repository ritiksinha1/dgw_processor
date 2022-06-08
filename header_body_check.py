#! /usr/local/bin/python3
""" What are the overlap patterns between course limits in the header and course requirements in the
    body?
    Mapper generates dicts of expanded course lists, keyed by course_id, for maxcredit/maxclass in
    header blocks in an "analysis file." Here, we look up all those courses in body rules to see
    whether there is redundancy ... or not.
"""

import csv
import json
import os
import sys
import psycopg

from collections import defaultdict
from psycopg.rows import namedtuple_row
from time import time


# format_num_class_credit()
# -------------------------------------------------------------------------------------------------
def format_num_class_credit(cc_dict: dict):
  """
  """
  assert isinstance(cc_dict, dict), f'{type(cc_dict)} is not dict'

  try:
    num_classes_str = ''
    if cc_dict['min_classes'] is not None:
      min_classes = int(cc_dict['min_classes'])
      max_classes = int(cc_dict['max_classes'])
      if min_classes == max_classes:
        if min_classes != 0:
          suffix = '' if min_classes == 1 else 'es'
          num_classes_str = f'{min_classes} class{suffix}'
      else:
        num_classes_str = f'Between {min_classes} and {max_classes} classes'

    num_credits_str = ''
    if cc_dict['min_credits'] is not None:
      min_credits = float(cc_dict['min_credits'])
      max_credits = float(cc_dict['max_credits'])
      if abs(max_credits - min_credits) < 0.01:
        if min_credits > 0.0:
          suffix = '' if abs(min_credits - 1.0) < 0.01 else 's'
          num_credits_str = f'{min_credits:.2f} credit{suffix}'
      else:
        num_credits_str = f'Between {min_credits:0.2f} and {max_credits:.2f} credits'

    if num_classes_str and num_credits_str:
      conjunction_str = ' ' + cc_dict['conjunction'].lower() + ' '
      num_credits_str = num_credits_str.lower()
    else:
      conjunction_str = ''
    return f'{num_classes_str}{conjunction_str}{num_credits_str}'

  except (KeyError, ValueError) as err:
    print(f'Ignore class/credit dict: {cc_dict}', file=sys.stderr)
    return None


def format_requirement(requirement_dict: dict) -> (str, set):
  """ Given a class_credit dict, generate a string telling how many classes and/or credits are
      required. In addition, create a set of the courses in the expanded scribed courses list minus
      excluded courses. Ignore with clauses.
  """
  number_str = format_num_class_credit(requirement_dict)
  course_dict = requirement_dict['course_list']

  scribed_courses = set()
  for area in course_dict['scribed_courses']:
    for course in area:
      with_clause = f' With ({course[2]})' if course[2] else ''  # omit
      scribed_courses.add(f'{course[0]} {course[1]}')

  excluded_courses = set()
  for course in course_dict['except_courses']:
    with_clause = f' With ({course[2]})' if course[2] else ''  # omit
    excluded_courses.add(f'{course[0]} {course[1]}')

  course_list = scribed_courses - excluded_courses
  return (number_str, course_list)


if __name__ == '__main__':
  # If an institution and requirement_id are given on the command line, process just that one
  # block and print course set details to the report file.
  if len(sys.argv) == 3:
    institution = sys.argv[1][0:3].upper() + '01'
    requirement_id = int(sys.argv[2].upper().strip('RA'))
    requirement_id = f'RA{requirement_id:06}'
    debug_block = (institution, requirement_id)
    print(f'Examining {debug_block}')
  else:
    debug_block = None

  start_time = time()
  with_clause_dict = defaultdict(int)
  if debug_block:
    report_file = open('./header_body_debug.txt', 'w')
    print('Count, Program, Limit, Type, Courses, Overlap, Alternatives', file=report_file)
  else:
    report_file = open('./Tech_Reports/header_body_report.txt', 'w')
    print('Count, Limit, Type, Courses, Overlap, Alternatives', file=report_file)

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute("""
      select lpad(course_id::text, 6, '0')||':'||offer_nbr as course, equivalence_group
      from cuny_courses
      where equivalence_group is not null
      """)
      equivalence_groups = {row.course: row.equivalence_group for row in cursor}
      cursor.execute("""
      select lpad(course_id::text, 6, '0')||':'||offer_nbr as courseid_str,
             discipline||' '||catalog_number as course_name
      from cuny_courses
      """)
      course_names = {row.courseid_str: row.course_name for row in cursor}
  with psycopg.connect('dbname=course_mappings') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      with open('./analysis.txt') as infile:
        blocks_set = set()
        for line in infile.readlines():
          ident, course_dict = line.split(';')
          institution, requirement_id, block_type, limit_type, number = ident.split()

          # Filter out repeated or non-debugging blocks
          this_block = (institution, requirement_id)
          if this_block in blocks_set or (debug_block and debug_block != this_block):
            continue

          blocks_set.add(this_block)
          course_dict = eval(course_dict)

          xlist_set = set([course_id for course_id, offer_nbr in course_dict.keys()])
          if len(xlist_set) == 1:
            print(f'{institution} {requirement_id} {block_type:6} {number:3} {limit_type:9} '
                  f'CROSS-LIST', file=report_file)
            continue
          try:
            equiv_set = set([equivalence_groups[f'{course_id:06}:{offer_nbr}']
                             for course_id, offer_nbr in course_dict.keys()])
            if len(equiv_set) == 1:
              print(f'{institution} {requirement_id} {block_type:6} {number:3} {limit_type:9} '
                    f'EQUIV-SET', file=report_file)
              continue
          except KeyError:
            pass

          # Look up all requirements in this block that include these courses; ignore with-clauses
          limited_set_keys = set([f'{k[0]:06}:{k[1]}' for k in course_dict.keys()])
          for course_tuple in course_dict.values():
            with_clause = 'None' if course_tuple[1] is None else course_tuple[1]
            with_clause_dict[with_clause] += 1

          if len(limited_set_keys) == 0:
            print(f'{institution} {requirement_id} {block_type:6} {number:3} {limit_type:9} '
                  f'NO-MATCH', file=report_file)
            continue

          limited_courses = [course_names[course_key] for course_key in limited_set_keys]
          limited_set = set(limited_courses)
          num_limited = len(limited_set)

          # Get list of required courses, again ignoring with-clauses
          limited_courses_phrase = ','.join([f"'{course}'" for course in limited_set_keys])
          cursor.execute(f"""
          select r.requirement_key, string_agg(m.course_id, ' ') as courses,
                 r.context, r.program_name
            from requirements r, course_mappings m
           where r.institution = %s
             and r.requirement_id = %s
             and m.course_id in ({limited_courses_phrase})
             and r.requirement_key = m.requirement_key
          group by r.requirement_key, r.context, r.program_name
          """, (institution, requirement_id))
          for row in cursor:
            context_dict = json.loads(row.context)
            requirement_dict = context_dict['requirement']
            requirement_name = requirement_dict['label']

            requirement_str, requirement_set = format_requirement(requirement_dict)
            num_requirement = len(requirement_set)

            overlap_set = limited_set & requirement_set
            num_overlap = len(overlap_set)

            if debug_block:
              limited_courses_str = ', '.join(sorted(limited_set))
              requirement_courses_str = ', '.join(sorted(requirement_set))
              overlap_courses_str = ', '.join(sorted(overlap_set))
              print(f'{institution} {requirement_id} {block_type} {number} {limit_type[3:]}'
                    f'\n  limit {limited_courses_str}'
                    f'\n  reqmt {requirement_courses_str}'
                    f'\n  inter {overlap_courses_str}',
                    file=report_file)
            else:
              print(f'{institution} {requirement_id} {block_type:8}, {number:5}, '
                    f'{limit_type[3:]:6}, '
                    f'{num_limited:3}, {num_overlap:3}, {num_requirement:3}', file=report_file)

  for item in sorted(with_clause_dict.items(), key=lambda i: i[1], reverse=True):
    print(f'{item[1]:10,} {item[0]}')

  num_blocks = len(blocks_set)
  suffix = '' if num_blocks == 1 else 's'
  min, sec = divmod(time() - start_time, 60)

  print(f'{num_blocks:,} block{suffix} {int(min):02}:{round(sec):02}')
