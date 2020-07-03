#! /usr/local/bin/python3
""" Convert Lexer and metadata items into JSON elements
"""

from collections import namedtuple
from enum import Enum
from typing import List, Set, Dict, Tuple, Optional, Union

from pgconnection import PgConnection

import argparse
import os
import sys

DEBUG = os.getenv('DEBUG_INTERPRETER')

# Dict of known colleges
colleges = dict()
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
for row in cursor.fetchall():
  colleges[row.code] = row.name
conn.close()


# class ScribeSection(Enum)
# -------------------------------------------------------------------------------------------------
class ScribeSection(Enum):
  """ Keep track of which section of a Scribe Block is being processed.
  """
  NONE = 0
  HEAD = 1
  BODY = 2


CatalogYears = namedtuple('CatalogYears', 'catalog_type first_year last_year text')


# expression_terminals()
# -------------------------------------------------------------------------------------------------
def expression_terminals(ctx, terminal_list):
  """ print the terminal nodes of an expression
  """
  if ctx.getChildCount() == 0:
    terminal_list.append({ctx.getParent().__class__.__name__: ctx.getText()})
  else:
    for child in ctx.getChildren():
      expression_terminals(child, terminal_list)


# context_path()
# -------------------------------------------------------------------------------------------------
def context_path(ctx):
  """ For debugging, given a context (or any object, actually), return a string showing the
      inheritance path for the object
  """
  ctx_list = []
  cur_ctx = ctx
  while cur_ctx:
    ctx_list.insert(0, type(cur_ctx).__name__.replace('Context', ''))
    cur_ctx = cur_ctx.parentCtx
  return ' => '.join(ctx_list)


# catalog_years()
# -------------------------------------------------------------------------------------------------
def catalog_years(period_start: str, period_stop: str) -> str:
  """ Metadata for "bulletin years": first yeear, last year and whether undergraduate or graduate
      period_start and period_end are supposed to look like YYYY-YYYY[UG], with the special value
      of '99999999' for period_end indicating the current catalog year.
      The earliest observed valid catalog year was 1960-1964, but note that it isn't a single
      academic year.
  """
  is_undergraduate = 'U' in period_start
  is_graduate = 'G' in period_start
  if is_undergraduate and not is_graduate:
    catalog_type = 'Undergraduate'
  elif not is_undergraduate and is_graduate:
    catalog_type = 'Graduate'
  else:
    catalog_type = 'Unknown'

  try:
    first = period_start.replace('-', '')[0:4]
    if int(first) < 1960:
      raise ValueError()
  except ValueError:
    first = 'Unknown-Start-Year'

  if period_stop == '99999999':
    last = 'Now'
  else:
    try:
      last = period_stop.replace('-', '')[4:8]
      if int(last) < 1960:
        raise ValueError()
    except ValueError:
      last = 'Unknown-End-Year'
  return CatalogYears._make((catalog_type, first, last, f'{first} through {last}'))


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


# with_clause()
# -------------------------------------------------------------------------------------------------
def with_clause(ctx):
  """ with_clause     : LP WITH expression RP;

      expression      : expression relational_op expression
                      | expression logical_op expression
                      | expression ',' expression
                      | full_course
                      | discipline
                      | NUMBER
                      | SYMBOL
                      | STRING
                      | CATALOG_NUMBER
                      | LP expression RP
                      ;
      Return a string describing the customization. Four cases are interpreted; others are reported
      as-scribed.
  """
  if DEBUG:
    print('*** with_clause()', file=sys.stderr)
  with_list = ctx.with_list()
  for with_expr in with_list.children:
    print(with_expr)
    print(with_expr.children)
    print('symbol:', with_expr.symbol().children, '\nrel_op:', str(with_expr.REL_OP()))
    if with_expr.STRING():
      print(' str:', str(with_expr.STRING()))
    elif with_expr.ALPHA_NUM():
      print(' alpha_num:', str(with_expr.ALPHA_NUM()))
    else:
      print('neither string nor alpha_num')
  return 'There was a WITH clause'


