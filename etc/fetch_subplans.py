#! /usr/local/bin/python3
""" Fetch subplan information from the mapper's requirements.other column
"""
import csv
import json
import sys

from collections import namedtuple

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
  exit('Usage: fetch_subplans [institution [plan|RA#]]')

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

      # Display the subplans
      print(plan_info['subplans'])
      subplans = plan_info['subplans']
      print(f'\n{row.institution} {row.requirement_id:8} {target_plan:12}', end='')
      if len(subplans) == 0:
        print('  no subplans')
        continue
      else:
        s = '' if len(subplans) == 1 else 's'
        print(f'  {len(subplans):3} subplan{s}\n'
              f'  Subplan     Enrolled  RA       major1       Title')
        for subplan in subplans:
          try:
            blocks = zip(subplan['requirement_id'], subplan['major1'], subplan['title'])
            blocks_list = []
            for block in blocks:
              major1_str = f'{block[1]:12}' if block[1] else '            '
              title_str = f'{block[2]}' if block[2] else ''
              blocks_list.append(f'{block[0]} {major1_str} {title_str}')
            blocks_str = ', '.join(blocks_list)
          except KeyError as err:
            blocks_str = 'No requirement blocks'
          print(f'  {subplan["subplan"]:12} {subplan["enrollment"]:7,}  {blocks_str}')
