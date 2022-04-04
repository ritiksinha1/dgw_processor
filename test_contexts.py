#! /usr/local/bin/python3
""" Testing Aid
    Display context info for requirements.
    Give the institution and requirement_id on the command line.
"""
import csv
import json
import os
import sys

from collections import namedtuple
from pprint import pprint

if len(sys.argv) != 3:
  exit(f'Usage: {sys.argv[0]} institution requirement_id')

institution = sys.argv[1][0:3].upper() + '01'
try:
  requirement_id = f'RA{int(sys.argv[2].upper().strip("RA")):06}'
except ValueError as ve:
  exit(f'Invalid requirement_id')

print(f'Requirement Contexts for {institution} {requirement_id}')

with open('course_mapper.requirements.csv') as csvfile:
  reader = csv.reader(csvfile)
  for line in reader:
    if reader.line_num == 1:
      Row = namedtuple('Row', [col.lower().replace(' ', '_') for col in line])
    else:
      row = Row._make(line)
      if row.institution == institution and row.requirement_id == requirement_id:
        print(f'\nRequirement Key {row.requirement_key}')
        context_col = json.loads(row.context)
        pprint(context_col['context'])
