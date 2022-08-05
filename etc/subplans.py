#! /usr/local/bin/python3
""" Develop defininitive plan-subplan relations table.
    Explore the relationship between (active) dgw block types and CUNYfirst subplan table.
"""

import csv
import psycopg
import sys

from collections import defaultdict, namedtuple
from psycopg.rows import namedtuple_row

if __name__ == '__main__':

  PlanKey = namedtuple('PlanKey', 'institution, plan')
  Subplan = namedtuple('Subplan', 'subplan, subplan_title, subplan_type')
  plan_names = defaultdict(str)
  subplans = defaultdict(list)

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      # Cache CUNYfirst plan-subplan info
      cursor.execute("""
      select
             s.institution,
             s.plan,
             p.description as plan_title,
             s.subplan,
             s.description as subplan_title,
             s.subplan_type
      from cuny_programs p, cuny_subplans s
      where p.program_status = 'A'
        and p.career ~* '^U'
        and s.status = 'A'
        and p.institution = s.institution
        and p.academic_plan = s.plan
      order by institution, plan, subplan
      """)
      for row in cursor:
        plan_key = PlanKey._make((row.institution, row.plan))
        plan_names[plan_key] = row.plan_title
        subplans[plan_key].append(Subplan._make([row.subplan, row.subplan_title, row.subplan_type]))

      # Report how many subplans each plan has
      with open('./subplan_report.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Institution', 'Plan', 'Plan Name', 'Number of Subplans'])
        for plan_key in plan_names.keys():
          writer.writerow([plan_key.institution[0:3], plan_key.plan, plan_names[plan_key],
                          len(subplans[plan_key])])

      # DGW Metadata
      cursor.execute(r"""
      select institution, requirement_id, block_type, block_value, title as block_title, parse_tree
        from requirement_blocks
       where period_stop ~* '^9'
         and block_type != 'DEGREE'
         and block_value ~* '\-'
      """)
      dgw_plans = defaultdict(dict)
      dgw_subplans = defaultdict(list)
      for row in cursor:
        # Proceed only if the discipline can be extracted
        try:
          discipline, award = row.block_value.split('-')
        except ValueError:
          print('Ignoring',
                row.institution,
                row.requirement_id,
                row.block_type,
                row.block_value,
                row.block_title)
          continue

        if row.block_type in ('MAJOR', 'MINOR'):
          dgw_plan_key = PlanKey._make([row.institution, discipline])
          dgw_plans[dgw_plan_key] = {'plan_type': row.block_type.lower(),
                                     'award': award,
                                     'plan_name': row.block_title}
          dgw_subplans[dgw_plan_key] = []
        else:
          dgw_subplans[dgw_plan_key].append(Subplan._make([row.block_value,
                                                          row.block_title,
                                                          row.block_type]))
      with open('./dgw_subplan_report.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Institution',
                         'Plan',
                         'Plan Name',
                         'Number of Subplans',
                         'Plan Type'])
        for k, v in dgw_plans.items():
          writer.writerow([k.institution[0:3],
                           f"{k.plan}-{v['award']}", v['plan_name'],
                           len(dgw_subplans[k]),
                           v['plan_type'],
                           ])
