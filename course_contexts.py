#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?

    The goal is to extract both the context (the label structure) and the specificity (how many
    alternatives there are) for each course.

    Block, blocktype, copy_rules, noncourse, and remarks are all irrelevant for present purposes.
    Specificity depends on the structure of the course_list, the group (and area) structure, and
    conditional factors.

    This code is modeled on htmlificization, and assumes that the header and body lists in the
    database never need to be interpreted unless they are missing.
"""

import os
import sys

from argparse import ArgumentParser
from collections import namedtuple
from pgconnection import PgConnection
from dgw_interpreter import dgw_interpreter
from quarantined_blocks import quarantine_dict

from pprint import pprint
from inspect import currentframe, getframeinfo

DEBUG = os.getenv('DEBUG_CONTEXTS')

Course = namedtuple('Course',
                    'course_id offer_nbr context_path, num_alternatives')


# Context Handlers
# =================================================================================================
def do_course_list(item: dict) -> str:
  """ For a course list, the label gives the requirement name, the length of the list and the
      conjunction determine how many alternatives there are.
  """
  if DEBUG:
    print('*** do_course_list()', file=sys.stderr)
  return_str = ''

  return return_str


def do_group_items(item: dict) -> str:
  """
  """
  if DEBUG:
    print('*** do_group_items()')
  return ''


def do_conditional(item: dict) -> str:
  """
  """
  if DEBUG:
    print('*** do_conditional()')
  return ''


def iter_list(items: list) -> list:
  """
  """
  if DEBUG:
    print(f'*** iterlist({len(items)=})')
  return_list = []
  for value in items:
    if isinstance(value, list):
      return_list += iter_list(value)
    elif isinstance(value, dict):
      return_list += iter_dict(value)
    else:
      print(f'iter_list: Neither list nor dict: {value=} {len(return_list)=}', file=sys.stderr)

  return return_list


def iter_dict(item: dict) -> list:
  """
  """
  if DEBUG:
    print(f'*** iterlist({item.keys()=})')
  return_list = []
  for key, value in item.items():
    if isinstance(value, list):
      return_list += iter_list(value)
    elif isinstance(value, dict):
      return_list += iter_dict(value)
    else:
      print(f'iter_dict: Neither list nor dict: {key=} {value=} {len(return_list)=}',
            file=sys.stderr)

  return return_list


# __main__()
# =================================================================================================
if __name__ == '__main__':
  parser = ArgumentParser('Look up course list contexts')
  parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
  parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
  parser.add_argument('-v', '--block_values', nargs='*', default=['csci-ba'])
  parser.add_argument('-f', '--force', action='store_true', default=False)
  parser.add_argument('-p', '--period', default='current')
  args = parser.parse_args()
  period = args.period.lower()

  # Allowable values for period
  assert period in ['all', 'current']

  with open('./debug', 'w') as debug:
    conn = PgConnection()
    cursor = conn.cursor()
    institutions = [inst.upper().strip('01') for inst in args.institutions]
    for institution in institutions:
      institution = institution + '01'
      block_types = [arg.upper() for arg in args.block_types]
      for block_type in block_types:
        assert block_type in ['MAJOR', 'CONC', 'MINOR']
        block_values = [value.upper() for value in args.block_values]
        if 'ALL' in block_values:
          cursor.execute(f"""
        select distinct block_value
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
        order by block_value
    """)
          block_values = [row.block_value.upper() for row in cursor.fetchall()
                          if not row.block_value.isdigit()
                          and '?' not in row.block_value]
        for block_value in block_values:
          if block_value.startswith('MHC') or block_value.isdigit():
            continue
          cursor.execute(f"""
        select requirement_id, period_stop, requirement_text, header_list, body_list
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
           and block_value ~* '^{block_value}$'
    """)
          for row in cursor.fetchall():
            if (institution, row.requirement_id) in quarantine_dict:
              print(f'{institution}, {row.requirement_id} is quarantined')
              continue
            if period == 'current' and row.period_stop != '99999999':
              continue
            print(f'{institution} {block_type} {block_value} {period}: ', end='')
            header_list, body_list = (row.header_list, row.body_list)
            if (len(header_list) == 0 and len(body_list) == 0) or args.force:
              print(f'[{len(header_list)=}] {args.force=} reinterpret')
              header_list, body_list = dgw_interpreter(institution, block_type, block_value,
                                                       period_range=period)

            print(f'*** {institution} {block_type} {block_value} {period}', file=debug)
            pprint(body_list, stream=debug)
            print('\n', file=debug)

            # Iterate over the body
            pprint(iter_list(body_list))
