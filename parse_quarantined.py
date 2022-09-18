#! /usr/local/bin/python3
""" Parse all currently-quarantined blocks. Liberate any that now parse okay.
"""

import os
import psycopg
import sys

from dgw_parser import parse_block
from psycopg.rows import namedtuple_row
from quarantine_manager import QuarantineManager

progress = len(sys.argv) > 1

quarantined_dict = QuarantineManager()

# Convert keys to a list so we can delete from the dict if anything parses correctly now.
keys = list(quarantined_dict.keys())
num_quarantined = len(keys)
num_nolonger = 0
num_success = 0
num_fail = 0
with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    for index, key in enumerate(keys):
      if progress:
        print(f'{index+1:5} / {len(keys)}')
      institution, requirement_id = key
      cursor.execute("""
      select institution, requirement_id, period_start, period_stop, requirement_text
        from requirement_blocks
       where institution = %s
         and requirement_id = %s
      """, (institution, requirement_id))
      row = cursor.fetchone()
      if not row.period_stop.startswith('9'):
        num_nolonger += 1
        del quarantined_dict[key]
        print(f'{institution} {requirement_id} Dequarantined: No longer current')
        continue
      parse_tree = parse_block(institution, requirement_id, row.period_start, row.period_stop,
                               row.requirement_text)
      try:
        if error_msg := parse_tree['error']:
          if 'timeout' in error_msg.lower():
            print(f'{institution} {requirement_id} Timeout: {error_msg}')
          num_fail += 1
      except KeyError:
        # Parsed okay: dequarantine it.
        del quarantined_dict[key]
        print(f'{institution} {requirement_id} OK: No longer quarantined')
        num_success += 1
if progress:
  print()
print(f'Quarantined before:  {num_quarantined:>5,}\n'
      f'No longer current:   {num_nolonger:>5}\n'
      f'Parsed successfully: {num_success:>5,}\n'
      f'Quarantined after:   {num_fail:>5,}')
