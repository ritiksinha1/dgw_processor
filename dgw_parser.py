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
from collections import namedtuple, defaultdict

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockVisitor import ReqBlockVisitor

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

import psycopg
from psycopg.rows import namedtuple_row

from catalogyears import catalog_years
from dgw_filter import dgw_filter
from scriberror import ScribeError
from dgw_handlers import dispatch
from quarantine_manager import QuarantineManager

DEBUG = os.getenv('DEBUG_PARSER')

sys.setrecursionlimit(10**6)

quarantined_dict = QuarantineManager()


# Replacement for ANTLR Error listener
class DGW_ErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise ScribeError(f'Syntax Error on line {line}, column {column}')

    def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
        pass  # print(f'Ambiguity between {startIndex} and {stopIndex}')

    def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex, conflictingAlts,
                                    configs):
        pass  # print(f'AttemptingFullContext between {startIndex} and {stopIndex}')

    def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
        pass  # print(f'ContextSensitivity between {startIndex} and {stopIndex}')


# timeout_manager()
# -------------------------------------------------------------------------------------------------
@contextmanager
def timeout_manager(seconds: int):

  def alarm_handler(signum, frame):
    suffix = '' if seconds == 1 else 's'
    raise ScribeError(f'Timeout after {seconds} second{suffix}')

  signal.signal(signal.SIGALRM, alarm_handler)
  signal.alarm(seconds)

  # Generator for with statement
  try:
    yield
  finally:
    signal.alarm(0)


# parse_block()
# =================================================================================================
def parse_block(institution: str,
                requirement_id: str,
                period_start: str,
                period_stop: str,
                requirement_text: str,
                timelimit=30) -> tuple:
  """ Parse the block and generate the parse_tree for it; update the database.
  """
  if DEBUG:
    print(f'*** parse_block({institution=}, {requirement_id=}, {timelimit=})', file=sys.stderr)

  catalog_years_text = catalog_years(period_start, period_stop).text

  # All processing for a requirement_block must complete within timelimit seconds. If not, the
  # returned augmented tree will contain an 'error' key and empty header/body lists.
  parse_tree = {'header_list': [], 'body_list': []}

  with timeout_manager(timelimit):
    start_time = time.time()
    try:
      # Filter out everything after END, plus hide-related tokens (but not hidden content).
      text_to_parse = dgw_filter(requirement_text)

      # Generate the parse tree from the Antlr4 parser generator.
      input_stream = InputStream(text_to_parse)
      lexer = ReqBlockLexer(input_stream)
      token_stream = CommonTokenStream(lexer)
      parser = ReqBlockParser(token_stream)
      parser.removeErrorListeners()
      parser.addErrorListener(DGW_ErrorListener())
      antlr_tree = parser.req_block()
    except (ScribeError, ValueError) as err:
      print(f'{institution} {requirement_id} ANTLR failure', file=sys.stderr)
      parse_tree['error'] = str(err)

    # Walk the header and body parts of the parse tree, interpreting the parts to be saved.
    if 'error' not in parse_tree.keys():
      try:
        header_list = []
        head_ctx = antlr_tree.header()
        if head_ctx:
          for child in head_ctx.getChildren():
            obj = dispatch(child, institution, requirement_id)
            if obj != {}:
              header_list.append(obj)

        body_list = []
        body_ctx = antlr_tree.body()
        if body_ctx:
          for child in body_ctx.getChildren():
            obj = dispatch(child, institution, requirement_id)
            if obj != {}:
              body_list.append(obj)

        parse_tree['header_list'] = header_list
        parse_tree['body_list'] = body_list
      except Exception as err:
        parse_tree['error'] = str(err)
        print(f'{institution} {requirement_id} DGW failure', file=sys.stderr)

    elapsed_time = round((time.time() - start_time), 3)
    timestamp = time.strftime('%Y-%m-%d %H:%M', time.localtime())
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor() as cursor:
        cursor.execute("""
        update requirement_blocks set parse_tree = %s, dgw_seconds = %s, dgw_timestamp = %s
        where institution = %s
        and requirement_id = %s
        """, (json.dumps(parse_tree), elapsed_time, timestamp, institution, requirement_id))

  return parse_tree


