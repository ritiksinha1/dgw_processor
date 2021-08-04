#! /usr/local/bin/python3
""" Add a requirement block to the quarantine list.
    Get the institution and requirement_id from the TEST_DATA environment variable.
    Get the reason from stdin.
"""

import os
import sys
import csv

from collections import namedtuple

Row = namedtuple('Row', 'institution requirement_id block_type reason can_ellucian')

TEST_DATA = os.getenv('TEST_DATA')
if TEST_DATA is None:
  sys.exit('TEST_DATA not set')

try:
  institution, requirement_id, block_type, *_ = TEST_DATA.split('/')[1].split('_')
except ValueError:
  sys.exit(f'{TEST_DATA} is not a valid block string')

with open('../quarantine_list.csv') as rfile:
  reader = csv.reader(rfile)
  for line in reader:
    if reader.line_num == 1 or len(line) == 0 or line[0].startswith('#'):
      continue
    row = Row._make(line)
    if row.institution == institution and row.requirement_id == requirement_id:
      sys.exit(f'{institution} {requirement_id} is already quarantined: "{line}"')

reason = input(f'Why quarantine {institution} {requirement_id}? ')
if len(reason) == 0:
  sys.exit('Not quarantined')

can_ellucian = input('Does ellucian parse this block correctly? (Yn) ')
can_ellucian = 'Yes' if can_ellucian.lower().startswith('y') else 'No'

with open('../quarantine_list.csv', 'a') as wfile:
  writer = csv.writer(wfile)
  writer.writerow([institution, requirement_id, block_type, reason, can_ellucian])
print(f'Added: {institution} {requirement_id} {block_type} {reason}')
os.system('./sort_quar')
