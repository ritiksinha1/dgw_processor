#! /usr/local/bin/python3
""" Count the sizes of the test_result files.
    Report all sizes after telling what percentage were length 0, indicating complete parsing.
"""
from pathlib import Path
from collections import Counter
all_sizes = Counter()
school_sizes = Counter()
for file in Path('test_results').glob('*'):
  size = file.stat().st_size
  all_sizes[file.stat().st_size] += 1
  school = file.name[0:3]
  school_sizes[f'{school}-{size}'] += 1

print(f'{100 * all_sizes[0] / sum(all_sizes.values()):.1f}%')
for key in sorted(all_sizes.keys()):
  print(f'{key:04}: {all_sizes[key]:,}')

for key in sorted(school_sizes.keys()):
  print(f'{key}: {school_sizes[key]:,}')

