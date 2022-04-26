#! /usr/local/bin/python3
""" Analyze the condition_report dicts from parse_all
    Need to break it down by block type and context depth.
"""
import json
import os
import sys
from collections import defaultdict

lhs = defaultdict(int)
ops = defaultdict(int)
rhs = defaultdict(int)
lines = open('./conditions_report.txt').readlines()
for line in lines:
  report = json.loads(line)
  for relop_expression in report['relop_expressions']:
    lhs[relop_expression[0]] += 1
    ops[relop_expression[1]] += 1
    rhs[relop_expression[2]] += 1

print(f'{len(lhs):>9,} Lefthand Side Values')
d = {k: v for k, v in sorted(lhs.items(), key=lambda item: item[1], reverse=True)}
for k, v in d.items():
  print(f'{v:9,} {k}')

print(f'\n{len(ops):>9,} Operators')
d = {k: v for k, v in sorted(ops.items(), key=lambda item: item[1], reverse=True)}
for k, v in d.items():
  print(f'{v:>8,} {k}')

print(f'\n{len(rhs):>9,} Righthand Side Values')
d = {k: v for k, v in sorted(rhs.items(), key=lambda item: item[1], reverse=True)}
for k, v in d.items():
  print(f'{v:>8,} {k}')
