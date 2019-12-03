#! /usr/local/bin/python3

import inspect
from pprint import pprint

import argparse
import sys
from io import StringIO

import psycopg2
from psycopg2.extras import NamedTupleCursor

from antlr4 import *
from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockVisitor import ReqBlockVisitor

trans_dict = dict()
for c in range(13, 31):
  trans_dict[c] = None

trans_table = str.maketrans(trans_dict)


class ReqBlockInterpreter(ReqBlockVisitor):
  def visitMinres(self, ctx):
    print(inspect.getmembers(ctx))
    print(f'At least {ctx.NUMBER()} credits must be completed in residency.')

  def visitNumcredits(self, ctx):
    print(f'This major requires {ctx.NUMBER()} credits.')


# main()
# -------------------------------------------------------------------------------------------------
def main(argv):
  """  Mainly, this is the main testing thing.
  """
  input_stream = InputStream(argv)
  lexer = ReqBlockLexer(input_stream)
  token_stream = CommonTokenStream(lexer)
  parser = ReqBlockParser(token_stream)
  tree = parser.req_block()
  interpreter = ReqBlockInterpreter()
  interpreter.visit(tree)
  for child in tree.headers().getChildren():
    pprint(dir(child))
    print('--------------------------------------------------------------------------------------')


if __name__ == '__main__':

  # Command line args
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-f', '--format')
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-t', '--types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-a', '--development', action='store_true', default=False)

  # Parse args and handle default list of institutions
  args = parser.parse_args()
  digits = '0123456789'
  institutions = [f'{i.lower().strip(digits)}' for i in args.institutions]
  types = [f'{t.upper()}' for t in args.types]
  values = [f'{v.upper()}' for v in args.values]
  if args.debug:
    print(f'institutions: {institutions}')
    print(f'types: {types}')
    print(f'values: {values}')

  # Create dict of known colleges
  colleges = dict()
  course_conn = psycopg2.connect('dbname=cuny_courses')
  course_cursor = course_conn.cursor(cursor_factory=NamedTupleCursor)
  course_cursor.execute('select substr(lower(code),0,4) as code, name from institutions')
  for row in course_cursor.fetchall():
    colleges[row.code] = row.name
  course_conn.close()

  # Get the top-level requirements to examine: college, block-type, and/or block value
  conn = psycopg2.connect('dbname=cuny_programs')
  cursor = conn.cursor(cursor_factory=NamedTupleCursor)

  query = """
      select requirement_id, title, requirement_text
      from requirement_blocks
      where institution = %s
        and block_type = %s
        and block_value = %s
        and period_stop = '99999999'
  """
  for institution in institutions:
    for type in types:
      for value in values:
        cursor.execute(query, (institution, type, value))
        if cursor.rowcount == 0:
          print(f'No match for {institution} {type} {value}')
        else:
          for row in cursor.fetchall():
            print(f'{institution}, {type} {value} "{row.title}" {len(row.requirement_text)} chars')
            requirement_text = row.requirement_text\
                                  .translate(trans_table)\
                                  .strip('"')\
                                  .replace('\\r', '\r')\
                                  .replace('\\n', '\n')
            main(requirement_text)
