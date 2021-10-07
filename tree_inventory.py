#! /usr/local/bin/python3

import argparse
import os
import sys

import datetime

from collections import defaultdict, namedtuple
from pprint import pprint

from pgconnection import PgConnection


def make_bin():
  """ defaultdict factory for frequency distributions
  """
  return defaultdict(int)


if __name__ == '__main__':

  parser = argparse.ArgumentParser('Look at parse tree properties')
  parser.add_argument('--errors', action='store_true')
  parser.add_argument('--keys', action='store_true')

  args = parser.parse_args()

  conn = PgConnection()
  cursor = conn.cursor()

  if args.errors:
    with open('rerun.sh', 'a') as reruns:
      print(f'# {datetime.datetime.now().isoformat()}', file=reruns)

      # Get timeout blocks
      cursor.execute(f"""
                     select institution, requirement_id, parse_tree
                       from requirement_blocks
                      where parse_tree->'error' is not null
                      """)
      if cursor.rowcount == 0:
        print('No error blocks found')
      else:
        for row in cursor.fetchall():
          parse_tree = row.parse_tree
          error_message = parse_tree['error']
          if 'Timeout' in error_message:
            print(f'dgw_parser.py -i {row.institution} -ra {row.requirement_id} -ti 1800',
                  file=reruns)
          print(f'{row.institution} {row.requirement_id} {error_message}')
      print('# end', file=reruns)

  if args.keys:
    # Explore what keys appear where in the parse_tree
    Key = namedtuple('KEY', 'institution requirement_id block_type block_value')
    cursor.execute("""
    select institution, requirement_id, block_type, block_value, parse_tree
      from requirement_blocks
     where period_stop ~* '^9'
       and block_type in ('MAJOR', 'MINOR', 'CONC')
       and parse_tree->'error' is null
  order by institution, block_type, block_value
    """)

    print(f'{cursor.rowcount} blocks')
    parse_trees = dict()
    for row in cursor.fetchall():
      key = Key._make([row.institution, row.requirement_id, row.block_type, row.block_value])
      parse_trees[key] = row.parse_tree

    print('Process Trees')
    # Number of dicts per header/body list
    header_lengths = defaultdict(int)
    body_lengths = defaultdict(int)

    # Frequency distributions of keys in header/body dicts
    header_counts = defaultdict(int)
    body_counts = defaultdict(int)
    for parse_tree in parse_trees.values():
      try:
        header_list = parse_tree['header_list']
        body_list = parse_tree['body_list']

        header_lengths[len(header_list)] += 1
        body_lengths[len(body_list)] += 1

        for header_dict in header_list:
          for header_key in header_dict.keys():
            header_counts[header_key] += 1
        for body_dict in body_list:
          for body_key in body_dict.keys():
            body_counts[body_key] += 1
      except KeyError as ke:
        print(key.institution, key.requirement_id, ke, file=sys.stderr)

    print('Num Keys to CSV')
    all_lengths = set(header_lengths.keys()).union(body_lengths.keys())
    with open('Num_Keys.csv', 'w') as csv_file:
      print('Num Keys, Header, Body', file=csv_file)
      for length in sorted(all_lengths):
        print(f'{length:3},{header_lengths[length]:4}, {body_lengths[length]:4}', file=csv_file)

    print('Header Counts')
    for header_key in sorted(header_counts.keys()):
      print(f'  {header_key:20}: {header_counts[header_key]:8,}')
    print('Body Counts')
    for body_key in sorted(body_counts.keys()):
      print(f'  {body_key:20}: {body_counts[body_key]:8,}')
