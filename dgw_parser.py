#! /usr/local/bin/python3
""" Generate parse trees for Scribe Blocks.
"""
import argparse
import json
import os
import re
import signal
import sys
import time

from contextlib import contextmanager
from collections import namedtuple
from pprint import pprint

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockVisitor import ReqBlockVisitor

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from pgconnection import PgConnection
# Need psycopg for error handling
import psycopg

from quarantine_manager import QuarantineManager
from dgw_filter import dgw_filter
from dgw_handlers import dispatch
from catalogyears import catalog_years

DEBUG = os.getenv('DEBUG_PARSER')

sys.setrecursionlimit(10**6)

quarantined_dict = QuarantineManager()


# Parser Exceptions: syntax errors and timeouts
# -------------------------------------------------------------------------------------------------
class DGWError(Exception):
  pass


# Replacement for ANTLR Error listener
class DGW_ErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise DGWError(f'Syntax Error on line {line}, column {column}')

    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        pass  # print(f'Ambiguity between {startIndex} and {stopIndex}')

    def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex, conflictingAlts,
                                    configs):
        pass  # print(f'AttemptingFullContext between {startIndex} and {stopIndex}')

    def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
        pass  # print(f'ContextSensitivity between {startIndex} and {stopIndex}')


# Timeout manager
@contextmanager
def timeout_manager(seconds):

  def alarm_handler(signum, frame):
    suffix = '' if seconds == 1 else 's'
    raise DGWError(f'Timeout after {seconds} second{suffix}')

  signal.signal(signal.SIGALRM, alarm_handler)
  signal.alarm(seconds)

  # Generator for with statement
  try:
    yield
  finally:
    signal.alarm(0)


