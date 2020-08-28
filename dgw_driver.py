#! /usr/bin/env python3
""" This is the entry point for processing a requirement block.

    Use command line args to select requirement_block(s) from the db, create a DGW_Processor to
    hold information extracted from each block. Convert the requirement block text to html, then
    if the parse argument is set, walk the parse tree, generating additional information to be added
    back to the database along with the html.

    See __main__ for other use cases.
"""


from datetime import datetime
from typing import List, Set, Dict, Tuple, Optional, Union

import os
import re
import sys

import argparse
import inspect
import json
import logging
import traceback

from io import StringIO

from collections import namedtuple
import urllib.parse

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener

from pgconnection import PgConnection

from templates import *

from dgw_processor import DGW_Processor
from dgw_logger import DGW_Logger
from dgw_filter import dgw_filter

# Module initialization
# -------------------------------------------------------------------------------------------------
DEBUG = os.getenv('DEBUG_DRIVER')

if os.getenv('LOG_ANTLR'):
  logging.basicConfig(filename='Logs/antlr.log',
                      format='%(asctime)s %(message)s',
                      level=logging.DEBUG)

# Lists of tuples of these types get added to lists for the Head and Body sections.
Requirement = namedtuple('Requirement', 'keyword, value, text, course')
ShareList = namedtuple('ShareList', 'keyword text share_list')

# Known named fields for WITH clauses
with_named_fields = ['DWAge', 'DWCredits', 'DWCreditType', 'DWCourseNumber', 'DWDiscipline',
                     'DWGradeNumber', 'DWGradeLetter', 'DWGradeType', 'DWLocation', 'DWPassFail',
                     'DWResident', 'DWSchool', 'DWSection', 'DWTer', 'DWTitle', 'DWTransfer',
                     'DWTransferCourse', 'DWTransferSchool', 'DWInprogress', 'DWPreregistered',
                     'DWTermType', 'DWPassed']
# The ones of interest here:
known_with_qualifiers = ['DWPassFail', 'DWResident', 'DWTransfer', 'DWTransferCourse']


