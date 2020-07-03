#! /usr/bin/env python3
""" This is the entry point for processing a requirement block during development.

    Use command line args to select a block from the db, then parse it, create a DGW_Processor to
    process nodes in the parse tree, and walk the parse tree. The DGW_Processor object will pick up
    the pieces.
"""


from datetime import datetime
from typing import List, Set, Dict, Tuple, Optional, Union

import os
import re
import sys

import argparse
import inspect
import logging
import traceback

from io import StringIO

from collections import namedtuple
from urllib import parse

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener

from pgconnection import PgConnection

from templates import *

from dgw_processor import DGW_Processor
from dgw_logger import DGW_Logger
from dgw_filter import filter

# Module initialization
# -------------------------------------------------------------------------------------------------
DEBUG = os.getenv('DEBUG_PARSER')

if not os.getenv('HEROKU'):
  logging.basicConfig(filename='Logs/antlr.log',
                      format='%(asctime)s %(message)s',
                      level=logging.DEBUG)

# Lists of tuples of these types get added to lists for the Head and Body sections.
Requirement = namedtuple('Requirement', 'keyword, value, text, course')
ShareList = namedtuple('ShareList', 'keyword text share_list')

# Used for lists of active courses found for particular scribed discipline-catalog_number pairs.
CourseList = namedtuple('CourseList',
                        'scribed_courses list_type customizations exclusions '
                        'active_courses attributes')

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
def dgw_parser(institution, block_type, block_value, period='current', do_parse=False):
  """  Creates a ReqBlockInterpreter, which will include a json representation of requirements.
       For now, it returns an html string telling what it was able to extract from the requirement
       text.
       The period argument can be 'current', 'latest', or 'all', which will be picked out of the
       result set for 'all'
  """
  if DEBUG:
    print(f'*** dgw_parser({institution}, {block_type}, {block_value}. {period})')
  conn = PgConnection()
  cursor = conn.cursor()
  query = """
    select requirement_id, title, period_start, period_stop, requirement_text
    from requirement_blocks
    where institution ~* %s
      and block_type = %s
      and block_value = %s
    order by period_stop desc
  """
  cursor.execute(query, (institution, block_type.upper(), block_value.upper()))
  # Sanity Check
  assert cursor.rowcount > 0, f'<h1 class="error">No Requirements Found</h1><p>{cursor.query}</p>'
  return_html = ''
  for row in cursor.fetchall():
    if period == 'current' and row.period_stop != '99999999':
      return f"""<h1 class="error">“{row.title}” is not a currently offered {block_type}
                 at {institution}.</h1>
              """
    # Filter out everything after END.
    # For parsing, also filter out "hide" things, but leave them in for display purposes.
    text_to_parse = filter(row.requirement_text)
    text_to_show = filter(row.requirement_text, remove_hide=False)
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
      print('Parsing ...')
      dgw_logger = DGW_Logger(institution, block_type, block_value, row.period_stop)

      input_stream = InputStream(text_to_parse)
      lexer = ReqBlockLexer(input_stream)
      lexer.removeErrorListeners()
      lexer.addErrorListener(dgw_logger)
      token_stream = CommonTokenStream(lexer)
      parser = ReqBlockParser(token_stream)
      parser.removeErrorListeners()
      parser.addErrorListener(dgw_logger)

      try:
        print('Walking ...')
        walker = ParseTreeWalker()
        tree = parser.req_block()
        walker.walk(processor, tree)
      except Exception as e:
        if DEBUG:
          exc_type, exc_value, exc_traceback = sys.exc_info()
          print(f'{exc_type.__name__}: {exc_value}')
          traceback.print_tb(exc_traceback, limit=30, file=sys.stdout)
        msg_body = f"""College: {processor.institution}
                       Block Type: {processor.block_type}
                       Block Value: {processor.block_value}
                       Catalog: {processor.catalog_years.catalog_type}
                       Catalog Years: {processor.catalog_years.text}
                       Error: {e}"""
        msg_body = parse.quote(re.sub(r'\n\s*', r'\n', msg_body))
        email_link = f"""
        <a href="mailto:cvickery@qc.cuny.edu?subject=DGW%20Parser%20Failure&body={msg_body}"
           class="button">report this problem (optional)</a>"""

        return_html = (f"""<div class="error-box">
                          <p class="error">Currently unable to interpret this block completely.</p>
                          <p class="error">Internal Error Message: “<em>{e}</em>”</p>
                          <p>{email_link}</p></div>"""
                       + return_html)
    return_html += processor.html

    if period == 'current' or period == 'recent':
      break
  conn.close()
  return return_html


# main()
# =================================================================================================
# Feed requirement_block(s) to dgw_parser() for testing
if __name__ == '__main__':

  # Command line args
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-f', '--format')
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-a', '--development', action='store_true', default=False)

  # Parse args and handle default list of institutions
  args = parser.parse_args()

  for institution in args.institutions:
    institution = institution.upper() + ('01' * (len(institution) == 3))
    for block_type in args.block_types:
      for block_value in args.block_values:
        print(institution, block_type, block_value)
        html = dgw_parser(institution, block_type, block_value, do_parse=True)
        if args.debug:
          print(html)
