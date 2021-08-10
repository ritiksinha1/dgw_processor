#! /usr/local/bin/python3
""" Look up the requirement text for all active blocks and save them in a set of test_data
    directories, named test_data.<<block type>>.
    There is a list of known bad blocks kept in the file "quarantine_list". Blocks in that list are
    moved to the test_data.quarantine directory instead of to the normal <<block_type>>
"""
import argparse
import re
import sys
import csv

from pathlib import Path
from collections import namedtuple

from pgconnection import PgConnection
from quarantine_manager import QuarantineManager
from dgw_filter import dgw_filter

# Parse args
parser = argparse.ArgumentParser(description='Generate test data for ReqBlock.g4')
parser.add_argument('-d', '--debug', action='store_true', default=False)
parser.add_argument('-p', '--period', default='99999999')
parser.add_argument('block_types', metavar='block_type', nargs='*', default=['all'])
args = parser.parse_args()
period_stop = args.period
if period_stop.lower() == 'active':
  period_stop = '99999999'
if period_stop != '99999999':
  exit(f'"{period_stop}" is an unsupported period. '
       'Only "active" or "99999999" are valid for now.')

# Get quarantine list
# Row = namedtuple('ROW', 'institution requirement_id block_type reason can_ellucian')
# quarantined_blocks = []
# with open('../quarantine_list.csv') as qfile:
#   reader = csv.reader(qfile)
#   for line in reader:
#     if reader.line_num == 1 or len(line) == 0 or line[0].startswith('#'):
#       continue
#     row = Row._make(line)
#     if 'timeout' in row.reason.lower():
#       timeout_blocks.append((row.institution.strip(), row.requirement_id.strip()))
#     else:
#       quarantined_blocks.append((row.institution, row.requirement_id.strip()))
quarantined_dict = QuarantineManager()

quarantine_dir = Path('./test_data.quarantine')
if quarantine_dir.is_dir():
  for file in quarantine_dir.iterdir():
    file.unlink()
else:
  quarantine_dir.mkdir(exist_ok=True)

timeout_blocks = []
timeout_dir = Path('./test_data.timeout')
if timeout_dir.is_dir():
  for file in timeout_dir.iterdir():
    file.unlink()
else:
  timeout_dir.mkdir(exist_ok=True)

block_types = args.block_types
if 'all' in block_types:
  block_types = ['major', 'minor', 'conc', 'degree', 'other']

for block_type in block_types:
  directory = Path(f'test_data.{block_type.lower()}')
  if directory.is_dir():
    for file in directory.iterdir():
      file.unlink()
  else:
    exit(f'{directory} is not a directory')

  conn = PgConnection()
  cursor = conn.cursor()

  cursor.execute(f"""
                 select * from requirement_blocks
                 where block_type = '{block_type.upper()}'
                   and period_stop = '{period_stop}'
                   order by institution, requirement_id""")
  print(f'{cursor.rowcount} {block_type}s found')

  for block in cursor.fetchall():
    institution = block.institution
    requirement_id = block.requirement_id
    block_type = block.block_type.upper()

    # Check for quarantined status
    text_to_write = dgw_filter(block.requirement_text)
    if quarantined_dict.is_quarantined((block.institution, block.requirement_id)):
      file = Path(quarantine_dir,
                  f'{institution}_{requirement_id}_{block_type}'.strip('_'))
      print(f'{institution} {requirement_id} {block_type} is quarantined')

    # Check for timeout status
    elif (institution, requirement_id) in timeout_blocks:
      file = Path(timeout_dir,
                  f'{institution}_{requirement_id}_{block_type}'.strip('_'))
      print(f'{institution} {requirement_id} {block_type} is timeouted')
    else:
      file = Path(directory,
                  f'{institution}_{requirement_id}_{block_type}'.strip('_'))
    file.write_text(text_to_write)
