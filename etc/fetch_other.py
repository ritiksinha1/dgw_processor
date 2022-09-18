#! /usr/local/bin/python3
""" Fetch information other than subplan info from the mapper's requirements.other column
"""
import csv
import json
import sys

from collections import namedtuple

csv.field_size_limit(2**20)

# Command line args: [institution [plan]]
target_institution = target_plan = target_requirement_id = None
if len(sys.argv) > 1:
  target_institution = sys.argv[1].upper().strip('10')
# The second option could be either a plan name or a requirement_id #
if len(sys.argv) > 2:
  if sys.argv[2].isdigit():
    target_requirement_id = f'RA{int(sys.argv[2]):06}'
  else:
    target_plan = sys.argv[2].upper()
if len(sys.argv) > 3:
  exit('Usage: fetch_other [institution [plan|RA#]]')

with open ('/Users/vickery/Projects/dgw_processor/course_mapper.programs.csv') as csv_file:
  reader = csv.reader(csv_file)
  for line in reader:
    if reader.line_num == 1:
      Row = namedtuple('Row', [c.lower().replace(' ', '_') for c in line])
    else:
      # Filter rows by cmd line args
      row = Row._make(line)
      if target_institution and target_institution != row.institution:
        continue
      other = json.loads(row.other)
      plan_info = other['plan_info']

      if target_plan and target_plan != plan_info['plan']:
        continue
      else:
        if target_requirement_id is None:
          target_requirement_id = plan_info['requirement_id']

      if target_requirement_id and target_requirement_id != plan_info['requirement_id']:
        continue
      else:
        if target_plan is None:
          target_plan = plan_info['plan']

      # Display all the keys, and the lengths of their lists
      print(f'\n{row.institution} {row.requirement_id:8} {target_plan:12}')
      for other_key, other_value in other.items():
        print(f'  {other_key} {len(other_value)}')
