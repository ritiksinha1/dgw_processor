#! /usr/local/bin/python3
""" Extract a scribe block from the db for examination.
    If you know the Requirement ID, give that. Otherwise, give the (block type and) value. Only the
    current block of that type and value will be used
"""

import os
import sys

import argparse
import json
import psycopg

from pathlib import Path
from pprint import pprint
from psycopg.rows import namedtuple_row

if __name__ == '__main__':
  args = ' '.join(sys.argv[1:]).replace(',', ' ').replace('_', ' ').split(' ')
  institution = f'{args[0][0:3].upper()}01'
  requirement_id = int(args[1].strip('RA'))
  requirement_id = f'RA{requirement_id:06}'

  # Look up the block type and value
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute(f'select block_type, block_value, requirement_text, parse_tree'
                     f'  from requirement_blocks'
                     f" where institution = '{institution}'"
                     f"   and requirement_id = '{requirement_id}'")
      if cursor.rowcount != 1:
        exit(f'{cursor.rowcount} blocks for {institution} {requirement_id}')

      row = cursor.fetchone()

  base_name = f'{institution}_{requirement_id}_{row.block_type}_{row.block_value}'.replace('/', '.')

  parse_tree = row.parse_tree

  try:
    header_list = parse_tree['header_list']
    body_list = parse_tree['body_list']
  except KeyError as ke:
    if 'error' in parse_tree.keys():
      error_value = parse_tree['error']
    else:
      error_value = ''
    print(f'{base_name} has not been parsed. {error_value}')
    header_list = body_list = {}

  print(base_name)
  with open(f'./extracts/{base_name}.txt', 'w') as scribe_block:
    print(row.requirement_text, file=scribe_block)

  with open(f'./extracts/{base_name}.json', 'w') as json_file:
    print(json.dumps(parse_tree, indent=2), file=json_file)

  exit()
