#! /usr/local/bin/python3

import psycopg
import sys

from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:

    cursor.execute("""
      select t.institution, t.plan, coalesce(e.enrollment, 0) as enrollment
        from cuny_acad_plan_tbl t left join cuny_acad_plan_enrollments e
          on t.institution = e.institution
         and t.plan = e.plan
      """)
    plans = {(row.institution, row.plan): row.enrollment for row in cursor.fetchall()}

    # In case of multiple subplans with the same name at an institution, later one(s) will overwrite
    # earlier ones. But this is just used to estimate number of students impacted by missing
    # requirement blocks, so we accept the inaccuracy for now.
    cursor.execute("""
      select institution, string_agg(plan, ',') as plans, subplan, sum(enrollment) as enrollments
        from cuny_acad_subplan_enrollments
       group by institution, subplan
      """)
    subplans = {(row.institution, row.subplan): int(row.enrollments) for row in cursor.fetchall()}


def enrollments(institution: str, arg: str) -> str:
  """ Returns enrollment information for the arg, which may be a requirement_id, plan, or subplan.
      Return value is a (count, text) tuple, where the text is either "plan" or "subplan" or, if
      there is no matching enrollment info, an error message. Count is None for errors.
  """
  institution = institution.upper().strip('01') + '01'
  block_type = block_value = plan = subplan = None

  # Decide what sort of argument was provided
  block_number = arg.upper().strip('RA')
  if block_number.isnumeric():

    # Interpret arg as a requirement_id
    arg = f'RA{block_number:>06}'
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("""
        select institution, requirement_id, block_type, block_value, title, period_stop
          from requirement_blocks
         where institution = %s
           and requirement_id = %s
        """, (institution, arg))
        if cursor.rowcount != 1:
          num_err = 'No' if cursor.rowcount == 0 else f'{cursor.rowcount:,}'
          return (None, f'{institution[0:3]} {arg}: {num_err} matching requirement blocks')
        row = cursor.fetchone()
        # check block type to see whether block value is a plan or a subplan
        block_type = row.block_type
        block_value = row.block_value
        if block_type == 'MAJOR':
          plan = block_value
        elif block_type == 'CONC' or row.block_type == 'MINOR':
          subplan = block_value
        else:
          return (None, f'{institution[0:3]} {arg} ({block_type.title()} {block_value}): No data')

  else:
    # Interpret arg as a plan or subplan code
    arg = arg.upper()

  # See if there is info
  if (institution, arg) in subplans.keys():
    return subplans[(institution, arg)], 'subplan'
  elif (institution, arg) in plans.keys():
    num_students = int(plans[(institution, arg)])
    num_students = 'Zero' if num_students == 0 else f'{num_students:,}'
    return num_students, 'plan'
  else:
    details = f' ({block_type.title()} {block_value})' if block_type else ''

    return (None, f'{institution[0:3]} {arg}{details}: No enrollment')


# Interactive mode
if __name__ == '__main__':
  # Args on command line?
  if len(sys.argv) > 2:
    enrollment, text = enrollments(sys.argv[1], sys.argv[2])
    if enrollment:
      s = '' if enrollment == 1 else 's'
      print(f'{enrollment} {text} student{s}')
    else:
      print(text)
    exit()
  # No command line options; interactive mode
  while True:
    print('? ', end='')
    line = input()
    if line.strip() in ['', 'q']:
      exit()
    institution, arg = line.split()
    enrollment, text = enrollments(institution, arg)
    if enrollment:
      s = '' if enrollment == '1' else 's'
      print(f'{enrollment} {text} student{s}')
    else:
      print(text)
