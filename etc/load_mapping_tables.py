#! /usr/local/bin/python3
""" Load the three course mapping tables into the course_mapper database. Then you can use
    getrequirments.py to see what requirements a course satisfies, for example.
"""

import csv
import os
import sys
import psycopg

from collections import namedtuple
from pathlib import Path
from psycopg.rows import namedtuple_row
from time import time


def _count_generator(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


if __name__ == '__main__':
  session_start = time()
  csv.field_size_limit(sys.maxsize)
  with psycopg.connect('dbname=course_mappings') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      tables = dict()
      csv_files = Path('/Users/vickery/Projects/dgw_processor').glob('c*v')
      for file in csv_files:

        with open(file, 'rb') as fp:
          c_generator = _count_generator(fp.raw.read)
          num_lines = sum(buffer.count(b'\n') for buffer in c_generator)
        table_name = file.name.replace('course_mapper.', '').replace('.csv', '')
        print(f'\n{table_name}: {num_lines:,} lines')
        tables[table_name] = num_lines - 1
        nl = num_lines / 100.0
        with open(file) as csv_file:
          reader = csv.reader(csv_file)
          for line in reader:
            print(f'\r{reader.line_num:,}/{num_lines:,} {round(reader.line_num/nl)}%', end='')
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
  csi = '\033['
  bold = f'{csi}1m'
  norm = f'{csi}0m'
  print(f'\nTotal {int(hr):02}:{int(min):02}:{round(sec):02}\n\n'
        f'Database: {bold}course_mappings{norm}')
  for key, value in tables.items():
    print(f'{value:10,} {key}')