# build_course_list()
# -------------------------------------------------------------------------------------------------
def build_course_list(institution, ctx) -> list:
  """ course_list     : course_item (and_list | or_list)? course_qualifier* label?;
      full_course     : discipline catalog_number course_qualifier*;
      course_item     : discipline? catalog_number course_qualifier*;
      and_list        : (list_and course_item )+;
      or_list         : (list_or course_item)+;
      discipline      : SYMBOL | WILD | BLOCK | IS; // Keywords can be discipline names
      catalog_number  : SYMBOL | NUMBER | CATALOG_NUMBER | RANGE | WILD;
      course_qualifier: with_clause
                      | except_clause
                      | including_clause
                      | maxpassfail
                      | maxperdisc
                      | maxspread
                      | maxtransfer
                      | mincredit
                      | mingpa
                      | mingrade
                      | minspread
                      | ruletag
                      | samedisc
                      | share
                      | with_clause
                      ;

      The returned object has the following structure:
        scribed_courses     List of all discipline:catalog_number pairs specified after distributing
                            disciplines across catalog_numbers. (Show "BIOL 1, 2" as "BIOL 1, BIOL
                            2")
        list_type           'and' or 'or'
        customizations      Information about WITH pharases, and which scribed_courses they apply
                            to
        exclusions          List of course_lists for excluded courses
        active_courses      List of all active courses that match the scribed_courses list after
                            expanding wildcards and catalog_number ranges.
        attributes          List of all attribute values the active courses list have in common,
                            currently limited to WRIC and BKCR

  """
  if DEBUG:
    print(f'*** build_course_list({institution}, {ctx.__class__.__name__})', file=sys.stderr)
  if ctx is None:
    return None

  # The object to be returned (as a namedtuple), and shortcuts to the fields
  return_object = {'scribed_courses': [],
                   'list_type': '',
                   'qualifiers': [],
                   'label': '',
                   'active_courses': [],
                   'attributes': []}
  scribed_courses = return_object['scribed_courses']
  list_type = return_object['list_type']
  qualifiers = return_object['qualifiers']
  active_courses = return_object['active_courses']
  attributes = return_object['attributes']

  # Drill into ctx to determine which type of list
  if ctx.and_list():
    list_type = 'and'
    list_fun = ctx.and_list
  elif ctx.or_list():
    list_type = 'or'
    list_fun = ctx.or_list
  else:
    list_fun = None

  # The list has to start with both a discipline and catalog number, but sometimes just a wildcard
  # is given.
  print(ctx.course_item().getText())
  discipline, catalog_number, course_qualifier = (None, None, None)
  catalog_number = ctx.course_item().catalog_number().getText()
  # The next two might be absent
  try:
    discipline = ctx.course_item().discipline().getText()
  except AttributeError as ae:
    discipline = '@'
  try:
    course_qualifier = ctx.course_item().course_qualifier().getText()
  except AttributeError as ae:
    pass
  scribed_courses.append((discipline, catalog_number))

  # For the remaining scribed courses, distribute disciplines across elided elements
  if list_fun is not None:
    course_items = list_fun().course_item()
    for course_item in course_items:
      items = [c.getText() for c in course_item.children]
      if len(items) == 1:
        catalog_number = items[0]
      else:
        discipline, catalog_number = items
      scribed_courses.append((discipline, catalog_number))

  if course_qualifier is not None:
    print('course qualifier not implemented yet', course_qualifier)

  # Active Courses
  conn = PgConnection()
  cursor = conn.cursor()
  for scribed_course in scribed_courses:
    # For display to users
    display_discipline, display_catalog_number = scribed_course
    # For course db query
    discipline, catalog_number = scribed_course
    # discipline part
    discp_op = '='
    if '@' in discipline:
      discp_op = '~*'
      discipline = '^' + discipline.replace('@', '.*') + '$'

    # catalog number part

    #   0@ means any catalog number < 100 according to the Scribe manual, but CUNY has no catalog
    #   numbers that start with zero. But other patterns might be used: 1@, for example.
    catalog_numbers = catalog_number.split(':')
    if len(catalog_numbers) == 1:
      if '@' in catalog_numbers[0]:
        catnum_clause = "catalog_number ~* '^" + catalog_numbers[0].replace('@', '.*') + "$'"
      else:
        catnum_clause = f"catalog_number = '{catalog_numbers[0]}'"
    else:
      low, high = catalog_numbers
      #  Assume no wildcards in range ...
      try:
        catnum_clause = f"""(numeric_part(catalog_number) >= {float(low)} and
                             numeric_part(catalog_number) <=' {float(high)}')
                         """
      except ValueError:
        #  ... but it looks like there were.
        #  Assume:
        #    - the range is being used for a range of course levels (1@:3@, for example)
        #    - catalog numbers are 3 digits (so 1@ means 100 to 199, for example
        #  Otherwise, 1@ would match 1, 10-19, 100-199, and 1000-1999, which would be strange, or
        #  at least fragile in the case of Lehman, which uses 2000-level numbers for blanket credit
        #  courses at the 200 level.
        matches = re.match('(.*?)@(.*)', low)
        if matches.group(1).isdigit():
          low = matches.group(1) + '00'
          matches = re.match('(.*?)@(.*)', high)
          if matches.group(1).isdigit():
            high = matches.group(1) + '99'
            catnum_clause = f"""(numeric_part(catalog_number) >= {float(low)} and
                                 numeric_part(catalog_number) <= {float(high)})
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
    if cursor.rowcount > 0:
      all_blanket = True
      all_writing = True
      for row in cursor.fetchall():
        active_courses.append((row.course_id, row.offer_nbr, row.discipline, row.catalog_number,
                               row.title))
        if 'BKCR' not in row.attributes:
          all_blanket = False
        if 'WRIC' not in row.attributes:
          all_writing = False
      if all_blanket:
        attributes.append('blanket')
      if all_writing:
        attributes.append('writing')
  conn.close()

  #

  return return_object


# course_list2html()
# -------------------------------------------------------------------------------------------------
def course_list2html(course_list: List):
  """ Turn a list of active courses into a list of HTML sections.
  """
  return_list = []

  # for course in course_list:
  #   num_courses = len(course.active_courses)
  #   if num_courses == 0:
  #     num_courses = 'No'
  #   summary = (f'<p>There are {num_courses} active courses that match this course '
  #              f'specification.</p>')
  #   if num_courses == len(course.scribed_courses):
  #     summary = ''  # No need to say anything about this normal case.

  #   suffix = '' if len(course.active_courses) == 1 else 's'

  #   # With
  #   if len(course_list.customizations) > 0:
  #     suffix += '<h2>Customizations</h2><p>This list applies only when:</p>'
  #     if len(course_list.customizations) == 1:
  #       suffix += f'<p>{course_list.customizations[0]}</p>'
  #     else:
  #       suffix += '<ul class="closeable">'
  #       for customization in course_list.customizations:
  #         suffix += f'<li>{customization}</li>'
  #       suffix += '</ul>'

  #   # Except
  #   if len(course_list.exceptions) > 0:
  #     suffix += '<h2>Exceptions</h2>'
  #     if len(course_list.exceptions) == 1:
  #       suffix += f'<p>{course_list.exceptions[0]}</p>'
  #     else:
  #       suffix += '<ul class="closeable">'
  #       for exception in course_list.exceptions:
  #         suffix += f'<li>{exception}</li>'
  #       suffix += '</ul>'

  #   html = """
  #   <section>
  #     <h1>Degreeworks specification: “{course.discipline} {course.catalog_number}”</h1>
  #     {summary}
  #     <h2 class="closer">{num_courses} Active Course{suffix}</h2>
  #     <p></p>
  #     <ul class="closeable">
  #   """

  return return_list


