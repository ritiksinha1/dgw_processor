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
from ReqBlockListener import ReqBlockListener

trans_dict = dict()
for c in range(13, 31):
  trans_dict[c] = None

trans_table = str.maketrans(trans_dict)


def classes_or_credits(ctx):
  """
  """
  classes_credits = ctx.CREDITS()
  if classes_credits is None:
    classes_credits = ctx.CLASSES()
  return str(classes_credits).lower()


def build_course_list(ctx):
  """ INFROM? (SYMBOL | WILDSYMBOL) (NUMBER | RANGE | WILDNUMBER) (AND  ((SYMBOL NUMBER) | NUMBER))*
      INFROM? (SYMBOL | WILDSYMBOL) (NUMBER | RANGE | WILDNUMBER) (OR  ((SYMBOL NUMBER) | NUMBER))*
  """
  if ctx is None:
    return
  print(ctx.INFROM())
  print(ctx.SYMBOL(), ctx.WILDSYMBOL(),)
  print(ctx.NUMBER(), ctx.RANGE(), ctx.WILDNUMBER())


class ReqBlockInterpreter(ReqBlockListener):
  def __init__(self, block_type, block_value, title):
    self.block_type = block_type.lower()
    self.block_value = block_value
    self.title = title
    if self.block_type == 'conc':
      self.block_type = 'concentration'

  def enterMinres(self, ctx):
    """ MINRES NUMBER (CREDITS | CLASSES)
    """
    classes_credits = classes_or_credits(ctx)
    # print(inspect.getmembers(ctx))
    if float(str(ctx.NUMBER())) == 1:
      classes_credits = classes_credits.strip('es')
    print(f'At least {ctx.NUMBER()} {str(classes_credits).lower()} must be completed in residency.')

  def enterNumcredits(self, ctx):
    """ NUMBER CREDITS (and_courses | or_courses)?
    """
    print('and_courses', ctx.and_courses())
    print('or_courses: ', ctx.or_courses())
    print(f'This {self.block_type} requires {ctx.NUMBER()} credits.')

  def enterMaxcredits(self, ctx):
    """ MAXCREDITS NUMBER (and_courses | or_courses)
    """
    build_course_list(ctx.and_courses())
    build_course_list(ctx.or_courses())
    print('enterMaxcredits() here', ctx.NUMBER())

  def enterMaxpassfail(self, ctx):
    """ MAXPASSFAIL NUMBER (CREDITS | CLASSES) (TAG '=' SYMBOL)?
    """
    print('enterMaxpassfail() here')


# main()
# -------------------------------------------------------------------------------------------------
def main(req_text, block_type, block_value, title):
  """  Mainly, this is the main testing thing.
  """
  input_stream = InputStream(req_text)
  lexer = ReqBlockLexer(input_stream)
  token_stream = CommonTokenStream(lexer)
  parser = ReqBlockParser(token_stream)
  interpreter = ReqBlockInterpreter(block_type, block_value, title)
  walker = ParseTreeWalker()
  tree = parser.req_text()
  walker.walk(interpreter, tree)


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
            main(requirement_text, type, value, row.title)
