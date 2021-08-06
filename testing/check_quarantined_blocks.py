#! /usr/local/bin/python3
""" Check whether quarantined files have been cleaned up yet.
    Try to parse each quarantined block. If a block doesn't generate any errors, remove it from
    ../quarantine_list.csv and move the block from test_data.quarantine to test_data.{block_type}
"""

from pathlib import Path

from copy import copy
import csv
import subprocess
import sys

from dgw_filter import dgw_filter
from quarantined_blocks import quarantined_dict

target_dict = copy(quarantined_dict)

classpath = './classes:/usr/local/lib/antlr-4.9.2-complete.jar'

quarantined_dir = Path('./test_data.quarantine')

timelimit = 60

# Step through all the currently-quarantined blocks
for key, value in quarantined_dict.items():
  quarantined_file = Path(quarantined_dir, f'{key[0]}_{key[1]}_{value[0]}')
  block_text = dgw_filter(quarantined_file.read_text())
  block_text = block_text.encode('utf-8')
  try:
    completed = subprocess.run(['java', '-cp', classpath,
                                'org.antlr.v4.gui.TestRig',
                                'ReqBlock',
                                'req_block'],
                               timeout=timelimit,
                               input=block_text,
                               capture_output=True)
    if len(completed.stderr) == 0:
      del target_dict[key]
      quarantined_file.rename(f'./test_data.{value[0].lower()}/{quarantined_file.name}')
      print(f'{quarantined_file.name} is no longer quarantined', file=sys.stderr)
  except subprocess.TimeoutExpired:
    print(f'{quarantined_file} timed out', file=sys.stderr)

if len(target_dict) != len(quarantined_dict):
  print(f'You gotta remove {len(quarantined_dict) - len(target_dict)} csv row(s)')
