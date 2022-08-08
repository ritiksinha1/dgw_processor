#! /usr/local/bin/python3
""" Gather the information needed for selecting plans that have scribe blocks and non-empty
    enrollmwnts. Makes a spreadsheet for sanity checking.
"""
import csv
import datetime
import psycopg
import sys

from psycopg.rows import namedtuple_row

grace_period = datetime.date.today() - datetime.timedelta(weeks=52)

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""copy(
    select p.institution, p.plan, p.plan_type, p.description, p.effective_date,
           e.enrollment,
           r.requirement_id, r.block_type, r.title
      from cuny_acad_plan_tbl p
           left join cuny_plan_enrollments e
                  on p.institution = e.institution
                 and p.plan = e.plan
                     left join requirement_blocks r
                            on p.institution = r.institution
                           and p.plan = r.block_value
                           and r.period_stop ~* '^9'
     where p.plan !~* '^mhc'
     order by p.institution, p.plan)
     to '/Users/vickery/Projects/dgw_processor/etc/out/plans.csv' csv header
    """)
    # for row in cursor:
    #   if row.enrollment is None and row.effective_date > grace_period:
    #     print(row.institution, row.plan, row.description, row.effective_date, row.enrollment)
