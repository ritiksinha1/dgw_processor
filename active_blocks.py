#! /usr/local/bin/python3
"""
"""

import psycopg
import sys

from psycopg.rows import namedtuple_row

active_blocks = dict()

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""
    select institution, requirement_id,
           min(active_term) as min_term,
           max(active_term) as max_term,
           count(active_term) as num_terms,
           sum(total_students) as enrollment
      from ra_counts
    -- where institution = 'LEH01' and requirement_id in ('RA001829', 'RA002612', 'RA002360')
    group by institution, requirement_id
    order by institution, requirement_id
    ;
    """)
    for row in cursor:
      active_blocks[(row.institution, row.requirement_id)] = row
