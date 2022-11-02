#! /usr/local/bin/python3
""" Parse all currently-quarantined blocks. Liberate any that now parse okay.
"""

import argparse
import os
import psycopg
import sys

from dgw_parser import parse_block
from psycopg.rows import namedtuple_row
from quarantine_manager import QuarantineManager


if __name__ == '__main__':
  # Do you really need to show progress?
  # You are going to see ANTLR/DGW, etc messages for each file anyway.
  parser = argparse.ArgumentParser('Try to re-parse quarantined dap_req_blocks')
  parser.add_argument('-p', '--show-progress', action='store_true')
  args = parser.parse_args()

  quarantined_dict = QuarantineManager()

  # Convert keys to a list so we can delete from the dict if anything parses correctly now.
  keys = list(quarantined_dict.keys())
  num_quarantined = len(keys)
  num_nolonger = 0
  num_success = 0
  num_fail = 0
  error_word = '{error}'
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      with conn.cursor(row_factory=namedtuple_row) as update_cursor:
        for index, key in enumerate(keys):
          institution, requirement_id = key
          if args.show_progress:
            print(f'{institution} {requirement_id} {index+1:3}/{len(keys)}')

          cursor.execute("""
          select institution, requirement_id, period_start, period_stop,
                 requirement_text,
                 parse_tree->'error' as analysis_text
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
              num_fail += 1
              if 'timeout' in error_msg.lower():
                print(f'{institution} {requirement_id} Timeout: {error_msg}')

              # Restore the original error message
              analysis_text = row.analysis_text.replace("'", '|')
              restore_query = f"""
              update requirement_blocks
                     set parse_tree = jsonb_set(parse_tree, '{error_word}', '"{analysis_text}"')
               where institution = '{institution}'
                 and requirement_id = '{requirement_id}'"""
              update_cursor.execute(restore_query)
          except KeyError:
            # Parsed okay: dequarantine it.
            del quarantined_dict[key]
            print(f'{institution} {requirement_id} Parsed OK: No longer quarantined')
            num_success += 1

  print()
  print(f'Quarantined before:  {num_quarantined:>5,}\n'
        f'No longer current:   {num_nolonger:>5}\n'
        f'Parsed successfully: {num_success:>5,}\n'
        f'Quarantined after:   {num_fail:>5,}')
