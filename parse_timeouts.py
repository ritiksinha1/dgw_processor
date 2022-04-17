#! /usr/local/bin/python3
""" Re-parse requirement blocks that timed out.
"""

import argparse
import os
import psycopg
import sys
import time

from dgw_parser import parse_block
from psycopg.rows import namedtuple_row


def elapsed(since: float):
  """ Show the hours, minutes, and seconds that have elapsed since since seconds ago.
  """
  h, ms = divmod(int(time.time() - since), 3600)
  m, s = divmod(ms, 60)
  return f'{m:02}:{s:02}'


if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser('Re-parse Scribe Blocks that timed out.')
  arg_parser.add_argument('-d', '--debug', action='store_true')
  arg_parser.add_argument('-t', '--timelimit', type=int, default=1800)

  args = arg_parser.parse_args()

  # Get the institutions and requirement_ids of the error blocks.
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute("""
      select institution, requirement_id,
             period_start, period_stop,
             requirement_text,
             parse_tree->'error' as error
        from requirement_blocks
       where period_stop ~* '^9'
         and parse_tree->'error' is not null
         and (parse_tree->'error')::text ~* 'Timeout'
       order by institution, requirement_id
      """)
      num_attempted = cursor.rowcount
      num_fail = 0
      num_succeed = 0
      num_timeout = 0
      for row in cursor:

        print(f'{row.institution} {row.requirement_id}', end='')
        sys.stdout.flush()
        start = time.time()
        parse_tree = parse_block(row.institution,
                                 row.requirement_id,
                                 row.period_start,
                                 row.period_stop,
                                 row.requirement_text,
                                 args.timelimit)

        try:
          error_msg = parse_tree['error'].strip('\n')
          if 'timeout' in error_msg.lower():
            print(f' Timeout {elapsed(start)}')
            num_timeout += 1
          else:
            print(f' Failed {error_msg}')
            num_fail += 1
        except KeyError:
          print(f' Completed {elapsed(start)}')
          num_succeed += 1

  print(f'Timelimit:{args.timelimit:>7,} sec\n'
        f'Attempted:{num_attempted:>7,}\n'
        f'Success:  {num_succeed:>7,}\n'
        f'Timeout:  {num_timeout:>7,}\n'
        f'Failed:   {num_fail:>7,}')
