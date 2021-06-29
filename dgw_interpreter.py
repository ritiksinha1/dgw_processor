#! /usr/local/bin/python3
""" This module replaces dgw_processor.py.
    Instead of walking the parse tree and triggering callbacks, this module explores the tree
    directly.
"""
import os
import re
import sys
import argparse
import json

from pprint import pprint

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockVisitor import ReqBlockVisitor

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from pgconnection import PgConnection
from psycopg2 import Binary

from dgw_filter import dgw_filter
from dgw_handlers import dispatch
from dgw_utils import catalog_years

DEBUG = os.getenv('DEBUG_INTERPRETER')

sys.setrecursionlimit(10**6)


# dgw_interpreter()
# =================================================================================================
def dgw_interpreter(institution: str, block_type: str, block_value: str,
                    period_range='current', update_db=True, verbose=False,
                    do_pprint=False) -> tuple:
  """ For each matching Scribe Block, parse the block and generate lists of JSON objects from it.

       The period_range argument can be 'all', 'current', or 'latest', with the latter two being
       picked out of the result set for 'all'. If there is more than one block in the selected
       range, all will be updated in the db, but only the oldest one’s header and body lists will be
       returned.
  """

  if DEBUG:
    print(f'*** dgw_interpreter({institution}, {block_type}, {block_value}, {period_range})',
          file=sys.stderr)
  conn = PgConnection()
  fetch_cursor = conn.cursor()
  update_cursor = conn.cursor()
  query = """
    select institution, requirement_id, title, period_start, period_stop, requirement_text
    from requirement_blocks
    where institution = %s
      and block_type = %s
      and block_value = %s
    order by period_stop desc
  """
  fetch_cursor.execute(query, (institution, block_type, block_value))
  # Sanity Check
  if fetch_cursor.rowcount < 1:
    print(f'No Requirements Found\n{fetch_cursor.query}', file=sys.stderr)
    return (None, None)

  num_rows = fetch_cursor.rowcount
  num_updates = 0
  for row in fetch_cursor.fetchall():
    if verbose:
      print(f'{institution} {row.requirement_id} {block_type} {block_value} ',
            end='',
            file=sys.stderr)
      if period_range == 'current' and row.period_stop != '99999999':
        print(f'Not currently offered.', end='', file=sys.stderr)
      else:
        print(catalog_years(row.period_start, row.period_stop).text, end='', file=sys.stderr)
      print(file=sys.stderr)

    # Filter out everything after END, plus hide-related tokens (but not hidden content).
    text_to_parse = dgw_filter(row.requirement_text)
    with open('./debug', 'w') as debug_file:
      if do_pprint:
        print('*** SCRIBE BLOCK ***', file=debug_file)
        print(text_to_parse, file=debug_file)

      # Generate the parse tree from the Antlr4 parser generator.
      input_stream = InputStream(text_to_parse)
      lexer = ReqBlockLexer(input_stream)
      token_stream = CommonTokenStream(lexer)
      parser = ReqBlockParser(token_stream)
      parse_tree = parser.req_block()

      # Walk the head and body parts of the parse tree, interpreting the parts to be saved.
      header_list = []
      if DEBUG:
        print('\n*** PARSE HEAD ***', file=sys.stderr)
      head_ctx = parse_tree.head()
      if head_ctx:
        for child in head_ctx.getChildren():
          obj = dispatch(child, institution, row.requirement_id)
          if obj != {}:
            header_list.append(obj)

      body_list = []
      if DEBUG:
        print('\n*** PARSE BODY ***', file=sys.stderr)
      body_ctx = parse_tree.body()
      if body_ctx:
        for child in body_ctx.getChildren():
          obj = dispatch(child, institution, row.requirement_id)
          if obj != {}:
            body_list.append(obj)

      if update_db:
        update_cursor.execute(f"""
  update requirement_blocks set header_list = %s, body_list = %s
  where institution = '{row.institution}'
  and requirement_id = '{row.requirement_id}'
  """, (json.dumps(header_list), json.dumps(body_list)))

      print('*** HEADER LIST ***', file=debug_file)
      pprint(header_list, stream=debug_file)
      print('*** BODY LIST ***', file=debug_file)
      pprint(body_list, stream=debug_file)

    if period_range == 'current' or period_range == 'latest':
      break
  conn.commit()
  conn.close()

  return (header_list, body_list)


# __main__
# =================================================================================================
# Select Scribe Blocks for parsing
if __name__ == '__main__':
  """ You can select blocks by institutions, block_types, block_values, and period from here.
      By default, the requirement_blocks table's head_objects and body_objects fields are updated
      for each block parsed.
  """
  # Command line args
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-np', '--progress', action='store_false')
  parser.add_argument('-p', '--period', choices=['all', 'current', 'latest'], default='current')
  parser.add_argument('-pp', '--pprint', action='store_true')
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-nu', '--update_db', action='store_false')
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])

  # Parse args
  args = parser.parse_args()
  if args.requirement_id:
    institution = args.institutions[0].strip('10').upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')
    requirement_id = f'RA{int(requirement_id):06}'
    # Look up the block type and value
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f'select block_type, block_value from requirement_blocks'
                   f"  where institution = '{institution}'"
                   f"    and requirement_id = '{requirement_id}'")
    assert cursor.rowcount == 1, (f'Found {cursor.rowcount} block_type/block_value pairs '
                                  f'for {institution} {requirement_id}')
    block_type, block_value = cursor.fetchone()
    conn.close()
    print(f'{institution} {requirement_id} {block_type} {block_value} {args.period}',
          file=sys.stderr)
    header_list, body_list = dgw_interpreter(institution,
                                             block_type,
                                             block_value,
                                             period_range=args.period,
                                             update_db=args.update_db)
    if not args.update_db:
      html = to_html(header_list, is_head=True)
      html += to_html(body_list, is_body=True)
      print(html)
    exit()

  if args.institutions[0] == 'all':
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute('select code from cuny_institutions')
    institutions = [row.code for row in cursor.fetchall()]
    conn.close()
  else:
    institutions = args.institutions

  num_institutions = len(institutions)
  institution_count = 0
  for institution in institutions:
    institution_count += 1
    institution = institution.upper() + ('01' * (len(institution) == 3))
    if args.block_types[0] == 'all':
      args.block_types = ['DEGREE', 'MAJOR', 'MINOR', 'CONC', 'OTHER']
    types_count = 0
    num_types = len(args.block_types)
    for block_type in args.block_types:
      block_type = block_type.upper()
      types_count += 1
      if args.block_values[0].lower() == 'all':
        conn = PgConnection()
        cursor = conn.cursor()
        cursor.execute('select distinct block_value from requirement_blocks '
                       'where institution = %s and block_type = %s'
                       'order by block_value', (institution, block_type))
        block_values = [row.block_value for row in cursor.fetchall()]
        conn.close()
      else:
        block_values = [value.upper() for value in args.block_values]

      num_values = len(block_values)
      values_count = 0
      for block_value in block_values:
        values_count += 1
        if block_value.isnumeric() or block_value.startswith('MHC'):
          continue
        if args.progress:
          print(f'{institution_count:2} / {num_institutions:2};  {types_count} / {num_types}; '
                f'{values_count:3} / {num_values:3} ', end='', file=sys.stderr)
        header_list, body_list = dgw_interpreter(institution,
                                                 block_type.upper(),
                                                 block_value,
                                                 period_range=args.period,
                                                 update_db=args.update_db,
                                                 verbose=args.progress,
                                                 do_pprint=args.pprint)
        if args.debug:
          print(f'{header_list=}\n{body_list=}', file=sys.stderr)
