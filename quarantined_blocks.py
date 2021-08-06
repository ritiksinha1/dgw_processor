#! /usr/local/bin/python3
""" Build a dict of quarantined blocks for importing into other modules.
"""
import csv

from collections import namedtuple
from pprint import pprint

from catalogyears import catalog_years
from pgconnection import PgConnection

conn = PgConnection()
cursor = conn.cursor()

quarantined_dict = {}
with open('/Users/vickery/Projects/dgw_processor/quarantine_list.csv') as qfile:
  reader = csv.reader(qfile)
  for line in reader:
    if reader.line_num == 1:
      Row = namedtuple('Row', [col.lower().replace(' ', '_') for col in line])
    else:
      row = Row._make(line)
      # augment the dict with info about the status of the block
      cursor.execute(f"""
    select period_start, period_stop
      from requirement_blocks
     where institution = '{row.institution}'
       and requirement_id = '{row.requirement_id}'""")
      assert cursor.rowcount == 1
      periods = cursor.fetchone()
      periods = catalog_years(periods.period_start, periods.period_stop)
      catalog = periods.catalog_type
      last = periods.last_year
      last = 'Current' if last == 'Now' else 'Unknown' if last.startswith('Unknown') else last
      ellucian = row.can_ellucian.lower().startswith('y')

      quarantined_dict[(row.institution, row.requirement_id)] = (row.block_type,
                                                                 catalog, last,
                                                                 row.explanation.strip('.'),
                                                                 row.can_ellucian)
conn.close()

if __name__ == '__main__':
  pprint(quarantined_dict)
