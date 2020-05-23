#! /usr/local/bin/python3
""" Run the antler parser against a scribe block, and record
    info about the block, as well as timing and output info
    for later analysis.
"""

import os
import subprocess
import sys
import time

from pathlib import Path

timelimit = 1500

block_type = sys.argv[1]
test_dir = Path(f'./test_data.{block_type}')
requirement_block = sys.argv[2]

file = Path(test_dir, requirement_block)
size = file.stat().st_size
lines = file.read_text().count('\n')
try:
  t0 = time.time()
  completed = subprocess.run(['grun', 'ReqBlock', 'req_block'],
                             timeout=timelimit,
                             stdin=file.open(),
                             capture_output=True)
  elapsed = time.time() - t0
  output = len(completed.stdout) + len(completed.stderr)
  if output != 0:
    with open(f'test_results.{block_type}/{sys.argv[2]}', 'w') as errorlog:
      print(f'{completed.stdout} {completed.stderr}', file=errorlog)

except subprocess.TimeoutExpired:
  output = 'timeout'
  elapsed = TIMELIMIT + 1
  print(f'{block_type}\t{requirement_block}\t{lines}\t{output}\tTIMEOUT', file=sys.stderr)

print(f'{block_type}\t{requirement_block}\t{lines}\t{output}\t{elapsed:0.1f}')
