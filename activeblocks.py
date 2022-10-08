#! /usr/local/bin/python3
"""
"""

import psycopg
import sys

from psycopg.rows import namedtuple_row

active_blocks = dict()
active_plans = dict()
active_subplans = dict()

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""
    select institution, requirement_id, block_type, block_value,
           min(active_term) as min_term,
           max(active_term) as max_term,
           count(active_term) as num_terms,
           sum(total_students) as enrollment
      from ra_counts
    group by institution, requirement_id, block_type, block_value
    order by institution, requirement_id, block_type, block_value
    ;
    """)
    for row in cursor:
      active_blocks[(row.institution, row.requirement_id)] = row
      if row.block_type in ['MAJOR', 'MINOR']:
        active_plans[(row.institution, row.block_value)] = row
      if row. block_type == 'CONC':
        active_subplans[(row.institution, row.block_value)] = row
