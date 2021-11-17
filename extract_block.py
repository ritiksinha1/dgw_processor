#! /usr/local/bin/python3
""" Extract a scribe block from the db for examination.
    If you know the Requirement ID, give that. Otherwise, give the (block type and) value. Only the
    current block of that type and value will be used
"""

import os
import sys

import argparse
import json

from pathlib import Path
from pprint import pprint

from pgconnection import PgConnection

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institution', default='QNS01')
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-t', '--block_type', default='MAJOR')
  parser.add_argument('-v', '--block_value')

  # Parse args
  args = parser.parse_args()

  institution = args.institution.strip('10').upper() + '01'

  if args.requirement_id:
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')

    requirement_id = f'RA{int(requirement_id):06}'
    # Look up the block type and value
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f'select block_type, block_value, requirement_text, requirement_html,'
                   f'       parse_tree'
                   f'  from requirement_blocks'
                   f" where institution = '{institution}'"
                   f"   and requirement_id = '{requirement_id}'")
    if cursor.rowcount != 1:
      exit(f'{cursor.rowcount} blocks for {institution} {requirement_id}')
    row = cursor.fetchone()
    conn.close()

  elif args.block_value:
    block_type = args.block_type.upper()
    block_value = args.block_value.upper()
    # Look up the block type and value
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f'select requirement_id, block_type, block_value,'
                   f'       requirement_text, requirement_html,'
                   f'       parse_tree'
                   f'  from requirement_blocks'
                   f" where institution = '{institution}'"
                   f"   and block_type = '{block_type}'"
                   f"   and block_value = '{block_value}'"
                   f"   and period_stop = '99999999'")
    if cursor.rowcount != 1:
      exit(f'{cursor.rowcount} current blocks for {institution} {block_type} {block_value}')
    row = cursor.fetchone()
    requirement_id = row.requirement_id
    conn.close()
  else:
    exit('Missing requirement ID or block value')

  base_name = f'{institution}_{requirement_id}_{row.block_type}_{row.block_value}'

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
  with open(f'./extracts/{base_name}.html', 'w') as html_file:
    print(row.requirement_html, file=html_file)

  with open(f'./extracts/{base_name}.scribe', 'w') as scribe_block:
    print(row.requirement_text, file=scribe_block)

  with open(f'./extracts/{base_name}.json', 'w') as json_file:
    print(json.dumps(parse_tree), file=json_file)

  with open(f'./extracts/{base_name}.py', 'w') as parsed:
    print('HEADER = (', file=parsed)
    pprint(header_list, stream=parsed)
    print(')\nBODY = (', file=parsed)
    pprint(body_list, stream=parsed)
    print(')', file=parsed)

exit()
