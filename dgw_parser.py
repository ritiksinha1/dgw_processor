#! /usr/bin/env python3

import logging
import inspect
from datetime import datetime
from pprint import pprint
from typing import List, Set, Dict, Tuple, Optional, Union

import argparse
import sys
import os
import traceback
from io import StringIO
import re

from collections import namedtuple
from enum import Enum
from urllib import parse

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockListener import ReqBlockListener

from pgconnection import PgConnection

from closeable_objects import dict2html, items2html
from templates import *

# Module initialization
# -------------------------------------------------------------------------------------------------
DEBUG = os.getenv('DEBUG_PARSER')

if not os.getenv('HEROKU'):
  logging.basicConfig(filename='Logs/antlr.log',
                      format='%(asctime)s %(message)s',
                      level=logging.DEBUG)

Requirement = namedtuple('Requirement', 'keyword, value, text, course')
ShareList = namedtuple('ShareList', 'keyword text share_list')
ScribedCourse = namedtuple('ScribedCourse', 'discipline catalog_number courses')

trans_dict: Dict[int, None] = dict()
for c in range(13, 31):
  trans_dict[c] = None

trans_table = str.maketrans(trans_dict)

# Create dict of known colleges
colleges = dict()
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
for row in cursor.fetchall():
  colleges[row.code] = row.name
conn.close()

# Utilities
# =================================================================================================


# format_catalog_years
# -------------------------------------------------------------------------------------------------
def format_catalog_years(period_start: str, period_stop: str) -> str:
  """ Just the range of years covered, not whether grad/undergrad
  """
  first = period_start[0:4]
  if period_stop == '99999999':
    last = 'until Now'
  else:
    last = f'through {period_stop[5:9]}'
  return f'{first} {last}'


# get_number()
# -------------------------------------------------------------------------------------------------
def get_number(ctx):
  """ Return int or float depending on value
  """
  value = float(str(ctx.NUMBER()))
  if value == int(value):
    value = int(value)
  return value


# get_range()
# -------------------------------------------------------------------------------------------------
def get_range(ctx):
  """ Like get_number, but for range
  """
  low, high = [float(n) for n in str(ctx.RANGE()).split(':')]
  if int(low) == low and int(high) == high:
    low = int(low)
    high = int(high)
  return low, high


# class_or_credit()
# -------------------------------------------------------------------------------------------------
def class_or_credit(ctx, number=0) -> str:
  """ (CLASS | CREDIT)
      Number, if present, tells whether to return singular or plural form of the keyword
  """
  if DEBUG:
    print('*** class_or_credit()', file=sys.stderr)
  which = ctx.CREDIT()
  if which is None:
    which = ctx.CLASS()
  which = str(which).lower().strip('es')
  if number != 1:
    which = classes if which == 'class' else 'credits'
  return which


