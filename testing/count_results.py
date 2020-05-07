#! /usr/local/bin/python3
""" Count the sizes of the test_result files.
    Report all sizes after telling what percentage were length 0, indicating complete parsing.
"""
from pathlib import Path
from collections import Counter
sizes = Counter()
for file in Path('test_results').glob('*'):
  sizes[file.stat().st_size] += 1

print(f'{100 * sizes[0] / sum(sizes.values()):.1f}%')
for key in sorted(sizes.keys()):
  print(f'{key:04}: {sizes[key]:,}')
