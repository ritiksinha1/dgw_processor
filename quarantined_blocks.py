#! /usr/local/bin/python3
""" Build a dict of quarantined blocks for importing into other modules.
"""
import csv
from collections import namedtuple
from pprint import pprint

quarantine_dict = dict()

Row = namedtuple('Row', 'institution requirement_id explanation can_ellucian')
quarantine_dict = {}
with open('/Users/vickery/Projects/dgw_processor/quarantine_list.csv') as qfile:
  reader = csv.reader(qfile)
  for line in reader:
    if reader.line_num == 1 or len(line) == 0 or line[0].startswith('#'):
      continue
    row = Row._make(line)
    ellucian = row.can_ellucian.lower().startswith('y')

    quarantine_dict[(row.institution, row.requirement_id)] = (row.explanation.strip('.'),
                                                              row.can_ellucian)

if __name__ == '__main__':
  pprint(quarantine_dict)