# build_course_list()
# -------------------------------------------------------------------------------------------------
def build_course_list(institution, ctx) -> list:
  """ course_list     : course (and_list | or_list)? ;
      course          : DISCIPLINE (CATALOG_NUMBER | WILDNUMBER | NUMBER | RANGE | WITH) ;
      course_item     : DISCIPLINE? (CATALOG_NUMBER | WILDNUMBER | NUMBER | RANGE) ;
      and_list        : (AND course_item)+ ;
      or_list         : (OR course_item)+ ;

      If the list is an AND list, but there are wildcards, say it's an OR list.
      This should not be an issue because my grammar allows either type of list in places where the
      Scribe language actually restricts the rules to OR lists.

      The returned list has the list of courses as extracted from the Scribe block and, for each
      scribed course, a list of actual courses with their catalog descriptions, with the exception
      where the "course" part has a WITH qualifier as the catalog number.
  """
  if DEBUG:
    print(f'*** build_course_list()', file=sys.stderr)
  if ctx is None:
    return None
  scribed_courses: list = []

  # The list has to start with both a discipline and catalog number
  course_ctx = ctx.course()
  discipline, catalog_number = (str(c) for c in course_ctx.children)
  scribed_courses.append(ScribedCourse._make((discipline, catalog_number, [])))
  # Drill into ctx to determine which type of list
  list_type = 'or'  # default
  if ctx.and_list():
    list_type = 'and'
    list_fun = ctx.and_list
  elif ctx.or_list():
    list_type = 'or'
    list_fun = ctx.or_list
  else:
    list_fun = None

  if list_fun is not None:
    course_items = list_fun().course_item()
    for course_item in course_items:
      items = [str(c) for c in course_item.children]
      if len(items) == 1:
        catalog_number = items[0]
      else:
        discipline, catalog_number = items
      scribed_courses.append(ScribedCourse._make((discipline, catalog_number, [])))

  # Expand the list of scribe-encoded courses into courses that actually exist
  conn = PgConnection()
  cursor = conn.cursor()
  for scribed_course in scribed_courses:
    # For display to users
    display_discipline, display_catalog_number, _ = scribed_course
    # For course db query
    discipline, catalog_number, _ = scribed_course
    # discipline part
    discp_op = '='
    if '@' in discipline:
      discp_op = '~*'
      discipline = '^' + discipline.replace('@', '.*') + '$'

    # catalog number part
    #   If the catalog_number is a WITH qualifier, skip the lookup for this course.
    if catalog_number.lower().startswith('(with'):
      continue
    #   0@ means any catalog number < 100 according to the Scribe manual, but CUNY has no catalog
    #   numbers that start with zero. But other patterns might be used: 1@, for example.
    catalog_numbers = catalog_number.split(':')
    if len(catalog_numbers) == 1:
      if '@' in catalog_numbers[0]:
        catnum_clause = "catalog_number ~* '^" + catalog_numbers[0].replace('@', '.*') + '$'
      else:
        catnum_clause = f"catalog_number = '{catalog_numbers[0]}'"
    else:
      low, high = catalog_number
      #  Assume no wildcards in range
      try:
        catnum_clause = f"""(numeric_part(catalog_number) >= {float(low)} and
                             numeric_part(catalog_number) <=' {float(high)}')
                         """
      except ValueError:
        #  There is no good way to turn this into a db query (that I know of), so the following
        #  assumptions are used:
        #    - the range is being used for a range of course levels (1@:3@, for example)
        #    - catalog numbers are 3 digits (so 1@ means 100 to 199, for example
        matches = re.match('(.*?)@(.*)', low)
        if matches.group(1).isdigit():
          low = matches.group(1) + '00'
          matches = re.match('(.*?)@(.*)', high)
          if matches.group(1).isdigit():
            high = matches.group(1) + '99'
            catnum_clause = f"""(numeric_part(catalog_number) >= {float(low)} and
                                 numeric_part(catalog_number) <=' {float(high)}')
                             """
        else:
          # Either low or high is not in the form \d+@
          catnum_clause = "catalog_number = ''"  # Will match no courses
    course_query = f"""
select institution, course_id, offer_nbr, discipline, catalog_number, title,
       requisites, description, contact_hours, max_credits, designation,
       replace(regexp_replace(attributes, '[A-Z]+:', '', 'g'), ';', ',')
       as attributes
  from cuny_courses
 where institution ~* '{institution}'
   and course_status = 'A'
   and discipline {discp_op} '{discipline}'
   and {catnum_clause}
   order by discipline, numeric_part(catalog_number)
              """
    cursor.execute(course_query)

    # Convert generator to list.
    for row in cursor.fetchall():
      scribed_course.courses.append(row)
  conn.close()
  return {'courses': scribed_courses, 'list_type': list_type}