# numcredit()
# -------------------------------------------------------------------------------------------------
def numcredit(institution, block_type_str, ctx):
  """ (NUMBER | RANGE) CREDIT PSEUDO? INFROM? course_list? TAG? ;
  """
  if DEBUG:
    print('*** numcredit()', file=sys.stderr)
  try:
    if ctx.visited:
      return None
  except AttributeError:
    ctx.visited = True
  if ctx.PSEUDO() is None:
    text = f'This {block_type_str} requires '
  else:
    text = f'This {block_type_str} generally requires '
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
  return Requirement('credits',
                     f'{ctx.NUMBER()} credits',
                     f'{text}',
                     courses)


# numclass()
# -------------------------------------------------------------------------------------------------
def numclass(institution, ctx):
  """ (NUMBER | RANGE) CLASS INFROM? course_list? TAG? label* ;
      Could be a standalone rule or as part of a group. This is the implementation for either.
  """
  if DEBUG:
    print('*** numclass()', file=sys.stderr)
  try:
    if ctx.visited:
      return None
  except AttributeError:
    ctx.visited = True
  if ctx.NUMBER():
    num_classes = int(str(ctx.NUMBER()))
  else:
    num_classes = None
  if ctx.RANGE():
    low, high = str(ctx.RANGE()).split(':')
  else:
    low = high = None
  if ctx.course_list():
    course_list = build_course_list(institution, ctx.course_list())
  else:
    course_list = None
  label_str = ''
  if ctx.label is not None:
    for label in ctx.label():
      label_str += str(label.STRING())
      label.visited = True
  return {'number': num_classes,
          'low': low,
          'high': high,
          'courses': course_list,
          'label': label_str}


# =================================================================================================
if __name__ == '__main__':
  parser = argparse.ArgumentParser('Test utils')
  parser.add_argument('-d', '--debug', action='store_true')
  parser.add_argument('-c', '--calendar_year', nargs=2)
  args = parser.parse_args()

  if args.calendar_year:
    result = catalog_years(args.calendar_year[0], args.calendar_year[1])
    print(f'{result.catalog_type} bulletin for {result.text}')
