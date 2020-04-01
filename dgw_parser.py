#! /usr/bin/env python3
"""
    The goal of this project is to produce lists of courses that are required and/or can be used to
    satisfy a requirement. So the course_lists have to be tagged somehow. For now the only
    distinction is courses listed in the head (generally exclusions) and those listed in the body
    (mostly requirements.) This has to be refined: what courses are required, what ones can be used,
    and what ones are prohibited. There are parameters associated with each of these three classes
    that need to be worked out if this is going to be useful for transfer guidance. Not so much,
    though, for generating catalog descriptions.
"""

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

# Lists of tuples of these types get added to lists for the Head and Body sections.
Requirement = namedtuple('Requirement', 'keyword, value, text, course')
ShareList = namedtuple('ShareList', 'keyword text share_list')

# Used for lists of active courses found for particular scribed discipline-catalog_number pairs.
CourseList = namedtuple('CourseList',
                        'scribed_courses list_type customizations exclusions '
                        'active_courses attributes')

trans_dict: Dict[int, None] = dict()
for c in range(13, 31):
  trans_dict[c] = None

trans_table = str.maketrans(trans_dict)

# Dict of known colleges
colleges = dict()
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
for row in cursor.fetchall():
  colleges[row.code] = row.name
conn.close()

# Known named fields for WITH clauses
with_named_fields = ['DWAge', 'DWCredits', 'DWCreditType', 'DWCourseNumber', 'DWDiscipline',
                     'DWGradeNumber', 'DWGradeLetter', 'DWGradeType', 'DWLocation', 'DWPassFail',
                     'DWResident', 'DWSchool', 'DWSection', 'DWTer', 'DWTitle', 'DWTransfer',
                     'DWTransferCourse', 'DWTransferSchool', 'DWInprogress', 'DWPreregistered',
                     'DWTermType', 'DWPassed']
# The ones of interest here:
known_with_qualifiers = ['DWPassFail', 'DWResident', 'DWTransfer', 'DWTransferCourse']


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