# __main__
# =================================================================================================
# Select Scribe Block(s) for parsing
if __name__ == '__main__':
  """ You can select blocks by institutions, block_types, block_values, and period from here.
      By default, the requirement_blocks table's head_objects and body_objects fields are updated
      for each block parsed.
  """
  # Cache college names
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute('select code, prompt as name from cuny_institutions')
      college_names = {r.code: r.name for r in cursor}
  college_names['SWG01'] = 'Oswego'

  # Command line args
  parser = argparse.ArgumentParser(description='Parse DGW Scribe Blocks')
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-p', '--period', choices=['all', 'current'], default='current')
  parser.add_argument('-q', '--do_quarantined', action='store_true')
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-ti', '--timelimit', type=int, default=180)

  select_clause = """
  select institution,
         requirement_id,
         block_type,
         block_value,
         title,
         period_start,
         period_stop,
         requirement_text
    from requirement_blocks
   """
  # Parse args
  args = parser.parse_args()

  if args.requirement_id:
    # The query has to be for just one institution.
    types_clause = values_clause = period_clause = ''
    institution = args.institutions[0][0:3].upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    requirement_id = f'RA{int(requirement_id):06}'
    institution_clause = (f"where institution = '{institution}' and requirement_id = "
                          f"'{requirement_id}'")

  else:
    # Assemble arguments to select desired blocks
    if args.institutions[0] == 'all':
      institution_clause = "where institution ~* '.*'"
    else:
      institutions = ','.join([f"'{inst[0:3].upper()}01'" for inst in args.institutions])
      institution_clause = f'where institution in ({institutions})'

    # block types
    if args.block_types[0] == 'all':
      args.block_types = ['DEGREE', 'MAJOR', 'MINOR', 'CONC', 'OTHER']
    block_types = ','.join([f"'{value.upper()}'" for value in args.block_types])
    types_clause = f'and block_type in ({block_types})'

    # block values
    if args.block_values[0] == 'all':
      values_clause = ''
    else:
      block_values = ','.join([f"'{value.upper()}'" for value in args.block_values])
      values_clause = f'and block_value in ({block_values})'

    # period
    if args.period.lower() == 'all':
      period_clause = ''
    else:
      period_clause = "and period_stop ~* '^9'"

  query_str = f"""
  {select_clause}
  {institution_clause}
  {types_clause}
  {values_clause}
  {period_clause}
  order by institution, block_type, block_value
  """
  if args.debug:
    print(query_str, file=sys.stderr)

  LongTime = namedtuple('LongTime', 'institution requirement_id block_value time')

  def longtime_factory():
    """ Record max parsing time, by block_type.
    """
    return LongTime._make(['UNK', 'RA000000', 'Unknown', 0])

  longest_times = defaultdict(longtime_factory)
  logfile_name = __file__.replace('.py', '.log')
  with open(logfile_name, 'w') as log_file:
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute(query_str)
        if cursor.rowcount == 0:
          exit('No matching blocks found.')

        process_start = time.time()
        institution_start = process_start
        current_institution = None
        for row in cursor:
          if row.institution != current_institution:
            if current_institution is not None:
              print(f'{college_names[current_institution]}: '
                    f'{(time.time() - institution_start):,.1f} sec',
                    file=log_file)
            current_institution = row.institution
            institution_start = time.time()
          is_quarantined = quarantined_dict.is_quarantined((row.institution, row.requirement_id))
          if is_quarantined and not args.do_quarantined:
            print(f'{row.institution} {row.requirement_id} Quarantined', file=log_file)
            continue

          print(f'\r{cursor.rownumber:6,}/{cursor.rowcount:,} '
                f'{row.institution} {row.requirement_id}', end='')
          parsing_start = time.time()
          parse_tree = parse_block(row.institution,
                                   row.requirement_id,
                                   row.period_start,
                                   row.period_stop,
                                   row.requirement_text,
                                   args.timelimit)
          parsing_time = time.time() - parsing_start
          if parsing_time > longest_times[row.block_type].time:
            longest_times[row.block_type] = LongTime._make([row.institution, row.requirement_id,
                                                            row.block_value, parsing_time])

          try:
            error_msg = parse_tree['error'].strip('\n')
            if 'Timeout' in error_msg:
              print(' Timeout      ', end='')
            elif 'Quarantine' in error_msg:
              print(' Quarantined  ', end='')
            else:
              print(f' Error       ', end='')
            print(f'{row.institution} {row.requirement_id} Error: {error_msg}', file=log_file)

          except KeyError:
            print(f'    OK         ', end='')
            print(f'{row.institution} {row.requirement_id} OK', file=log_file)
    # Report last college
    print(f'{college_names[current_institution]}: {(time.time() - institution_start):,.1f} sec',
          file=log_file)

    min, sec = divmod(time.time() - process_start, 60)
    hr, min = divmod(min, 60)
    print(f'\nTotal time: {int(hr):02}:{int(min):02}:{round(sec):02}\nMax times by block type:\n'
          f'Block Type   Sec Clg Value',
          file=log_file)
    for block_type, value in longest_times.items():
      print(f'{block_type:10} {value.time:5.1f} {value.institution[0:3]} {value.block_value}',
            file=log_file)