# dgw_parser()
# =================================================================================================
def dgw_parser(institution, block_type, block_value, period='all', do_parse=False):
  """ For each matching Scribe Block, create a DGW_Processor to hold the info about it; the
      constructor parses the block and extracts information objects from it, creating a HTML
      representation of the Scribe Block and lists of dicts of the extracted objects, one for the
      head and one for the body of the block.

      Update/replace the HTML Scribe Block and the lists of object in the requirement_blocks table.

       The period argument can be 'current', 'latest', or 'all', which will be picked out of the
       result set for 'all'
  """
  if DEBUG:
    print(f'*** dgw_parser({institution}, {block_type}, {block_value}. {period})', file=sys.stderr)
  if do_parse:
    operation = 'Parsed'
  else:
    operation = 'Updated'
  conn = PgConnection()
  fetch_cursor = conn.cursor()
  update_cursor = conn.cursor()
  query = """
    select requirement_id, title, period_start, period_stop, requirement_text
    from requirement_blocks
    where institution = %s
      and block_type = %s
      and block_value = %s
    order by period_stop desc
  """
  fetch_cursor.execute(query, (institution, block_type, block_value))
  # Sanity Check
  assert fetch_cursor.rowcount > 0, f'No Requirements Found\n{fetch_cursor.query}'
  num_rows = fetch_cursor.rowcount
  num_updates = 0
  for row in fetch_cursor.fetchall():
    if period == 'current' and row.period_stop != '99999999':
      return f"""<h1 class="error">“{row.title}” is not a currently offered {block_type}
                 at {institution}.</h1>
              """
    # Filter out everything after END.
    # For parsing, also filter out "hide" things, but leave them in for display purposes.
    text_to_parse = dgw_filter(row.requirement_text)
    text_to_show = dgw_filter(row.requirement_text, remove_hide=False)
    processor = DGW_Processor(institution,
                              row.requirement_id,
                              block_type,
                              block_value,
                              row.title,
                              row.period_start,
                              row.period_stop,
                              text_to_show)

    # Default behavior is just to show the scribe block(s), and not to try parsing them in real
    # time. (But during development, that can be useful for catching coding errors.)
    if do_parse:
      if DEBUG:
        print('Parsing ...', file=sys.stderr)
      dgw_logger = DGW_Logger(institution, block_type, block_value, row.period_stop)

      input_stream = InputStream(text_to_parse)
      lexer = ReqBlockLexer(input_stream)
      lexer.removeErrorListeners()
      lexer.addErrorListener(dgw_logger)
      token_stream = CommonTokenStream(lexer)
      parser = ReqBlockParser(token_stream)
      parser.removeErrorListeners()
      parser.addErrorListener(dgw_logger)
      tree = parser.req_block()

      try:
        if DEBUG:
          print('Walking ...', file=sys.stderr)
        walker = ParseTreeWalker()
        walker.walk(processor, tree)
      except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f'{exc_type.__name__}: {exc_value}', file=sys.stderr)
        traceback.print_tb(exc_traceback, limit=30, file=sys.stderr)
        # msg_body = f"""College: {processor.institution}
        #                Block Type: {processor.block_type}
        #                Block Value: {processor.block_value}
        #                Catalog: {processor.catalog_years.catalog_type}
        #                Catalog Years: {processor.catalog_years.text}
        #                Error: {e}"""
    requirement_html = re.sub(r'\n\s*', r'\n', processor.html().replace("'", '’'))
    head_objects = json.dumps(processor.sections[1])
    body_objects = json.dumps(processor.sections[2])
    # Add the info to the db
    update_query = f""" update requirement_blocks
                          set requirement_html = '{requirement_html}',
                              head_objects = '{head_objects}',
                              body_objects = '{body_objects}'
                        where institution = '{institution}'
                          and requirement_id = '{row.requirement_id}'
                    """
    update_cursor.execute(update_query)
    num_updates += update_cursor.rowcount
    if DEBUG:
      print(f'\r{operation} {institution} {row.requirement_id}', end='')

    if period == 'current' or period == 'latest':
      break
  conn.commit()
  conn.close()
  if DEBUG:
    print()
  return (num_updates, num_rows)


# __main__
# =================================================================================================
# Feed requirement_block(s) to dgw_parser() for testing
if __name__ == '__main__':
  """ You can parse a block or a list of blocks from here.
      But if you just want to update the html for the blocks you select, omit the --parse option
  """
  # Command line args
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-f', '--format')
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-p', '--parse', action='store_true', default=False)
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])

  # Parse args
  args = parser.parse_args()

  # Parse blocks, or just update requirement_html (and reset object lists)?
  if args.parse:
    operation = 'Parsed'
  else:
    operation = 'Updated'

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
      types_count += 1
      if args.block_values[0] == 'all':
        conn = PgConnection()
        cursor = conn.cursor()
        cursor.execute('select distinct block_value from requirement_blocks '
                       'where institution = %s and block_type = %s'
                       'order by block_value', (institution, block_type))
        block_values = [row.block_value for row in cursor.fetchall()]
        conn.close()
      else:
        block_values = args.block_values

      num_values = len(block_values)
      values_count = 0
      for block_value in block_values:
        values_count += 1
        if block_value.isnumeric() or block_value.startswith('MHC'):
          print(f'Skipping {institution} {block_type} {block_value}')
          continue
        if args.debug:
          print(institution, block_type.upper(), block_value, file=sys.stderr)
        num_updates, num_blocks = dgw_parser(institution,
                                             block_type.upper(),
                                             block_value,
                                             period='latest',
                                             do_parse=args.parse)
        suffix = '' if num_updates == 1 else 's'
        print(f'{institution_count} / {num_institutions}; {types_count} / {num_types}; '
              f'{values_count} / {num_values}: ', end='')
        print(f'{operation} {num_updates} block{suffix} for {institution} {block_type} '
              f'{block_value}')
