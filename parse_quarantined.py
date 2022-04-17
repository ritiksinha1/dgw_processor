#! /usr/local/bin/python3
""" Parse all currently-quarantined blocks. Liberate any that now parse okay.
"""

import os
import psycopg
import sys

from dgw_parser import parse_block
from psycopg.rows import namedtuple_row
from quarantine_manager import QuarantineManager

quarantined_dict = QuarantineManager()

# Convert keys to a list so we can delete from the dict if anything parses correctly now.
keys = list(quarantined_dict.keys())
num_quarantined = len(keys)
num_success = 0
num_fail = 0
with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    for key in keys:
      institution, requirement_id = key
      print(f'{institution} {requirement_id} ', end='')
      cursor.execute("""
      select institution, requirement_id, period_start, period_stop, requirement_text
        from requirement_blocks
       where institution = %s
         and requirement_id = %s
      """, (institution, requirement_id))
      row = cursor.fetchone()
      parse_tree = parse_block(institution, requirement_id, row.period_start, row.period_stop,
                               row.requirement_text)
      try:
        if error_msg := parse_tree['error']:
          print('Failed')
          num_fail += 1
      except KeyError:
        # Parsed okay: dequarantine it.
        del quarantined_dict[key]
        print('OK: No longer quarantined')
        num_success += 1

print(f'Quarantined:{num_quarantined:>5,}\n'
      f'Success:    {num_success:>5,}\n'
      f'Fail:       {num_fail:>5,}')
