#! /usr/local/bin/python3
""" This is like dgw_processor.py, only different.
    Instead of walking the tree and triggering callbacks. explore the structure of the tree.
"""
import os
import re
import sys
import argparse
import json
import resource
import traceback

from enum import IntEnum

# from htmlificization import to_html

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockVisitor import ReqBlockVisitor

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from dgw_filter import dgw_filter
from pgconnection import PgConnection
from psycopg2 import Binary

from dgw_handlers import dispatch
from dgw_utils import build_course_list,\
    catalog_years,\
    class_name,\
    class_or_credit,\
    colleges,\
    context_path,\
    expression_terminals,\
    get_number

DEBUG = os.getenv('DEBUG_PROCESSOR')
LOG_CONTEXT_PATH = os.getenv('LOG_CONTEXT_PATH')

# resource.setrlimit(resource.RLIMIT_STACK, ((resource.RLIM_INFINITY, resource.RLIM_INFINITY)))
sys.setrecursionlimit(10**6)


# dgw_parser()
# =================================================================================================
def dgw_parser(institution, block_type, block_value, period='all', update_db=True):
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
  assert fetch_cursor.rowcount > 0, f'No Requirements Found\n{fetch_cursor.query}'
  num_rows = fetch_cursor.rowcount
  num_updates = 0
  for row in fetch_cursor.fetchall():
    print(f'{institution} {row.requirement_id} {block_type} {block_value} {row.title}',
          file=sys.stderr)
    if period == 'current' and row.period_stop != '99999999':
      return f"""<h1 class="error">“{row.title}” is not a currently offered {block_type}
                 at {institution}.</h1>
              """
    # Filter out everything after END.
    # For parsing, also filter out "hide" things, but leave them in for display purposes.
    text_to_parse = dgw_filter(row.requirement_text)
    text_to_show = dgw_filter(row.requirement_text, remove_hide=False)
    # processor = DGW_Processor(institution,
    #                           row.requirement_id,
    #                           block_type,
    #                           block_value,
    #                           row.title,
    #                           row.period_start,
    #                           row.period_stop,
    #                           text_to_show)

    # Default behavior is just to show the scribe block(s), and not to try parsing them in real
    # time. (But during development, that can be useful for catching coding errors.)

    # dgw_logger = DGW_Logger(institution, block_type, block_value, row.period_stop)

    input_stream = InputStream(text_to_parse)
    lexer = ReqBlockLexer(input_stream)
    # lexer.removeErrorListeners()
    # lexer.addErrorListener(dgw_logger)
    token_stream = CommonTokenStream(lexer)
    parser = ReqBlockParser(token_stream)
    # parser.removeErrorListeners()
    # parser.addErrorListener(dgw_logger)
    tree = parser.req_block()

    head_list = []
    head_ctx = tree.head()
    if head_ctx:
      for child in head_ctx.getChildren():
        obj = dispatch(child, institution, 'head')
        if obj != {}:
          head_list.append(obj)

    body_list = []
    body_ctx = tree.body()
    if body_ctx:
      for child in body_ctx.getChildren():
        obj = dispatch(child, institution, 'body')
        if obj != {}:
          body_list.append(obj)

    if update_db:
      update_cursor.execute(f"""
update requirement_blocks set head_objects = %s, body_objects = %s
where institution = '{row.institution}'
and requirement_id = '{row.requirement_id}'
""", (json.dumps(head_list), json.dumps(body_list)))
    if period == 'current' or period == 'latest':
      break
  conn.commit()
  conn.close()
  return (head_list, body_list)


# __main__
# =================================================================================================
# Create DGW_Processor objects for testing
if __name__ == '__main__':
  """ You can parse a block or a list of blocks from here.
      But if you just want to update the html for the blocks you select, omit the --parse option
  """
  # Command line args
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-f', '--format')
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-n', '--no_update_db', action='store_false')
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])

  # Parse args
  args = parser.parse_args()

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
      if args.block_values[0] == 'ALL':
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
          continue
        print(f'{institution_count} / {num_institutions}; {types_count} / {num_types}; '
              f'{values_count} / {num_values}', file=sys.stderr)
        head_list, body_list = dgw_parser(institution,
                                          block_type.upper(),
                                          block_value,
                                          period='latest', update_db=args.no_update_db)

#         if args.show_html:
#           html = """
# <html>
#   <head>
#     <style>
#       details {
#         margin: 0.1em;
#         padding: 0.25em;
#         border: 1px solid green;
#       }
#     </style>
# """
#           html += f"""
#   </head>
#   <body>
#     <h2>HEAD</h2>
#       {to_html(head_list)}
#     <h2>BODY</h2>
#       {to_html(body_list)}
#   </body>
# </html>
#         """
#           print(html)
