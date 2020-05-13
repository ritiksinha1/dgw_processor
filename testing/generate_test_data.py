#! /usr/local/bin/python3
""" Look up the requirement blocks for all active majors and save them in the test_data directory.
"""
import argparse
import re
import sys

from pathlib import Path
from pgconnection import PgConnection

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
  try:
    directory.mkdir(mode=0o755, exist_ok=True)
  except FileExistsError as fee:
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
    title_str = re.sub(r'\_$', '', re.sub(r'_+', '_', re.sub(r'[\][\(\):/\&\t ]',
                                                             '_', block.title)))
    file = Path(directory,
                f'{block.institution}_{block.requirement_id}_{title_str}'.strip('_'))
    file.write_text(re.sub(r'[Ee][Nn][Dd]\.(.|\n)*', 'END.\n', block.requirement_text))
