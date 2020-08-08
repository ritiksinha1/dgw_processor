#! /usr/local/bin/python3
""" Look up the requirement text for all active blocks and save them in a set of test_data
    directories, named test_data.<<block type>>.
    There is a list of known bad blocks kept in the file "quarantine_list". Blocks in that list are
    moved to the test_data.quarantine directory instead of to the normal <<block_type>>
"""
import argparse
import re
import sys

from pathlib import Path
from pgconnection import PgConnection

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
quarantined_blocks = []
timeout_blocks = []
with open('./quarantine_list') as ql:
  for line in ql.readlines():
    # Ignore comments and blank lines
    line = re.sub(r'#.*$', '', line).strip()
    if len(line) < 1:
      continue
    try:
      institution, block_id, *_ = line.split()
      if _ == ['Timeout']:
        timeout_blocks.append((institution, block_id))
      else:
        quarantined_blocks.append((institution, block_id))
    except ValueError as ve:
      pass

quarantine_dir = Path('./test_data.quarantine')
if quarantine_dir.is_dir():
  for file in quarantine_dir.iterdir():
    file.unlink()
else:
  quarantine_dir.mkdir(exist_ok=True)

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
    # Check for quarantined status
    text_to_write = dgw_filter(block.requirement_text)
    title_str = re.sub(r'\_$', '', re.sub(r'_+', '_', re.sub(r'[\][\(\):/\&\t ]',
                                                             '_', block.title)))
    if (block.institution, block.requirement_id) in quarantined_blocks:
      file = Path(quarantine_dir,
                  f'{block.institution}_{block.requirement_id}_{title_str}'.strip('_'))
      print(f'{block.institution} {block.requirement_id} {block.block_type} is quarantined')
    # Check for timeout status
    elif (block.institution, block.requirement_id) in timeout_blocks:
      file = Path(timeout_dir,
                  f'{block.institution}_{block.requirement_id}_{title_str}'.strip('_'))
      print(f'{block.institution} {block.requirement_id} {block.block_type} is timeouted')
    else:
      file = Path(directory,
                  f'{block.institution}_{block.requirement_id}_{title_str}'.strip('_'))
    file.write_text(text_to_write)
