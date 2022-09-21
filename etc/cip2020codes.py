#! /usr/local/bin/python3
""" Load the CIP table from https://nces.ed.gov/ipeds/ into local table, renaming columns.

    Note: as a separate step, I edited the .csv file downloaded from ipeds to remove all '='
    characters from the first two columns before running this script.

    Also, this script replaces embedded single quotes ("'") with right curly single quotes for db
    integrity. (“Women’s”)
"""

import csv
import psycopg

from collections import namedtuple
from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    # I like these column names better than the ones in the CSV file.
    cursor.execute("""
    drop table if exists cip2020codes;
    create table cip2020codes
      (cip_family       text,
       cip_code         text,
       action           text,
       text_change      text,
       cip_title        text,
       cip_definition   text,
       cross_references text,
       examples         text)
    """)
    with open('queries/CIPCode2020.csv') as csv_file:
      reader = csv.reader(csv_file)
      for line in reader:
        if reader.line_num == 1:
          Row = namedtuple('ROW', ['cip_family', 'cip_code', 'action', 'text_change', 'cip_title',
                           'cip_definition', 'cross_references', 'examples'])
        else:
          row = Row._make(line)
          values_str = ','.join("'" + col.replace("'", "’") + "'" for col in row)
          cursor.execute(f"""
          insert into cip2020codes values({values_str})
          """)
