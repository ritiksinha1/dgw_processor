#! /usr/local/bin/python3
""" Add a requirement block to the quarantine list.
    Get the institution and requirement_id from the TEST_DATA environment variable.
    Get the reason from stdin.
"""

import os
import sys
import csv
import subprocess

from collections import namedtuple
from pathlib import Path

from quarantine_manager import QuarantineManager

quarantined_dict = QuarantineManager()

# Intengrity Check: the rows in the quarantined_dict must match the files in the test_data.quarantine
# dir.
quarantine_dir = Path('./test_data.quarantine')
# for file in quarantine_dir.glob('*'):
#   institution, requirement_id, block_type = file.name.split('_')
#   if (institution, requirement_id) not in quarantined_dict.keys():
#     sys.exit(f'Fix quarantines: {institution} {requirement_id} is not in ../quarantine_list.csv')
# for key, value in quarantined_dict.items():
#   institution, requirement_id, block_type = (key + (value[0],))
#   if not Path(quarantine_dir, f'{institution}_{requirement_id}_{block_type}').is_file():
#     sys.exit(f'Fix quarantines: {institution}_{requirement_id}_{block_type} is not in '
             # f'./test_data.quarantine')

# Now test that the test data hasn't already been quarantined
try:
  test_data = os.getenv('TEST_DATA')
  if test_data is None:
    raise TypeError()
  # Mystery: where does the asterisk at the end of the environment variable come from?
  test_data = Path(test_data.strip('*'))
except TypeError as te:
  sys.exit('TEST_DATA not set')

try:
  institution, requirement_id, block_type = test_data.name.split('_')
except ValueError:
  sys.exit(f'{test_data} is not a valid requirement block filename')

if quarantined_dict.is_quarantined((institution, requirement_id)):
  sys.exit(f'{institution} {requirement_id} is already quarantined: "'
           f'{quarantined_dict[(institution, requirement_id)]}"')

reason = input(f'Why quarantine {institution} {requirement_id}? ')
if len(reason) == 0:
  sys.exit('Not quarantined')

can_ellucian = input('Does ellucian parse this block correctly? (Yn) ')
can_ellucian = ('No' if can_ellucian.lower().startswith('n') else
                'Yes' if can_ellucian.lower().startswith('y') else
                'Unknown')

# with open('../quarantine_list.csv', 'a') as wfile:
#   writer = csv.writer(wfile)
#   writer.writerow([institution, requirement_id, block_type, reason, can_ellucian])
# # Put the quarantine list CSV file into institution/requirement_id order
# subprocess.run('./sort_quarantine_list.sh')
quarantined_dict[(institution, requirement_id)] = [reason, can_ellucian]
# Move the offending item into test_data.quarantine
test_data.rename(Path(quarantine_dir, test_data.name))

print(f'Added: {institution} {requirement_id} {block_type} {reason}')
