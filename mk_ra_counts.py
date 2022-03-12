#! /usr/local/bin/python3

import csv
import os
import psycopg
import sys

from collections import namedtuple
from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""
    drop table if exists ra_counts;

    create table ra_counts (
    institution text,
    requirement_id text,
    active_term integer,
    total_students integer,
    foreign key (institution, requirement_id) references requirement_blocks,
    primary key (institution, requirement_id, active_term));
    """)
    cursor.execute("""
    select institution, requirement_id
      from requirement_blocks
     where period_stop ~* '^9'
     """)
    active_blocks = [(row.institution, row.requirement_id) for row in cursor]
    with open('downloads/All CUNY RAs with Counts.csv', newline='') as csv_file:
      reader = csv.reader(csv_file)
      for line in reader:
        if reader.line_num == 1:
          Row = namedtuple('Row', ' '.join(col.lower().replace(' ', '_') for col in line))
        else:
          row = Row._make(line)
          if (row.institution, row.dap_req_id) in active_blocks:
            cursor.execute("""
            insert into ra_counts values(%s, %s, %s, %s)
            """, [row.institution,
                  row.dap_req_id,
                  int(row.dap_active_term.strip('U')),
                  int(row.totalstudents)])
