#! /usr/local/bin/python3

import inspect
from pprint import pprint
from typing import List, Set, Dict, Tuple, Optional

import argparse
import sys
from io import StringIO

import psycopg2
from psycopg2.extras import NamedTupleCursor
from collections import namedtuple

from antlr4 import *
from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener

trans_dict = dict()
for c in range(13, 31):
  trans_dict[c] = None

trans_table = str.maketrans(trans_dict)

CourseInfo = namedtuple('CourseInfo', 'institution course_id offer_nbr discipline catalog_number '
                        'title course_status designation attributes')

# Create dict of known colleges
colleges = dict()
course_conn = psycopg2.connect('dbname=cuny_courses')
course_cursor = course_conn.cursor(cursor_factory=NamedTupleCursor)
course_cursor.execute('select substr(lower(code),0,4) as code, name from institutions')
for row in course_cursor.fetchall():
  colleges[row.code] = row.name


def classes_or_credits(ctx) -> str:
  """
  """
  classes_credits = ctx.CREDITS()
  if classes_credits is None:
    classes_credits = ctx.CLASSES()
  return str(classes_credits).lower()


def build_course_list(ctx) -> List[Dict]:
  """ INFROM? class_item (AND class_item)*
      INFROM? class_item (OR class_item)*
  """
  print(f'build_course_list({ctx})')
  course_list = []
  if ctx is None:
    return course_list
  # if ctx.INFROM():
  #   print(f'INFROM: {ctx.INFROM()}')
  for class_item in ctx.class_item():
    if class_item.SYMBOL():
      display_discipline = str(class_item.SYMBOL())
      search_discipline = display_discipline
    if class_item.WILDSYMBOL():
      display_discipline = str(class_item.WILDSYMBOL())
      search_discipline = display_discipline.replace('@', '.*')
    if class_item.NUMBER():
      display_number = str(class_item.NUMBER())
      search_number = display_number
    if class_item.RANGE():
      display_number = str(class_item.RANGE())
      low, high = display_number.split(':')
      search_number = f'>= {low}\' and catalog_number <= \'{high}'
    if class_item.WILDNUMBER():
      display_number = str(class_item.wildnumber)
      search_number = display_number.replace('@', '.*')
    print(display_discipline, display_number)
    course_query = f"""
                      select institution, course_id, offer_nbr, discipline, catalog_number, title,
                             course_status, designation, attributes
                        from courses
                       where institution ~* '{institution}'
                         and discipline ~ '{search_discipline}'
                         and catalog_number ~ '{search_number}'
                    """
    course_cursor.execute(course_query)
    details = []
    details = [CourseInfo._Make(row) for row in cursor.fetchall()]
    course_list.append({'display': f'{display_discipline} {display_number}',
                        'info': tuple(details)})
  pprint(course_list)
  return course_list


def course_list_to_html(courses: List[str]):
  html = ''
  for course in courses:
    html += '<p>course</p>'


class ReqBlockInterpreter(ReqBlockListener):
  def __init__(self, institution, block_type, block_value, title):
    self.institution = institution
    self.block_type = block_type.lower()
    self.block_value = block_value
    self.title = title
    college_name = colleges[institution]
    self.html = f"""<h1>{college_name} {self.title}</h1>
                 """
    if self.block_type == 'conc':
      self.block_type = 'concentration'

  def enterMinres(self, ctx):
    """ MINRES NUMBER (CREDITS | CLASSES)
    """
    classes_credits = classes_or_credits(ctx)
    # print(inspect.getmembers(ctx))
    if float(str(ctx.NUMBER())) == 1:
      classes_credits = classes_credits.strip('es')
    self.html += (f'<p>At least {ctx.NUMBER()} {str(classes_credits).lower()} '
                  f'must be completed in residency.</p>')

  def enterNumcredits(self, ctx):
    """ NUMBER CREDITS (and_courses | or_courses)?
    """
    self.html += (f'<p>This {self.block_type} requires {ctx.NUMBER()} credits.')
    if ctx.and_courses() is not None:
      build_course_list(ctx.and_courses())
    if ctx.or_courses() is not None:
      self.html += course_list_to_html(build_course_list(ctx.or_courses()))

  def enterMaxcredits(self, ctx):
    """ MAXCREDITS NUMBER (and_courses | or_courses)
    """
    print('enterMaxcredits() here')
    print(f'MAXCREDITS: {ctx.MAXCREDITS()}')
    print(f'NUMBER: {ctx.NUMBER()}')
    if ctx.and_courses() is not None:
      build_course_list(ctx.and_courses())
    if ctx.or_courses() is not None:
      build_course_list(ctx.or_courses())

  def enterMaxclasses(self, ctx):
    """ MAXCLASSES NUMBER (and_courses | or_courses)
    """
    print('enterMaxclasses() here')
    print(f'MAXCLASSES: {ctx.MAXCLASSES()}')
    print(f'NUMBER: {ctx.NUMBER()}')
    if ctx.and_courses() is not None:
      build_course_list(ctx.and_courses())
    if ctx.or_courses() is not None:
      build_course_list(ctx.or_courses())

  def enterMaxpassfail(self, ctx):
    """ MAXPASSFAIL NUMBER (CREDITS | CLASSES) (TAG '=' SYMBOL)?
    """
    print('enterMaxpassfail() here')


# dgw_parser()
# -------------------------------------------------------------------------------------------------
def dgw_parser(institution, req_text, block_type, block_value, title):
  """  Mainly, this is the main testing thing.
  """
  input_stream = InputStream(req_text)
  lexer = ReqBlockLexer(input_stream)
  token_stream = CommonTokenStream(lexer)
  parser = ReqBlockParser(token_stream)
  interpreter = ReqBlockInterpreter(institution, block_type, block_value, title)
  walker = ParseTreeWalker()
  tree = parser.req_text()
  walker.walk(interpreter, tree)
  print(interpreter.html)


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
            dgw_parser(institution, requirement_text + '\n', type, value, row.title)