# course_list2html()
# -------------------------------------------------------------------------------------------------
def course_list2html(course_list: dict):
  """ Look up all the courses in course_list, and return their catalog entries as a list of HTML
      divs.
  """
  all_blanket = True
  all_writing = True

  return_list = []
  for course in course_list:
    num_courses = len(course.courses)
    if num_courses == 0:
      summary = '<p>There are no active courses that match this course specification.</p>'
      num_courses = 'No'
    elif num_courses == 1:
      summary = ''  # Nothing to say about this: it's normal.
    else:
      summary = (f'<p>The following {num_courses} active courses match this course '
                 f'specification.</p>')

    suffix = '' if len(course.courses) == 1 else 's'
    this_course_list = f"""
    <section>
      <h1>Degreeworks specification: “{course.discipline} {course.catalog_number}”</h1>
      {summary}
      <h2 class="closer">{num_courses} Active Course{suffix}</h2>
      <ul class="closeable">
    """
    for found_course in course.courses:
      if all_writing and 'WRIC' not in found_course.attributes:
        all_writing = False
      if all_blanket and 'BKCR' not in found_course.attributes \
         and found_course.max_credits > 0:
        # if DEBUG:
        #   print('***', found_course.discipline, found_course.catalog_number, 'is a wet blanket',
        #         file=sys.stderr)
        all_blanket = False
      this_course_list += f"""
                  <li title="{found_course.course_id}:{found_course.offer_nbr}">
                    <strong>
                      {found_course.discipline} {found_course.catalog_number}
                      {found_course.title}</strong>
                    <br>
                    {found_course.contact_hours:0.1f} hr; {found_course.max_credits:0.1f} cr
                    Requisites: <em>{found_course.requisites}</em>
                    <br>
                    {found_course.description}
                    <br>
                    <em>
                      Designation: {found_course.designation};
                      Attributes: {found_course.attributes}
                    </em>
                  </li>
              """
    this_course_list += '</ul></section>'
    return_list.append(this_course_list)
  attributes = []
  if all_blanket:
    attributes.append('blanket credit')
  if all_writing:
    attributes.append('writing intensive')

  return attributes, return_list


# class ScribeSection(Enum)
# -------------------------------------------------------------------------------------------------
class ScribeSection(Enum):
  """ Keep track of which section of a Scribe Block is being processed.
  """
  NONE = 0
  HEAD = 1
  BODY = 2


# Class ReqBlockInterpreter
# =================================================================================================
class ReqBlockInterpreter(ReqBlockListener):
  def __init__(self, institution, block_type, block_value, title, period_start, period_stop,
               requirement_text):
    if DEBUG:
      print(f'*** ReqBlockInterpreter({institution}, {block_type}, {block_value})', file=sys.stderr)
    self.institution = institution
    self.block_type = block_type
    self.block_type_str = (block_type.lower()
                           .replace('conc', 'concentration')
                           .replace('other', 'other requirement'))
    self.block_value = block_value
    self.title = title
    self.period_start = period_start
    self.period_stop = period_stop
    self.institution_name = colleges[institution]
    self.requirement_text = requirement_text
    self.scribe_section = ScribeSection.NONE
    self.sections = [[], [], []]  # NONE, HEAD, BODY

  @property
  def html(self):
    len_empty = len(self.sections[ScribeSection.NONE.value])
    assert len_empty == 0, (
        f'ERROR: Scribe Block Section {ScribeSection.NONE.name} has'
        f'{len_empty} item{"" if len_empty == 1 else "s"} instead of none.')
    html_body = f"""
<h1>{self.institution_name} {self.title}</h1>
<p>Requirements for Catalog Years
{format_catalog_years(self.period_start, self.period_stop)}
</p>
<section>
  <h1 class="closer">Degreeworks Code</h1>
  <div>
    <hr>
    <pre>{self.requirement_text.replace('<','&lt;')}</pre>
  </div>
</section>
<section>
  <h1 class="closer">Extracted Requirements</h1>
  <div>
    <hr>
    {items2html(self.sections[ScribeSection.HEAD.value], 'Head Item')}
    {items2html(self.sections[ScribeSection.BODY.value], 'Body Item')}
  </div>
</section
"""

    return html_body

  def enterHead(self, ctx):
    if DEBUG:
      print('*** ENTERHEAD()', file=sys.stderr)
    self.scribe_section = ScribeSection.HEAD

  def enterBody(self, ctx):
    if DEBUG:
      print('*** ENTERBODY()', file=sys.stderr)

