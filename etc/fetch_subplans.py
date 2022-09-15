#! /usr/local/bin/python3
""" Fetch subplan information from the mapper's requirements.other column
"""
import csv
import json
import sys

from collections import namedtuple

# Command line args: [institution [plan]]
institution = plan = None
if len(sys.argv) > 1:
  institution = sys.argv[1].upper().strip('10')
if len(sys.argv) > 2:
  plan = sys.argv[2].upper()
if len(sys.argv) > 3:
  exit('Usage: fetch_subplans [institution [plan]]')
with open ('/Users/vickery/Projects/dgw_processor/course_mapper.programs.csv') as csv_file:
  reader = csv.reader(csv_file)
  for line in reader:
    if reader.line_num == 1:
      Row = namedtuple('Row', [c.lower().replace(' ', '_') for c in line])
    else:
      # Filter rows by cmd line args
      row = Row._make(line)
      if institution and institution != row.institution:
        continue
      other = json.loads(row.other)
      plan_info = other['plan_info']
      this_plan = plan_info['plan']
      if plan and plan != this_plan:
        continue

      # Display the subplans
      subplans = plan_info['subplans']
      print(f'\n{row.institution} {row.requirement_id:8} {this_plan:12}', end='')
      if len(subplans) == 0:
        print('  no subplans')
        continue
      else:
        s = '' if len(subplans) == 1 else 's'
        print(f'  {len(subplans):3} subplan{s}\n'
              f'  Subplan     Enroll  Requirement Block (Major1), ...')
        for subplan in subplans:
          try:
            blocks = zip(subplan['requirement_id'], subplan['major1'])
            blocks_list = []
            for block in blocks:
              major1_str = f' ({block[1]})' if block[1] else ' (None)'
              blocks_list.append(f'{block[0]}{major1_str}')
            blocks_str = ', '.join(blocks_list)
          except KeyError as err:
            blocks_str = 'No requirement blocks'
          print(f'  {subplan["subplan"]:12} {subplan["enrollment"]:5,}  {blocks_str}')
