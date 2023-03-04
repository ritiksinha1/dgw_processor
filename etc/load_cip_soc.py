#! /usr/local/bin/python3
"""Build cip_soc table."""

import csv
import psycopg
import sys

from collections import namedtuple
from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    with open('queries/CIP2020_SOC2018_Crosswalk.csv') as csv_file:
      reader = csv.reader(csv_file)
      for line in reader:
        if reader.line_num == 1:
          cols = [col.lower().replace(' ', '_').replace('\ufeff', '') for col in line]
          Row = namedtuple('Row', cols)
          table_def = ','.join([f'{col} text' for col in cols])
          cursor.execute(f"""
            drop table if exists cip_soc;
            create table cip_soc({table_def})
            """)
        else:
          cols = [col.replace("'", "’") for col in line]
          row_values = ','.join([f"'{col}'" for col in cols])
          cursor.execute(f"""
          insert into cip_soc values({row_values})
          """)