# numclasses  : NUMBER CLASSES (and_courses | or_courses) ;
# proxy_advice: PROXYADVICE STRING proxy_advice* ;
# noncourses  : NUMBER NONCOURSES LP SYMBOL (',' SYMBOL)* RP ;

# symbol      : SYMBOL ;

    self.scribe_section = ScribeSection.BODY

  def enterMinres(self, ctx):
    """ MINRES NUMBER (CREDIT | CLASS)
    """
    if DEBUG:
      print('*** enterMinres()', file=sys.stderr)
    number = get_number(ctx)
    which = class_or_credit(ctx, number)
    self.sections[self.scribe_section.value].append(
        Requirement('minres',
                    f'{number} {which}',
                    f'At least {number} {which.lower()} '
                    f'must be completed in residency.',
                    None))

# mingpa      : MINGPA NUMBER ;
# mingrade    : MINGRADE NUMBER ;

  # enterNumcredit()
  # -----------------------------------------------------------------------------------------------
  def enterNumcredit(self, ctx):
    """ (NUMBER | RANGE) CREDIT PSEUDO? INFROM? course_list? TAG? ; ;
    """
    if DEBUG:
      print('*** enterNumcredit()', file=sys.stderr)
    if ctx.PSEUDO() is None:
      text = f'This {self.block_type_str} requires '
    else:
      text = f'This {self.block_type_str} generally requires '
    if ctx.NUMBER() is not None:
      number = get_number(ctx)
      suffix = '' if number == 1 else 's'
      text += f'{number} credit{suffix}'
    elif ctx.RANGE() is not None:
      low, high = get_range(ctx)
      text += f'between {low} and {high} credits'
    else:
      text += f'an <span class="error">unknown</span> number of credits'
    course_list = None
    if ctx.course_list() is not None:
      course_list = build_course_list(self.institution, ctx.course_list())

    if course_list is None:
      text += '.'
      courses = None
    else:
      list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
      attributes, html_list = course_list2html(course_list['courses'])
      len_list = len(html_list)
      if len_list == 1:
        preamble = f' in '
        courses = html_list[0]
      else:
        preamble = f' in {list_quantifier} of these {len_list} {" and ".join(attributes)} courses:'
        courses = html_list
      text += f' {preamble} '
    self.sections[self.scribe_section.value].append(
        Requirement('credits',
                    f'{ctx.NUMBER()} credits',
                    f'{text}',
                    courses))

  # enterMaxcredit()
  # -----------------------------------------------------------------------------------------------
  def enterMaxcredit(self, ctx):
    """ MAXCREDIT NUMBER (and_courses | or_courses)
    """
    if DEBUG:
      print(f'*** enterMaxcredit()', file=sys.stderr)
    limit = f'a maximum of {ctx.NUMBER()}'
    if ctx.NUMBER() == 0:
      limit = 'zero'
    text = f'This {self.block_type_str} allows {limit} credits'
    course_list = None
    if ctx.and_courses() is not None:
      course_list = build_course_list(self.institution, ctx.and_courses())
    if ctx.or_courses() is not None:
      course_list = build_course_list(self.institution, ctx.or_courses())

    if course_list is None:  # Weird: no credits allowed, but no course list provided.
      text += '.'
      courses = None
    else:
      list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
      attributes, html_list = course_list2html(course_list['courses'])
      len_list = len(html_list)
      if len_list == 1:
        preamble = f' in '
        courses = html_list[0]
      else:
        preamble = f' in {list_quantifier} of these {len_list} {" and ".join(attributes)} courses:'
        courses = html_list
      text += f' {preamble} '
    self.sections[self.scribe_section.value].append(
        Requirement('maxcredits',
                    f'{ctx.NUMBER()} credits',
                    f'{text}',
                    courses))

  # enterMaxclass()
  # -----------------------------------------------------------------------------------------------
  def enterMaxclass(self, ctx):
    """ MAXCLASS NUMBER INFROM? course_list WITH? (EXCEPT course_list)? TAG? ;
    """
    if DEBUG:
      print('*** enterMaxclass()', file=sys.stderr)
    num_classes = int(str(ctx.NUMBER()))
    suffix = '' if num_classes == 1 else 'es'
    limit = f'no more than {num_classes} class{suffix}'
    if num_classes == 0:
      limit = 'no classes'
    text = f'This {self.block_type_str} allows {limit}'
    course_list = None
    # There can be two course lists, the main one, and an EXCEPT one
    course_lists = ctx.course_list()
    if len(course_lists) > 0:
      course_list = build_course_list(self.institution, course_lists[0])
    if len(course_lists) > 1:
      except_list = build_course_list(self.institution, course_lists[1])

    if course_list is None:  # Weird: no classes allowed, but no course list provided.
      text += '.'
      courses = None
    else:
      attributes, html_list = course_list2html(course_list['courses'])
      len_list = len(html_list)
      if len_list == 1:
        preamble = f' in '
        courses = html_list[0]
      else:
        if len_list == 2:
          list_quantifier = 'either' if course_list['list_type'] == 'or' else 'both'
        else:
          list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
        preamble = f' in {list_quantifier} of these {len_list} {" and ".join(attributes)} courses:'
        courses = html_list
      text += f' {preamble} '
    self.sections[self.scribe_section.value].append(
        Requirement('maxlasses',
                    f'{num_classes} class{suffix}',
                    f'{text}',
                    courses))

  # enterMaxpassfail()
  # -----------------------------------------------------------------------------------------------
  def enterMaxpassfail(self, ctx):
    """ MAXPASSFAIL NUMBER (CREDIT | CLASS) (TAG '=' SYMBOL)?
    """
    if DEBUG:
      print('*** enterMaxpassfail()', file=sys.stderr)
    num = int(str(ctx.NUMBER()))
    limit = f'no more than {ctx.NUMBER()}'
    if num == 0:
      limit = 'no'
    which = class_or_credit(ctx)
    if num == 1:
      which = which[0:-1].strip('e')
    text = f'This {self.block_type_str} allows {limit} {which} to be taken Pass/Fail.'
    self.sections[self.scribe_section.value].append(
        Requirement('maxpassfail',
                    f'{num} {which}',
                    f'{text}',
                    None))

  def enterNumclass(self, ctx):
    if DEBUG:
      print('*** enterNumClass', file=sys.stderr)
    pass

  def enterRule_subset(self, ctx):
    if DEBUG:
      print('*** enterRule_subset', file=sys.stderr)
    pass

  def enterBlocktype(self, ctx):
    """ NUMBER BLOCKTYPE LP DEGREE|CONC|MAJOR|MINOR RP label
    """
    if DEBUG:
      print('*** enterBlocktype', file=sys.stderr)
      print(ctx.SHARE_LIST())
    pass

  def enterBeginsub(self, ctx):
    if DEBUG:
      print('*** enterBeginSub', file=sys.stderr)
    pass

  def enterEndsub(self, ctx):
    if DEBUG:
      print('*** enterEndSub', file=sys.stderr)
    pass

  def enterRemark(self, ctx):
    """ REMARK STRING remark* ;
    """
    if DEBUG:
      print('*** enterRemark()', file=sys.stderr)
      print(ctx.STRING(), file=sys.stderr)
    pass

  def enterLabel(self, ctx):
    """ REMARK STRING ';' remark* ;
    """
    if DEBUG:
      print('*** enterLabel()', file=sys.stderr)
      print(ctx.STRING(), file=sys.stderr)
    pass

  def enterShare(self, ctx):
    """ SHARE SHARE_LIST
    """
    if DEBUG:
      print('*** enterShare()', file=sys.stderr)
    token = str(ctx.SHARE())
    if token.lower() in ['share', 'sharewith', 'nonexclusive']:
      share_type = 'share'
      neg = ''
    else:
      share_type = 'exclusive'
      neg = ' not'
    text = (f'Courses used to satisfy this requirement may{neg} also be used to satisfy'
            f' the following requirements:')
    this_section = self.sections[self.scribe_section.value]
    for i, item in enumerate(this_section):
      if item.keyword == share_type:
        break
    else:
      i += 1
      this_section.append(ShareList(share_type, text, []))

    this_section[i].share_list.append(str(ctx.SHARE_LIST()).strip('()'))


