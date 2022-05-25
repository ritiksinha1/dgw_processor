#! /usr/local/bin/python3
""" Load the three course mapping tables into the course_mapper database
"""

import csv
import os
import sys
import psycopg

from collections import namedtuple
from pathlib import Path
from psycopg.rows import namedtuple_row
from time import time

if __name__ == '__main__':
  session_start = time()
  with psycopg.connect('dbname=course_mappings') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:

      csv_files = Path('.').glob('c*v')
      for file in csv_files:
        table_name = file.name.replace('course_mapper.', '').replace('.csv', '')

        print(table_name)
        with open(file) as csv_file:
          reader = csv.reader(csv_file)
          for line in reader:
            if reader.line_num == 1:
              Row = namedtuple('Row', [col.lower().replace(' ', '_').replace('with', 'with_exp')
                               for col in line])
              field_names = Row._fields
              fields = ',\n'.join([f'{field_name} text' for field_name in field_names])
              cursor.execute(f"""
              drop table if exists {table_name};
              create table {table_name} ({fields});
              """)
            else:
              row = Row._make(line)
              row_dict = row._asdict()
              values = [value.replace('\'', '’') for value in row_dict.values()]
              values = ','.join([f"'{value}'" for value in values])
              cursor.execute(f'insert into {table_name} values({values})')
  min, sec = divmod(time() - session_start, 60)
  hr, min = divmod(min, 60)
  print(f'Total {int(hr):02}:{int(min):02}:{round(sec):02}')
