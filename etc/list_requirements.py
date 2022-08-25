#! /usr/local/bin/python3
""" Development utility to list requirement contexts in course_mapper_requirements.csv
"""

import argparse
import csv
import json
import sys

from collections import namedtuple

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('institution')
  parser.add_argument('requirement_id')
  parser.add_argument('--requirement_key', '-k')
  parser.add_argument('--full_text', '-f', action='store_true')
  args = parser.parse_args()
  institution = requirement_id = requirement_key = None
  if args.institution:
    institution = f'{args.institution.strip("10").upper()}01'
  if args.requirement_id:
    requirement_id = f'RA{args.requirement_id.upper().strip("AR"):>06}'
  if args.requirement_key:
    requirement_key = int(args.requirement_key)
  print(institution, requirement_id)

  csv.field_size_limit(sys.maxsize)
  with open('/Users/vickery/projects/dgw_processor/course_mapper.requirements.csv') as req_file:
    reader = csv.reader(req_file)
    for line in reader:
      if reader.line_num == 1:
        Row = namedtuple('Row', [col.lower().replace(' ', '_') for col in line])
      else:
        row = Row._make(line)
        if row.institution == institution and row.requirement_id == requirement_id:
          print('')
          if requirement_key is None or requirement_key == int(row.requirement_key):
            print(f'{row.institution} {row.requirement_id} {row.requirement_key:>08}:')
            for ctx in json.loads(row.context):
              for k, v in ctx.items():
                line = f'  {k}: {v}'
                if args.full_text or len(line) < 132:
                  print(line)
                else:
                  print(line[0:129] + '...')
          else:
            print(f'{row.institution} {row.requirement_id} {row.requirement_key:>08}:', end='')
            for ctx in json.loads(row.context):
              print(f' | {list(ctx.keys())[0]}', end='')
            print()
        else:
          pass
