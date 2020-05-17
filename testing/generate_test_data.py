#! /usr/local/bin/python3
""" Look up the requirement blocks for all active majors and save them in the test_data directory.
"""
import argparse
import re
import sys

from pathlib import Path
from pgconnection import PgConnection

from dgw_filter import filter

parser = argparse.ArgumentParser(description='Generate test data for ReqBlock.g4')
parser.add_argument('-d', '--debug', action='store_true', default=False)
parser.add_argument('-p', '--period', default='99999999')
parser.add_argument('block_types', metavar='block_type', nargs='*', default=['all'])
# Parse args
args = parser.parse_args()
period_stop = args.period
if period_stop.lower() == 'active':
  period_stop = '99999999'
if period_stop != '99999999':
  exit(f'"{period_stop}" is an unsupported period. '
       'Only "active" or "99999999" are valid for now.')
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
    text_to_write = filter(block.requirement_text)
    # Don't test empty or all-comment blocks (BAR01 RA000625)
    test_for_empty = re.sub(r'#.*?\n', '', text_to_write).strip()
    test_for_empty = re.sub(r'\s*?\n', '', test_for_empty)
    if test_for_empty == '':
      print(f'Ignoring empty block: {block.institution} {block.requirement_id} {block.block_type}')
      continue
    title_str = re.sub(r'\_$', '', re.sub(r'_+', '_', re.sub(r'[\][\(\):/\&\t ]',
                                                             '_', block.title)))
    file = Path(directory,
                f'{block.institution}_{block.requirement_id}_{title_str}'.strip('_'))
    file.write_text(text_to_write)
