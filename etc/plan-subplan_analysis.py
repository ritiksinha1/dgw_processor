#! /usr/local/bin/python3
""" Testing how plan and subplan enrollments match ra_counts.
"""

import csv
import psycopg
import sys

from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:

    # Do requirement blocks match plans?
    with open('./ra_to_plan.csv', 'w') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(['Institution', 'Requirement_id', 'Block Type', 'Block Value\n(Plan)',
                      'Students', 'Enrollment'])
      cursor.execute("""
      select dap.institution, dap.requirement_id, dap.block_type, dap.block_value,
             sum(ra.total_students) as total_students, e.enrollment
      from requirement_blocks dap
             left join ra_counts ra on dap.institution = ra.institution
                                   and dap.requirement_id = ra.requirement_id,
           cuny_plan_enrollments e
      where dap.period_stop ~* '^9'
        and dap.institution = e.institution
        and dap.block_value = e.plan
      group by dap.institution, dap.requirement_id, dap.block_type, dap.block_value, e.enrollment
      order by dap.institution, dap.block_type, dap.block_value
      """)
      for row in cursor:
        writer.writerow([row.institution, row.requirement_id, row.block_type, row.block_value,
                         row.total_students, row.enrollment])

    # Do plans match requirement blocks?
    with open('./plan_to_ra.csv', 'w') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(['Institution', 'Plan\n(Block Value)', 'Students', 'Enrollment', 'Requirement_id',
                      'Block Type'])
      cursor.execute("""
      select plan.institution, plan.plan,
             sum(ra.total_students) as total_students, e.enrollment,
             dap.requirement_id, dap.block_type
      from   cuny_subplans plan
             left join requirement_blocks dap
                    on plan.institution = dap.institution
                   and plan.plan = dap.block_value
             left join ra_counts ra on dap.institution = ra.institution
                                   and dap.requirement_id = ra.requirement_id,
           cuny_plan_enrollments e
      where dap.period_stop ~* '^9'
        and dap.institution = e.institution
        and dap.block_value = e.plan
      group by plan.institution, plan.plan, dap.requirement_id, dap.block_type, dap.block_value,
               e.enrollment
      order by plan.institution, plan.plan, dap.block_type, dap.block_value
      """)
      for row in cursor:
        writer.writerow([v for v in row])

    # Do requirement blocks match subplans?
    with open('./ra_to_subplan.csv', 'w') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(['Institution', 'Requirement_id', 'Block Type', 'Block Value\n(Subplan)',
                      'Students', 'Enrollment'])
      cursor.execute("""
      select dap.institution, dap.requirement_id, dap.block_type, dap.block_value,
             sum(ra.total_students) as total_students, e.enrollment
      from requirement_blocks dap
             left join ra_counts ra on dap.institution = ra.institution
                                   and dap.requirement_id = ra.requirement_id,
           cuny_subplan_enrollments e
      where dap.period_stop ~* '^9'
        and dap.institution = e.institution
        and dap.block_value = e.subplan
      group by dap.institution, dap.requirement_id, dap.block_type, dap.block_value, e.enrollment
      order by dap.institution, dap.block_type, dap.block_value
      """)
      for row in cursor:
        writer.writerow([row.institution, row.requirement_id, row.block_type, row.block_value,
                         row.total_students, row.enrollment])

    # Do subplans match requirement blocks?
    with open('./subplan_to_ra.csv', 'w') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(['Institution', 'Subplan\n(Block Value)', 'Students', 'Enrollment',
                      'Requirement_id', 'Block Type'])
      cursor.execute("""
      select plan.institution, plan.subplan,
             sum(ra.total_students) as total_students, e.enrollment,
             dap.requirement_id, dap.block_type
      from   cuny_subplans plan
             left join requirement_blocks dap
                    on plan.institution = dap.institution
                   and plan.subplan = dap.block_value
             left join ra_counts ra on dap.institution = ra.institution
                                   and dap.requirement_id = ra.requirement_id,
           cuny_subplan_enrollments e
      where dap.period_stop ~* '^9'
        and dap.institution = e.institution
        and dap.block_value = e.subplan
      group by plan.institution, plan.subplan, dap.requirement_id, dap.block_type, dap.block_value,
               e.enrollment
      order by plan.institution, plan.subplan, dap.block_type, dap.block_value
      """)
      for row in cursor:
        writer.writerow([v for v in row])
