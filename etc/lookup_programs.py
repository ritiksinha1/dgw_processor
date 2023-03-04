#! /usr/local/bin/python3
"""Attempt to use typed text to identify programs based on CIP codes.

Just shows how many matches there are as you type chars.
"""
import psycopg
import sys
import termios
import tty

from collections import defaultdict
from psycopg.rows import namedtuple_row


def _getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute("""
      select cip2020code, cip2020title||' '||soc2018title as string
      from cip_soc
      """)
    cip_soc_text = {row.cip2020code: ' '.join(set(row.string.lower().split()))
                    for row in cursor.fetchall() if row.cip2020code != 'NO MATCH'}

    cursor.execute("""
      select institution, plan, cip_code from cuny_acad_plan_tbl
      """)
    cuny_plans = defaultdict(list)
    for row in cursor.fetchall():
      cuny_plans[row.cip_code].append((row.institution, row.plan))

line = ''
while True:
  ch = _getch()
  print(ch, end='')
  if ch == '\r':
    print('\n', end='')
    line = ch = ''
  sys.stdout.flush()
  if ch == 'q' or ch == '\u0004':
    exit(f'\n{line=}')
  line += ch
  keys = set()
  values = []
  for key, value in cip_soc_text.items():
    if line in value:
      keys.add(key)
      values.append(value)
  print(f' {len(keys)}', end='')
  if len(keys) < 12:
    print(' ', keys, values, end='')
    for cip_code in keys:
      if len(cuny_plans[cip_code]) > 0:
        print(f' {cuny_plans[cip_code]}', end='')
  print()
