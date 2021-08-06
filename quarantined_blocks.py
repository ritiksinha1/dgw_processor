#! /usr/local/bin/python3
""" Build a dict of quarantined blocks for importing into other modules.
"""
import csv
from collections import namedtuple
from pprint import pprint

quarantined_dict = {}
with open('/Users/vickery/Projects/dgw_processor/quarantine_list.csv') as qfile:
  reader = csv.reader(qfile)
  for line in reader:
    if reader.line_num == 1:
      Row = namedtuple('Row', [col.lower().replace(' ', '_') for col in line])
    else:
      row = Row._make(line)
      ellucian = row.can_ellucian.lower().startswith('y')

      quarantined_dict[(row.institution, row.requirement_id)] = (row.block_type,
                                                                 row.explanation.strip('.'),
                                                                 row.can_ellucian)

if __name__ == '__main__':
  pprint(quarantined_dict)
