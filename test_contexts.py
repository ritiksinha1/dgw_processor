#! /usr/local/bin/python3
""" Testing Aid
    Display context info for requirements.
    Give the institution, requirement_id, and context keys of interest on the command line.
"""
import csv
import json
import os
import sys

from collections import namedtuple
from pprint import pprint

if len(sys.argv) < 3:
  exit(f'Usage: {sys.argv[0]} institution requirement_id [context_key...')

institution = sys.argv[1][0:3].upper() + '01'
try:
  if sys.argv[2].upper() == 'ALL':
    requirement_id = 'ALL'
  else:
    requirement_id = f'RA{int(sys.argv[2].upper().strip("RA")):06}'
except ValueError as ve:
  exit(f'Invalid requirement_id')

valid_keys = ['all',   # block_info, choice, ... requirement_block
              'dump',  # pprint the whole cell
              'block_info',
              'choice',
              'condition',
              'max_transfer',
              'min_grade',
              'name',
              'remark',
              'requirement_block']
context_keys = []
for context_key in sys.argv[3:]:
  # Command line aliases: names and labels for 'name'
  if context_key.startswith('name') or context_key.startswith('label'):
    context_key = 'name'
  for valid_key in valid_keys:
    if valid_key.startswith(context_key):
      context_keys.append(valid_key)
if 'all' in context_keys:
  context_keys = valid_keys[2:]   # Omit all and dump

print(f'Requirement Contexts for {institution[0:3]} {requirement_id} [{" ".join(context_keys)}]')

with open('course_mapper.requirements.csv') as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    if reader.line_num == 1:
      Row = namedtuple('Row', [col.lower().replace(' ', '_') for col in line])
    else:
      row = Row._make(line)
      if (institution == 'ALL01' or row.institution == institution) and \
         (requirement_id == 'ALL' or row.requirement_id == requirement_id):
        context_col = json.loads(row.context)
        if 'dump' in context_keys:
          print(f'\nRequirement Key {row.requirement_key}')
          pprint(context_col)
        else:
          for ctx in context_col['context']:
            try:
              block_info = ctx['block_info']
              ctx_requirement_id = block_info['requirement_id']
            except KeyError:
              pass
            for key in context_keys:
              try:
                obj = ctx[key]
                if key == 'condition':
                  print(row.institution, row.requirement_id, ctx_requirement_id, obj.strip(')( '))
                else:
                  print(f'Requirement Key {row.requirement_key:>3} ', end='')
                  pprint(obj)
              except KeyError:
                pass
