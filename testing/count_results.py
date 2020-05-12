#! /usr/local/bin/python3
""" Count the sizes of the test_result files.
    Tell what percentage were length 0, indicating complete parsing.
    Report CUNY-wide (highlighted) as well as individual colleges’ results.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

highlight_on = '\u001b[31m'  # Red Text
highlight_off = '\u001b[0m'

if os.getenv('DEBUG'):
  logfile = sys.stderr
else:
  time_stamp = str(datetime.now()).replace(' ', '_').rstrip('0123456789').rstrip('.')
  logfile = open(f'count_results_{time_stamp}.log', 'w')

for block_type in ['major', 'minor', 'conc', 'degree', 'other']:
  block_type_str = block_type.upper()
  num_files = len([f for f in Path(f'test_results.{block_type}').glob('*')])
  all_sizes = Counter()
  school_sizes = defaultdict(Counter)
  for file in Path(f'test_results.{block_type}').glob('*'):
    size = file.stat().st_size
    all_sizes[size] += 1
    school = file.name[0:3]
    school_sizes[school][size] += 1
  try:
    print(f'\n{highlight_on}ALL:  {100 * all_sizes[0] / sum(all_sizes.values()):.1f}% of '
          f'{num_files:,} {block_type_str}s{highlight_off}', file=logfile)
  except ZeroDivisionError:
    pass

  for school in sorted(school_sizes.keys()):
    try:
      print(f'{school}: '
            f'{100 * school_sizes[school][0] / sum(school_sizes[school].values()):>5.1f}%'
            f' of {sum(school_sizes[school].values()):,} {block_type_str.lower()}s', file=logfile)
    except ZeroDivisionError:
      pass
