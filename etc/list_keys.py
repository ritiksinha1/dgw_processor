#! /usr/local/bin/python3
""" This is a framework for looking at the keys in parse trees. The code changes depending on
    what's needed.
"""

import psycopg
import sys

from psycopg.rows import dict_row


def do_conditional(arg: dict, level: str):
  """ Recurse through a conditional dict, printing found keys and the t/f pattern with which they
      occur.
  """
  if len(level) > 10:
    print(institution, requirement_id, level, file=sys.stderr)
  for rule in arg['if_true']:
    if 'conditional' in rule.keys():
      do_conditional(rule['conditional'], level + 't')
    else:
      print(level + 't', list(rule.keys()))
  try:
    for rule in arg['if_false']:
      if 'conditional' in rule.keys():
        do_conditional(rule['conditional'], level + 'f')
      else:
        print(level + 'f', list(rule.keys()))
  except KeyError:
    pass


with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=dict_row) as cursor:
    cursor.execute("""
    select institution, requirement_id, block_type, block_value, parse_tree
      from requirement_blocks
      where block_type = 'MAJOR'
        and period_stop ~*'^9'
    """)
    print(f'{cursor.rowcount=}', file=sys.stderr)
    for row in cursor:
      institution = row['institution']
      requirement_id = row['requirement_id']
      parse_tree_dict = row['parse_tree']
      try:
        for header_item in parse_tree_dict['header_list']:

          # PROXY ADVICE IN HEADER?
          # if 'proxy_advice' in header_item.keys():
          #   print(row['institution'], row['requirement_id'], row['block_type'], row['block_value'],
          #         file=sys.stderr)

          # WHAT KEYS APPEAR IN HEADER CONDITIONALS?
          conditional = header_item['conditional']
          do_conditional(conditional, '')
        #   print('Header', list(header_item.keys()))
        # for body_item in parse_tree_dict['body_list']:
        #   print('Body', list(body_item.keys()))
      except KeyError:
        pass
