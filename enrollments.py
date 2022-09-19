#! /usr/local/bin/python3

import psycopg
import sys

from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:

    cursor.execute("""
      select institution, plan, enrollment
        from cuny_acad_plan_enrollments
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
          return (f'{cursor.rowcount} requirement blocks match {institution} {requirement_id}')
        row = cursor.fetchone()
        # check block type to see whether block value is a plan or a subplan
        plan = subplan = None
        if row.block_type == 'MAJOR':
          plan = row.block_value
        elif row.block_type == 'CONC' or row.block_type == 'MINOR':
          subplan = row.block_value
        else:
          return (None, f'{institution} {arg}: {row.block_type} is not MAJOR, MINOR, or CONC')

  else:
    # Interpret arg as a plan or subplan code
    arg = arg.upper()

  # See if there is info
  if (institution, arg) in subplans.keys():
    return subplans[(institution, arg)], 'subplan'
  elif (institution, arg) in plans.keys():
    return plans[(institution, arg)], 'plan'
  else:
    return (None, f'No plan or subplan info for {institution} {arg}')


# Interactive mode
if __name__ == '__main__':
  # Args on command line?
  if len(sys.argv) > 2:
    enrollment, text = enrollments(sys.argv[1], sys.argv[2])
    if enrollment:
      s = '' if enrollment == 1 else 's'
      exit(f'{enrollment:,} {text} student{s}')
    else:
      exit(text)
  # No command line options; interactive mode
  while True:
    print('? ', end='')
    line = input()
    if line.strip() in ['', 'q']:
      exit()
    institution, arg = line.split()
    enrollment, text = enrollments(institution, arg)
    if enrollment:
      s = '' if enrollment == 1 else 's'
      print(f'{enrollment:,} {text} student{s}')
    else:
      print(text)
