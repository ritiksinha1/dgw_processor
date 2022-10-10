#! /usr/local/bin/python3
""" Scribe blocks can be "current," but the underlying program or subprogram might no longer be
    "active" (accepting students).

    A "current" dap_req_block ("Scribe Block" or "requirement_block") is one that has a period_stop
    value that begins with '9'. However, programs can become inactive (no longer offered), without
    anyone updating the period_stop field for the block. The CUNYfirst acad_plan and acad_subplan
    tables tell what programs/concentrations are "active," but this doesn't necessarily mean the
    program or concentration is currently being offered. There is a pair of CUNYfirst tables that
    give the current enrollment for each plan/subplan, but we have seen instances where
    known-inactive programs show up with non-zero enrollments.

    OAREDA supplies a list of dap_req_blocks that are "truly active" in a file called
    dgw_ir_active_requirements.csv, which is updated daily. A script called mk_ra_counts builds a
    local table called ra_counts from the OAREDA CSV file. This code joins information from
    ra_counts with information from the OAREDA dap_req_block table (specifically, an augemented
    local copy called requirement_blocks) to produce dicts for access that information by block,
    plan, and subplan.
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
    select institution, requirement_id, block_type, block_value, block_title, major1,
           min(active_term) as min_term,
           max(active_term) as max_term,
           count(active_term) as num_terms,
           sum(total_students) as enrollment
      from ra_counts
    group by institution, requirement_id, block_type, block_value, block_title, major1
    order by institution, requirement_id, block_type, block_value
    ;
    """)
    for row in cursor:
      active_blocks[(row.institution, row.requirement_id)] = row
      if row.block_type in ['MAJOR', 'MINOR']:
        active_plans[(row.institution, row.block_value)] = row
      if row. block_type == 'CONC':
        active_subplans[(row.institution, row.block_value)] = row
