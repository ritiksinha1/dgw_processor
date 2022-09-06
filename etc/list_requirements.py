#! /usr/local/bin/python3
""" Development utility to list requirement names in course_mapper_requirements.csv
"""

import argparse
import csv
import json
import sys

from collections import namedtuple

if __name__ == '__main__':
  # Can specify an (institution, requirement_id) pair, or a requirement_key
  parser = argparse.ArgumentParser()
  parser.add_argument('lookup', nargs='*', default=None)
  parser.add_argument('--requirement_key', '-k', type=int)
  parser.add_argument('--full_text', '-f', action='store_true')
  args = parser.parse_args()

  """ If there is a key, only matching row is shown.
      Show all rows for an institution/requirement_id, unless overridden by the key
  """
  institution = requirement_id = requirement_key = None

  if args.lookup:
    if len(args.lookup) == 2:
      institution = f'{args.lookup[0].strip("10").upper()}01'
      requirement_id = f'RA{args.lookup[1].upper().strip("AR"):>06}'
    else:
      exit(f'eh? {args.lookup}')

  if args.requirement_key:
    requirement_key = f'{args.requirement_key}'

  if institution:
    print(institution, requirement_id, requirement_key)
  else:
    print('Key', requirement_key)

  csv.field_size_limit(sys.maxsize)
  with open('/Users/vickery/projects/dgw_processor/course_mapper.requirements.csv') as req_file:
    reader = csv.reader(req_file)
    for line in reader:
      if reader.line_num == 1:
        Row = namedtuple('Row', [col.lower().replace(' ', '_') for col in line])
      else:
        row = Row._make(line)

        if (requirement_key and row.requirement_key != requirement_key) or \
           (institution and row.institution != institution) or \
           (requirement_id and row.requirement_id != requirement_id):
          continue
        print(f'\n{row.institution} {row.requirement_id} {int(row.requirement_key):>08}:')
        for ctx in json.loads(row.context):
          for k, v in ctx.items():
            line = f'  {k}: {v}'
            if args.full_text or len(line) < 132:
              print(line)
            else:
              print(line[0:129] + '...')