# dgw_parser()
# =================================================================================================
def dgw_parser(institution: str, block_type: str = None, block_value: str = None,
               period_range='current', update_db=True, progress=False,
               do_pprint=False, requirement_id=None, do_quarantined=False, timelimit=30) -> tuple:
  """ For each matching Scribe Block, parse the block and generate lists of JSON objects from it.

       The period_range argument can be 'all', 'current', or 'latest', with the latter two being
       picked out of the result set for 'all'. If there is more than one block in the selected
       range, all will be updated in the db, but only the oldest one’s header and body lists will be
       returned.
  """
  assert requirement_id is not None or (block_type is not None and block_value is not None)
  if DEBUG:
    print(f'*** dgw_parser({institution=}, {block_type=}, {block_value=}, {period_range=}, '
          f'{update_db=}, {progress=}, {do_pprint=}, {requirement_id=}, {do_quarantined=}, '
          f'{timelimit=})', file=sys.stderr)

  conn = PgConnection()
  fetch_cursor = conn.cursor()
  update_cursor = conn.cursor()

  if requirement_id is not None:
    fetch_cursor.execute("""
    select institution, requirement_id, title, period_start, period_stop, requirement_text
      from requirement_blocks
     where institution = %s
       and requirement_id = %s
    """, (institution, requirement_id))
  else:
    query = """
      select institution, requirement_id, title, period_start, period_stop, requirement_text
      from requirement_blocks
      where institution = %s
        and block_type = %s
        and block_value = %s
        and period_stop ~* '^\\d'
      order by period_stop desc
    """
    fetch_cursor.execute(query, (institution, block_type, block_value))

  # Sanity Check
  if fetch_cursor.rowcount < 1:
    conn.close()
    raise ValueError(f'Error: No Requirements Found\n{fetch_cursor.query}')

  for row in fetch_cursor.fetchall():
    augmented_tree = {'header_list': [], 'body_list': []}

    # Manage quarantined blocks
    is_quarantined = False
    if quarantined_dict.is_quarantined((institution, row.requirement_id)):
      if do_quarantined:
        is_quarantined = True
      else:
        if progress:
          print(': Quarantined.')
        msg = f'Quarantined: {quarantined_dict.explanation((institution, row.requirement_id))}'
        augmented_tree['error'] = msg
        update_cursor.execute(f"""
        update requirement_blocks set parse_tree = %s
        where institution = '{row.institution}'
        and requirement_id = '{row.requirement_id}'
        """, (json.dumps(augmented_tree), ))
        # There may be non-quarantined blocks that match the requested period range
        continue

    if period_range == 'current' and not row.period_stop.startswith('9'):
      if progress:
        print(f' Skipping: not current.')
      # If the first block returned does not match the period range, no other ones will
      break

    catalog_years_text = catalog_years(row.period_start, row.period_stop).text
    if progress:
      print(f' ({catalog_years_text})', end='')
      sys.stdout.flush()

    # All processing for a requirement_block must complete within timelimit seconds. If not, the
    # returned augmented tree will contain an 'error' key and empty header/body lists.
    with timeout_manager(timelimit):
      start_time = time.time()
      try:
        # Filter out everything after END, plus hide-related tokens (but not hidden content).
        text_to_parse = dgw_filter(row.requirement_text)
        if DEBUG:
          debug_file = open('./debug', 'w')
          print(f'*** SCRIBE BLOCK ***\n{text_to_parse}', file=debug_file)
        # Generate the parse tree from the Antlr4 parser generator.
        input_stream = InputStream(text_to_parse)
        lexer = ReqBlockLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = ReqBlockParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(DGW_ErrorListener())
        parse_tree = parser.req_block()

        # Walk the header and body parts of the parse tree, interpreting the parts to be saved.
        header_list = []
        if DEBUG:
          print('\n*** PARSE HEAD ***', file=debug_file)

        head_ctx = parse_tree.header()
        if head_ctx:
          for child in head_ctx.getChildren():
            obj = dispatch(child, institution, row.requirement_id)
            if obj != {}:
              header_list.append(obj)

        body_list = []
        if DEBUG:
          print('\n*** PARSE BODY ***', file=debug_file)
        body_ctx = parse_tree.body()
        if body_ctx:
          for child in body_ctx.getChildren():
            obj = dispatch(child, institution, row.requirement_id)
            if obj != {}:
              body_list.append(obj)

        augmented_tree['header_list'] = header_list
        augmented_tree['body_list'] = body_list
        elapsed_time = round((time.time() - start_time), 3)
        if update_db:
          try:
            update_cursor.execute(f"""
            update requirement_blocks set parse_tree = %s, dgw_seconds = %s
            where institution = '{row.institution}'
            and requirement_id = '{row.requirement_id}'
            """, (json.dumps(augmented_tree), elapsed_time))

          # Deal with giant parse trees that exceed Postgres limit for jsonb data
          except psycopg.errors.ProgramLimitExceeded:
            with open('tree_to_large.log', 'a') as tree_too_large:
              print(f'\n{row.institution} {row.requirement_id}\n--------------'
                    f'JSON tree is {len(json.dumps(augmented_tree)):,} bytes', file=tree_too_large)
              print(augmented_tree, file=tree_too_large)
            err_msg = 'Parse tree too large for database'
            if progress:
              print(f': {err_msg}*')
            augmented_tree = {'error': err_msg, 'header_list': [], 'body_list': []}
            update_cursor.execute(f'rollback')
            update_cursor.execute(f"""
            update requirement_blocks set parse_tree = %s
            where institution = '{row.institution}'
            and requirement_id = '{row.requirement_id}'
            """, (json.dumps(augmented_tree), ))
            continue

        if is_quarantined:
          # Quarantined block now parses without error
          del quarantined_dict[(row.institution, row.requirement_id)]

        if progress:
          # End the progress line
          print('.')

        if DEBUG:
          print('\n*** HEADER LIST ***', file=debug_file)
          pprint(header_list, stream=debug_file)
          print('\n*** BODY LIST ***', file=debug_file)
          pprint(body_list, stream=debug_file)

      except Exception as err:
        print(f'{row.institution} {row.requirement_id}: {err}', file=sys.stderr)
        if progress:
          print('*')  # instead of a period.
        if is_quarantined:
          explanation = quarantined_dict.explanation((row.institution, row.requirement_id))
          augmented_tree['error'] = f'Quarantined: {explanation}'
        else:
          augmented_tree['error'] = str(err)
        if update_db:
          update_cursor.execute(f"""
          update requirement_blocks set parse_tree = %s
          where institution = '{row.institution}'
          and requirement_id = '{row.requirement_id}'
          """, (json.dumps(augmented_tree), ))
          continue

    if period_range == 'current' or period_range == 'latest':
      break

  conn.commit()
  conn.close()
  return augmented_tree


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
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-np', '--progress', action='store_false')
  parser.add_argument('-p', '--period', choices=['all', 'current', 'latest'], default='current')
  parser.add_argument('-q', '--do_quarantined', action='store_true')
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-ti', '--timelimit', type=int, default=30)
  parser.add_argument('-nu', '--update_db', action='store_false')

  # Parse args
  args = parser.parse_args()
  if args.requirement_id:
    institution = args.institutions[0].strip('10').upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')
    requirement_id = f'RA{int(requirement_id):06}'

    if args.progress:
      conn = PgConnection()
      cursor = conn.cursor()
      cursor.execute(f"""
                      select block_type, block_value
                        from requirement_blocks
                       where institution = %s
                         and requirement_id = %s
                       """, (institution, requirement_id))
      row = cursor.fetchone()
      print(f'{institution} {requirement_id} {row.block_type:6} {row.block_value:8} {args.period}',
            end='')
      sys.stdout.flush()
    parse_tree = dgw_parser(institution,
                            'block_type',   # Not used with requirement_id
                            'block_value',  # Not used with requirement_id
                            period_range=args.period,
                            progress=args.progress,
                            update_db=args.update_db,
                            requirement_id=requirement_id,
                            do_quarantined=args.do_quarantined,
                            timelimit=args.timelimit)
    # When not updating the db (i.e., during debugging), display the result as a web page.
    if not args.update_db:
      if 'error' in parse_tree.keys():
        err_msg = parse_tree['error']
        html = f'<h1 class="error">Error: {err_msg}</h1>'
      else:
        html = ''
      html += to_html(parse_tree['header_list'], is_head=True)
      html += to_html(parse_tree['body_list'], is_body=True)
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

      conn = PgConnection()
      cursor = conn.cursor()
      for block_value in block_values:
        values_count = 0
        cursor.execute(f"""
        select requirement_id, period_stop
          from requirement_blocks
         where institution = %s
           and block_type = %s
           and block_value = %s
        order by period_stop desc
        """, (institution, block_type, block_value))
        num_values = cursor.rowcount
        for row in cursor.fetchall():
          requirement_id = row.requirement_id
          period_stop = row.period_stop
          if args.period.lower() == 'current' and not period_stop.startswith('9'):
            break
          if args.period.lower() == 'latest' and values_count == 1:
            break
          values_count += 1
          if block_value.isnumeric() or block_value.startswith('MHC'):
            # print(f'Ignoring {institution} {requirement_id} {block_type} {block_value}')
            continue
          if args.progress:
            print(f'{institution_count:2} / {num_institutions:2};  {types_count} / {num_types}; '
                  f'{values_count:3} / {num_values:3} {institution} {requirement_id} {block_type:6}'
                  f' {block_value:8} {args.period}', end='')
            sys.stdout.flush()
          parse_tree = dgw_parser(institution,
                                  block_type.upper(),
                                  block_value,
                                  period_range=args.period,
                                  update_db=args.update_db,
                                  progress=args.progress,
                                  requirement_id=requirement_id,
                                  do_quarantined=args.do_quarantined,
                                  timelimit=args.timelimit)
