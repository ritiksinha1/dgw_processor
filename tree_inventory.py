#! /usr/local/bin/python3

import argparse
import os
import sys

import datetime

from collections import defaultdict, namedtuple
from pprint import pprint

from pgconnection import PgConnection


def find_course_list(parse_tree):
  """ Find a course_list with a label
  """
  global num_course_lists
  if isinstance(parse_tree, list):
    for element in parse_tree:
      if tree := find_course_list(element):
        return tree
  elif isinstance(parse_tree, dict):
    if 'course_list' in parse_tree.keys():
      num_course_lists += 1
      if 'label' in parse_tree.keys():
        return parse_tree
    else:
      for key, value in parse_tree.items():
        find_course_list(value)


if __name__ == '__main__':

  parser = argparse.ArgumentParser('Look at parse tree properties')
  parser.add_argument('-c', '--course_lists', action='store_true')
  parser.add_argument('-k', '--keys', action='store_true')
  parser.add_argument('-ti', '--timeouts', action='store_true')

  args = parser.parse_args()

  conn = PgConnection()
  cursor = conn.cursor()

  if args.timeouts:
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

  if args.keys or args.course_lists:
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

    print(f'{cursor.rowcount:,} parse trees')
    parse_trees = dict()
    for row in cursor.fetchall():
      key = Key._make([row.institution, row.requirement_id, row.block_type, row.block_value])
      parse_trees[key] = row.parse_tree

    print('Process Trees')
    if args.keys:
      # Number of dicts per header/body list
      header_lengths = defaultdict(int)
      body_lengths = defaultdict(int)

      # Frequency distributions of keys in header/body dicts
      header_counts = defaultdict(int)
      body_counts = defaultdict(int)
      for key, parse_tree in parse_trees.items():
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
          # if a block is missing either the header or body list, ignore it for purposes of the
          # inventory.
          print(key.institution, key.requirement_id, ke, file=sys.stderr)

      print('Generate Num_Keys.csv')
      all_lengths = set(header_lengths.keys()).union(body_lengths.keys())
      with open('Num_Keys.csv', 'w') as csv_file:
        print('Num Keys, Header, Body', file=csv_file)
        for length in sorted(all_lengths):
          print(f'{length:3},{header_lengths[length]:4}, {body_lengths[length]:4}', file=csv_file)

      print('Generate Key_Counts.csv')
      all_keys = set(list(header_counts.keys()) + list(body_counts.keys()))
      with open('Key_Counts.csv', 'w') as csv_file:
        print('Key, Header, Body', file=csv_file)
        for key in sorted(all_keys):
          if key in header_counts.keys():
            header_val = header_counts[key]
          else:
            header_val = 0
          if key in body_counts.keys():
            body_val = body_counts[key]
          else:
            body_val = 0
          print(f'{key},{header_val},{body_val}', file=csv_file)

    if args.course_lists:
      # find a course_list that has a label
      print('Look for a course list with a label')
      global num_course_lists
      num_course_lists = 0
      n = 0
      for key, parse_tree in parse_trees.items():
        n += 1
        print(f'  tree {n:5,}\r', end='')
        if course_list := find_course_list(parse_tree):
          exit(f'\n{key}: {course_list}')
      exit(f'\nNot found in {num_course_lists:,} course lists')