# Class DGW_Logger
# =================================================================================================
class DGW_Logger(ErrorListener):

  def __init__(self, institution, block_type, block_value, period_stop):
    self.block = f'{institution} {block_type} {block_value} {period_stop}'

  def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
    logging.debug(f'{self.block} {type(recognizer).__name__} '
                  f'Syntax {line}:{column} {msg}')

  def reportAmbiguity(self, recognizer, dfa, startIndex, stopIndex, exact, ambigAlts, configs):
    logging.debug(f'{self.block}: {type(recognizer).__name__} '
                  f'Ambiguity {startIndex}:{stopIndex} {exact} ({ambigAlts}) {configs}')

  def reportAttemptingFullContext(self, recognizer, dfa, startIndex, stopIndex,
                                  conflictingAlts, configs):
    logging.debug(f' {self.block}: {type(recognizer).__name__} '
                  f'FullContext {dfa} {startIndex}:{stopIndex} ({conflictingAlts}) {configs}')

  def reportContextSensitivity(self, recognizer, dfa, startIndex, stopIndex, prediction, configs):
    logging.debug(f' {self.block}: {type(recognizer).__name__} '
                  f'ContextSensitivity {dfa} {startIndex}:{stopIndex} ({prediction}) {configs}')


# dgw_parser()
# =================================================================================================
def dgw_parser(institution, block_type, block_value, period='current'):
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
  if cursor.rowcount == 0:
    # This is a bug, not an error
    return f'<h1 class="error">No Requirements Found</h1><p>{cursor.query}</p>'
  return_html = ''
  for row in cursor.fetchall():
    if period == 'current' and row.period_stop != '99999999':
      return f"""<h1 class="error">“{row.title}” is not a currently offered {block_type}
                 at {institution}.</h1>
              """
    requirement_text = row.requirement_text\
                          .translate(trans_table)\
                          .strip('"')\
                          .replace('\\r', '\r')\
                          .replace('\\n', '\n') + '\n'
    dgw_logger = DGW_Logger(institution, block_type, block_value, row.period_stop)
    # Unable to get Antlr to ignore cruft before BEGIN and after END. so, reluctantly, removing the
    # cruft here in order to get on with parsing.
    match = re.search(r'.*?(BEGIN.*?END\.).*', requirement_text, re.I | re.S)
    if match is None:
      raise ValueError(f'BEGIN...;...END. not found:\n{requirement_text}')
    input_stream = InputStream(match.group(1))
    lexer = ReqBlockLexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(dgw_logger)
    token_stream = CommonTokenStream(lexer)
    parser = ReqBlockParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(dgw_logger)
    interpreter = ReqBlockInterpreter(institution,
                                      block_type,
                                      block_value,
                                      row.title,
                                      row.period_start,
                                      row.period_stop,
                                      requirement_text)
    try:
      walker = ParseTreeWalker()
      tree = parser.req_block()
      walker.walk(interpreter, tree)
    except Exception as e:
      if DEBUG:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=30, file=sys.stdout)
      msg_body = f"""College: {interpreter.institution}
                     Block Type: {interpreter.block_type}
                     Block Value: {interpreter.block_value}
                     Period Start: {interpreter.period_start}
                     Period Stop: {interpreter.period_stop}
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
    return_html += interpreter.html

    if period == 'current' or period == 'recent':
      break
  conn.close()
  return return_html


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

  # Get the top-level requirements to examine: college, block-type, and/or block value
  conn = PgConnection()
  cursor = conn.cursor()

  query = """
      select requirement_id, title, requirement_text
      from requirement_blocks
      where institution = %s
        and block_type = %s
        and block_value = %s
        and period_stop = '99999999'
  """
  for institution in args.institutions:
    institution = institution.upper() + ('01' * (len(institution) == 3))
    for block_type in args.block_types:
      for block_value in args.block_values:
        if args.debug:
          print(institution, block_type, block_value)
        print(dgw_parser(institution, block_type, block_value))
  conn.close()