# do_with()
# -------------------------------------------------------------------------------------------------
def do_with(ctx):
  """ with_clause     : LP WITH with_list RP ;
      with_list       : with_expr (LOG_OP with_expr)* ;
      with_expr       : SYMBOL REL_OP (STRING | ALPHA_NUM) (OR (STRING + ALPHA_NUM))* ;

      Return a string describing the customization. Four cases are interpreted; others are reported
      as scribed.
  """
  if DEBUG:
    print('*** do_with()', file=sys.stderr)
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
  """ course_list     : course (and_list | or_list)? with_clause? except_clause? ;
      course          : DISCIPLINE (CATALOG_NUMBER | WILDNUMBER | NUMBER | RANGE) ;
      course_item     : DISCIPLINE? (CATALOG_NUMBER | WILDNUMBER | NUMBER | RANGE) ;
      and_list        : (AND course_item with_clause?)+ ;
      or_list         : (OR course_item with_clause?)+ ;

      If the list is an AND list, but there are wildcards, say it's an OR list.
      This should not be an issue because this grammar allows either type of list in places where
      the Scribe language actually restricts the rules to OR lists.

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
    print(f'*** build_course_list()', file=sys.stderr)
  if ctx is None:
    return None

  # The object to be returned (as a namedtuple), and shortcuts to the fields
  return_object = {'scribed_courses': [],
                   'list_type': '',
                   'customizations': '',
                   'exclusions': [],
                   'active_courses': [],
                   'attributes': []}
  scribed_courses = return_object['scribed_courses']
  exclusions = return_object['exclusions']
  active_courses = return_object['active_courses']
  attributes = return_object['attributes']

  # Drill into ctx to determine which type of list
  if ctx.and_list():
    return_object['list_type'] = 'and'
    list_fun = ctx.and_list
  elif ctx.or_list():
    return_object['list_type'] = 'or'
    list_fun = ctx.or_list
  else:
    list_fun = None

  # The list has to start with both a discipline and catalog number
  course_ctx = ctx.course()
  discipline, catalog_number = (str(c) for c in course_ctx.children)
  scribed_courses.append((discipline, catalog_number))

  # For the remaining scribed courses, distribute disciplines across elided elements
  if list_fun is not None:
    course_items = list_fun().course_item()
    for course_item in course_items:
      items = [str(c) for c in course_item.children]
      if len(items) == 1:
        catalog_number = items[0]
      else:
        discipline, catalog_number = items
      scribed_courses.append((discipline, catalog_number))

  # Customizations (WITH clause)
  if ctx.with_clause():
    return_object['customizations'] = do_with(ctx.with_clause())

  # Exclusions (EXCEPT clauses)
  if ctx.except_clause():
    exclusions_ctx = ctx.except_clause()
    return_object['exceptions'] = build_course_list(institution, exclusions_ctx)

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
        active_courses.append(row)
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

  return CourseList._make(return_object.values())


# course_list2html()
# -------------------------------------------------------------------------------------------------
def course_list2html(course_list: List):
  """ Turn a list of active courses into a list of HTML sections.
  """
  return_list = []

  for course in course_list:
    num_courses = len(course.active_courses)
    if num_courses == 0:
      num_courses = 'No'
    summary = (f'<p>There are {num_courses} active courses that match this course '
               f'specification.</p>')
    if num_courses == len(course.scribed_courses):
      summary = ''  # No need to say anything about this normal case.

    suffix = '' if len(course.active_courses) == 1 else 's'

    # With
    if len(course_list.customizations) > 0:
      suffix += '<h2>Customizations</h2><p>This list applies only when:</p>'
      if len(course_list.customizations) == 1:
        suffix += f'<p>{course_list.customizations[0]}</p>'
      else:
        suffix += '<ul class="closeable">'
        for customization in course_list.customizations:
          suffix += f'<li>{customization}</li>'
        suffix += '</ul>'

    # Except
    if len(course_list.exceptions) > 0:
      suffix += '<h2>Exceptions</h2>'
      if len(course_list.exceptions) == 1:
        suffix += f'<p>{course_list.exceptions[0]}</p>'
      else:
        suffix += '<ul class="closeable">'
        for exception in course_list.exceptions:
          suffix += f'<li>{exception}</li>'
        suffix += '</ul>'

    html = """
    <section>
      <h1>Degreeworks specification: “{course.discipline} {course.catalog_number}”</h1>
      {summary}
      <h2 class="closer">{num_courses} Active Course{suffix}</h2>
      <p></p>
      <ul class="closeable">
    """

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


# class ScribeSection(Enum)
# -------------------------------------------------------------------------------------------------
class ScribeSection(Enum):
  """ Keep track of which section of a Scribe Block is being processed.
  """
  NONE = 0
  HEAD = 1
  BODY = 2


# Class ReqBlockInterpreter(ReqBlockListener)
# =================================================================================================
class ReqBlockInterpreter(ReqBlockListener):
  def __init__(self, institution, block_type, block_value, title, period_start, period_stop,
               requirement_text):
    """ Lists of Requirements, ShareLists, and possibly other named tuples for the Head and Body
        setions of a Requirement Block are populated as the parse tree is walked for a particular
        Block. Each named tuple starts with a keyword
    """

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
    self.sections = [None, [], []]  # NONE, HEAD, BODY

  @property
  def html(self):
    # Add line numbers to requirements text for development purposes.
    num_lines = self.requirement_text.count('\n')
    lines_pre = '<pre class="line-numbers">'
    for line in range(num_lines):
      lines_pre += f'{line + 1:03d}  \n'
    lines_pre += '</pre>'

    html_body = f"""
