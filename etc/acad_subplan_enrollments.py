#! /usr/local/bin/python3

import csv
import psycopg
import sys

from collections import namedtuple
from pathlib import Path
from psycopg.rows import namedtuple_row

latest = None
csv_files = Path('.').glob('ACAD_SUBPLAN_ENRL*')
for csv_file in csv_files:
  if latest is None or latest.st_mtime < csv_file.st_mtime:
    latest = csv_file

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""
    drop table if exists acad_subplan_enrollments;
    create table acad_subplan_enrollments (
      institution text,
      plan text,
      subplan text,
      enrollment integer,
      primary key (institution, plan, subplan))
    """)
    with open(latest) as csv_file:
      reader = csv.reader(csv_file)
      for line in reader:
        if reader.line_num == 1:
          cols = [col.lower().replace(' ', '_').replace('-', '') for col in line]
          Row = namedtuple('Row', cols)
        else:
          row = Row._make(line)
          cursor.execute(f"""
          insert into acad_subplan_enrollments values(%s, %s, %s, %s)
          """, [row.institution, row.acad_plan, row.subplan, row.enrollment])
