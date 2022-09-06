#! /usr/local/bin/python3
""" List top-level keys in the header and body lists of a parse tree.
    Used to help verify the mapper's coverage.
"""

import psycopg
import sys

from psycopg.rows import dict_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=dict_row) as cursor:
    cursor.execute("""
    select institution, requirement_id, block_type, block_value, parse_tree
      from requirement_blocks
      where parse_tree != '{}'
    """)
    for row in cursor:
      parse_tree_dict = row['parse_tree']
      try:
        for header_item in parse_tree_dict['header_list']:
          # if 'proxy_advice' in header_item.keys():
          #   print(row['institution'], row['requirement_id'], row['block_type'], row['block_value'],
          #         file=sys.stderr)
          print('Header', list(header_item.keys()))
        for body_item in parse_tree_dict['body_list']:
          print('Body', list(body_item.keys()))
      except KeyError:
        pass
