#! /usr/local/bin/python3

import csv
import sys

from collections import namedtuple
from pprint import pprint, pformat

from catalogyears import catalog_years
from pgconnection import PgConnection


class QuarantineManager(dict):
  """
  """
  _quarantined_dict = None
  _columns = ['Institution', 'Requirement ID', 'Block Type', 'Catalog', 'Year', 'Explanation',
              'Can Ellucian']

  def __init__(self):
    if QuarantineManager._quarantined_dict is None:
      QuarantineManager._Row = namedtuple('_Row', [col.lower().replace(' ', '_')
                                          for col in QuarantineManager._columns])
      QuarantineManager._quarantined_dict = dict()
      with open('/Users/vickery/Projects/dgw_processor/quarantined_blocks.csv') as csv_file:
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
          if csv_reader.line_num == 1:
            QuarantineManager._columns = line
          else:
            row = QuarantineManager._Row._make(line)
            key, value = (row.institution, row.requirement_id), [row.block_type, row.catalog,
                                                                 row.year, row.explanation,
                                                                 row.can_ellucian]
            QuarantineManager._quarantined_dict[key] = value

  def __setitem__(self, k, v):
    QuarantineManager._quarantined_dict[k] = v

  def __delitem__(self, k):
    del QuarantineManager._quarantined_dict[k]

  def __getitem__(self, k):
    return(QuarantineManager._quarantined_dict[k])

  def is_qquarantined(self, k):
    return k in QuarantineManager._quarantined_dict.keys()

  def __str__(self):
    return pformat(QuarantineManager._quarantined_dict)


if __name__ == '__main__':
  quarantined_dict = QuarantineManager()
  print(quarantined_dict)