<h1>{self.institution_name} {self.title}</h1>
<p>Requirements for Catalog Years
{format_catalog_years(self.period_start, self.period_stop)}
</p>
<section>
  <h1 class="closer">Degreeworks Code</h1>
  <div>
    <hr>
    <section class=with-numbers>
      {lines_pre}
      <pre>{self.requirement_text.replace('<','&lt;')}</pre>
    </section
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

  # enterMinCredit()
  # -----------------------------------------------------------------------------------------------
  def enterMincredit(self, ctx):
    """ mincredit   :MINCREDIT NUMBER course_list TAG? ;
    """
    if DEBUG:
      print('*** enterMincredit()', file=sys.stderr)
    num_credits = float(str(ctx.NUMBER()))
    course_list = build_course_list(self, ctx.course_list())
    print(course_list)

  # enterNumcredit()
  # -----------------------------------------------------------------------------------------------
  def enterNumcredit(self, ctx):
    """ (NUMBER | RANGE) CREDIT PSEUDO? INFROM? course_list? TAG? ;
    """
    if DEBUG:
      print('*** enterNumcredit()', file=sys.stderr)
    self.sections[self.scribe_section.value].append(numcredit(self.institution,
                                                              self.block_type_str,
                                                              ctx))

  # enterMaxcredit()
  # -----------------------------------------------------------------------------------------------
  def enterMaxcredit(self, ctx):
    """ MAXCREDIT NUMBER course_list TAG? ;

        UNRESOLVED: the WITH clause applies only to the last course in the course list unless it's a
        range, in which cass it applies to all. Not clear what a wildcard catalog number means yet.
    """
    if DEBUG:
      print(f'*** enterMaxcredit()', file=sys.stderr)
    limit = f'a maximum of {ctx.NUMBER()}'
    if ctx.NUMBER() == 0:
      limit = 'zero'
    text = f'This {self.block_type_str} allows {limit} credits'
    course_list = None
    # There can be two course lists, the main one, and an EXCEPT one
    course_lists = ctx.course_list()
    if len(course_lists) > 0:
      course_list = build_course_list(self.institution, course_lists[0])
    if len(course_lists) > 1:
      except_list = build_course_list(self.institution, course_lists[1])

    if course_list is None:  # Weird: no credits allowed, but no course list provided.
      raise ValueError(f'MaxCredit rule with no courses specified.')

    else:
      list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
      attributes, html_list = course_list2html(course_list['courses'])
      len_list = len(html_list)
      if len_list == 1:
        preamble = f' in '
        courses = html_list[0]
      else:
        preamble = f' in {list_quantifier} of these {len_list} courses:'
        courses = html_list
      # Need to report what attributes all the found courses share and need to process any WITH
      # and EXCEPT clauses. YOU ARE HERE******************************************************
      text += f' {preamble} '
    self.sections[self.scribe_section.value].append(
        Requirement('maxcredits',
                    f'{ctx.NUMBER()} credits',
                    f'{text}',
                    courses))

  # enterMaxclass()
  # -----------------------------------------------------------------------------------------------
  def enterMaxclass(self, ctx):
    """ MAXCLASS NUMBER course_list TAG? ;
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
      raise ValueError('MaxClass with no list of courses.')
    # else:
    #   attributes, html_list = course_list2html(course_list['courses'])
    #   len_list = len(html_list)
    #   if len_list == 1:
    #     preamble = f' in '
    #     courses = html_list[0]
    #   else:
    #     if len_list == 2:
    #       list_quantifier = 'either' if course_list['list_type'] == 'or' else 'both'
    #     else:
    #       list_quantifier = 'any' if course_list['list_type'] == 'or' else 'all'
    #     preamble = f' in {list_quantifier} of these {len_list} {" and ".join(attributes)} courses:'
    #     courses = html_list
    #   text += f' {preamble} '
    # self.sections[self.scribe_section.value].append(
    #     Requirement('maxlasses',
    #                 f'{num_classes} class{suffix}',
    #                 f'{text}',
    #                 courses))

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
    """ (NUMBER | RANGE) CLASS INFROM? course_list? TAG? label* ;
    """
    if DEBUG:
      print('*** enterNumClass', file=sys.stderr)
    # Sometimes this is part of a rule subset (but not necessarily?)
    if hasattr(ctx, 'visited'):
      return
    else:
      return numclass(ctx)

  # enterGroup()
  # -----------------------------------------------------------------------------------------------
  def enterGroup(self, ctx):
    """ group       : NUMBER GROUP INFROM? group_list group_qualifier* label ;
        group_list  : group_item (OR group_item)* ;
        group_item  : LP
                    (course
                    | block
                    | block_type
                    | group
                    | rule_complete
                    | noncourse
                    ) RP label? ;
        group_qualifier : maxpassfail
                        | maxperdisc
                        | maxtransfer
                        | mingrade
                        | minperdisc
                        | samedisc
                        | share
                        | minclass
                        | mincredit
                        | ruletag ;
    """
    if DEBUG:
      print('*** enterGroup', file=sys.stderr)
    num_required = str(ctx.NUMBER())
    group_list = ctx.group_list()
    print('group_list.children:', group_list.children)
    label_ctx = ctx.label()
    label_str = label_ctx.STRING()
    label_ctx.visited = True
    if DEBUG:
      print('    ', label_str)
      print(f'    Require {num_required} of num_provided groups.')

  # enterRule_subset()
  # -----------------------------------------------------------------------------------------------
  def enterRule_subset(self, ctx):
    """ BEGINSUB (class_credit | group)+ ENDSUB qualifier* label ;
        class_credit    : (NUMBER | RANGE) (CLASS | CREDIT)
                          (ANDOR (NUMBER | RANGE) (CLASS | CREDIT))? PSEUDO?
                          INFROM? course_list? TAG? label? ;
        qualifier       : mingpa | mingrade ;
        mingpa          : MINGPA NUMBER ;
        mingrade        : MINGRADE NUMBER ;
    """
    if DEBUG:
      print('*** enterRule_subset', file=sys.stderr)
    for class_credit_ctx in ctx.class_credit():
      print(str(class_credit_ctx.NUMBER()[0]))

    classes_list = []

    label_ctx = ctx.label()
    label_str = label_ctx.STRING()
    print(label_str)
    label_ctx.visited = True

    # self.sections[self.scribe_section.value].append(
    #     Requirement('subset',
    #                 f'{len(classes_list)} classes or {len(credits_list)}',
    #                 label_str,
    #                 classes_list))

  def enterBlocktype(self, ctx):
    """ NUMBER BLOCKTYPE LP DEGREE|CONC|MAJOR|MINOR RP label
    """
    if DEBUG:
      print('*** enterBlocktype', file=sys.stderr)
      print(ctx.SHARE_LIST())
    pass

  # These two are in the superclass, but should be covered by enterRule_subset() above
  # def enterBeginsub(self, ctx):
  #   if DEBUG:
  #     print('*** enterBeginSub', file=sys.stderr)
  #   pass

  # def enterEndsub(self, ctx):
  #   if DEBUG:
  #     print('*** enterEndSub', file=sys.stderr)
  #   pass

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
      try:
        if ctx.visited:
          return None
      except AttributeError:
        # All labels should be processed as part of a rule
        print(ctx.STRING(), file=sys.stderr)

  # enterShare()
  # -----------------------------------------------------------------------------------------------
  def enterShare(self, ctx):
    """ share           : (SHARE | DONT_SHARE) (NUMBER (CREDIT | CLASS))? SHARE_LIST ;
        SHARE_LIST      : LP SHARE_ITEM (COMMA SHARE_ITEM)* RP ;
        SHARE_ITEM      : DEGREE | CONC | MAJOR | MINOR | (OTHER (EQ SYMBOL)?) | THIS_BLOCK;
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

    # There are separate share and exclusive SHARE_ITEM lists for the head and body.
    this_section = self.sections[self.scribe_section.value]
    for i, item in enumerate(this_section):
      if item.keyword == share_type:
        break
    else:   # This really is for the for loop: add the appropriate type of share list to the section
      this_section.append(ShareList(share_type, text, []))
      i = len(this_section) - 1

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


# main()
# =================================================================================================
# You could use this to test this module, but there are tests and testing subdirectories that serve
# that purpose better. For development, the transfer app and its log files provide a good way to
# look at how the processor handles different requirement blocks.
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
