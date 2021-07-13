#! /usr/local/bin/python3
""" Extract a scribe block from the db for examination.
"""

import os
import sys

import argparse
from pathlib import Path

from pgconnection import PgConnection

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-ra', '--requirement_id')

  # Parse args
  args = parser.parse_args()
  if args.requirement_id:

    institution = args.institutions[0].strip('10').upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')
    requirement_id = f'RA{int(requirement_id):06}'
    # Look up the block type and value
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f'select block_type, block_value, requirement_text, requirement_html'
                   f'  from requirement_blocks'
                   f" where institution = '{institution}'"
                   f"   and requirement_id = '{requirement_id}'")
    assert cursor.rowcount == 1, (f'Found {cursor.rowcount} block_type/block_value pairs '
                                  f'for {institution} {requirement_id}')
    block_type, block_value, requirement_text, requirement_html = cursor.fetchone()
    conn.close()

    base_name = f'{institution}_{requirement_id}_{block_type}_{block_value}'
    print(base_name)
    with open(f'./extracts/{base_name}.html', 'w') as html_file:
      print(requirement_html, file=html_file)
    with open(f'./extracts/{base_name}.scribe', 'w') as scribe_block:
      print(requirement_text, file=scribe_block)
exit()
