#! /usr/local/bin/python3
""" Check whether quarantined files have been cleaned up yet.
    Try to parse each quarantined block. If a block doesn't generate any errors, remove it from
    ../quarantine_list.csv and move the block from test_data.quarantine to test_data.{block_type}
"""

import subprocess
import sys

from pathlib import Path

from dgw_preprocessor import dgw_filter
from quarantine_manager import QuarantineManager

quarantined_dict = QuarantineManager()
quarantined_dir = Path('/Users/vickery/Projects/dgw_processor/testing/test_data.quarantine')
classpath = './classes:/usr/local/lib/antlr-4.9.2-complete.jar'

timelimit = 60

# Step through all the currently-quarantined blocks
for key, value in quarantined_dict.items():
  quarantined_file = Path(quarantined_dir, f'{key.institution}_{key.requirement_id}_{value[0]}')
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
      del quarantined_dict[key]
      quarantined_file.rename(f'./test_data.{value[0].lower()}/{quarantined_file.name}')
      print(f'{quarantined_file.name} is no longer quarantined', file=sys.stderr)
    else:
      print(f'{quarantined_file.name} is still quarantined', file=sys.stderr)
  except subprocess.TimeoutExpired:
    print(f'{quarantined_file} timed out', file=sys.stderr)
