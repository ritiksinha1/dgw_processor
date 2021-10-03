#! /usr/local/bin/python3
""" Run the antler parser against a scribe block, and record
    info about the block, as well as timing and output info
    for later analysis.
"""

import os
import subprocess
import sys
import time

from argparse import ArgumentParser
from pathlib import Path

from dgw_filter import dgw_filter

DEBUG = os.getenv('DEBUG_RUN')

parser = ArgumentParser('run grun')
parser.add_argument('block_type')
parser.add_argument('requirement_block')
parser.add_argument('-t', '--timelimit', default=900)
args = parser.parse_args()
timelimit = int(args.timelimit)
block_type = args.block_type.lower()

test_dir = Path(f'./test_data.{block_type}')

file = Path(test_dir, args.requirement_block)
size = file.stat().st_size
lines = file.read_text()
lines = dgw_filter(lines)
num_lines = lines.count('\n')
lines = lines.encode('utf-8')   # Need bytes-like object for input arg to subprocess.run()
if DEBUG:
  print(f'{test_dir.name}/{file.name} has {size} bytes; {num_lines} lines. {timelimit=}')

if os.getenv('HOSTTYPE') == 'aarch64':
  classpath = './classes:/opt/homebrew/Cellar/antlr/4.9.2/antlr-4.9.2-complete.jar'
else:
  classpath = './classes:/usr/local/lib/antlr-4.9.2-complete.jar'

try:
  run_args = ['java', '-cp', classpath, 'org.antlr.v4.gui.TestRig', 'ReqBlock', 'req_block']
  t0 = time.time()
  completed = subprocess.run(run_args,
                             timeout=timelimit,
                             # stdin=file.open(),
                             input=lines,
                             capture_output=True)
  elapsed = time.time() - t0
  output = len(completed.stdout) + len(completed.stderr)
  if output != 0:
    with open(f'test_results.{args.block_type}/{args.requirement_block}', 'w') as errorlog:
      print(f'{completed.stdout} {completed.stderr}', file=errorlog)

except subprocess.TimeoutExpired:
  output = 'timeout'
  elapsed = timelimit + 1
  print(f'{args.block_type},{args.requirement_block},{num_lines},{output},{elapsed:0.1f}',
        file=sys.stderr)
print(f'{args.block_type},{args.requirement_block},{num_lines},{output},{elapsed:0.1f}')
