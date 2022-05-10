#! /usr/local/bin/python3
""" Analyze the condition_report dicts from parse_all
    Need to break it down by block type and context depth.
"""
import json
import os
import statistics
import sys

from collections import defaultdict


def stats(dist: list) -> tuple:
  """
  """
  return (f'N: {len(dist):3}  '
          f'Min: {min(dist):3}  '
          f'Avg: {statistics.mean(dist):4.1f}  '
          f'Max: {max(dist):3}')


freq_dist_by_block_type = defaultdict(lambda: defaultdict(int))

lhs = defaultdict(int)
ops = defaultdict(int)
rhs = defaultdict(int)
lines = open('./conditions_report.txt').readlines()
for line in lines:
  report = json.loads(line)

  # Generate frequency counts of number of relop terms by block_type
  freq_dist_by_block_type[report['block_type']][len(report['relop_expressions'])] += 1

  # Generate counts of lhs, relop, rhs values
  for relop_expression in report['relop_expressions']:
    lhs[relop_expression[0]] += 1
    ops[relop_expression[1]] += 1
    rhs[relop_expression[2]] += 1

print('\nRELOPS PER CONDITION')
for bt, dist in freq_dist_by_block_type.items():
  print(f'{bt:8}', stats(dist))

# Display counts of lhs, relop, rhs values
print(f'\n{len(lhs):>9,} LEFTHAND SIDE VALUES')
d = {k: v for k, v in sorted(lhs.items(), key=lambda item: item[1], reverse=True)}
for k, v in d.items():
  print(f'{v:9,} {k}')

print(f'\n{len(ops):>9,} OPERATORS')
d = {k: v for k, v in sorted(ops.items(), key=lambda item: item[1], reverse=True)}
for k, v in d.items():
  print(f'{v:>8,} {k}')

print(f'\n{len(rhs):>9,} RIGHTHAND SIDE VALUES')
d = {k: v for k, v in sorted(rhs.items(), key=lambda item: item[1], reverse=True)}
for k, v in d.items():
  print(f'{v:>8,} {k}')
