#! /usr/local/bin/python3
""" Convert Lexer and metadata items into JSON elements
"""

from collections import namedtuple
from typing import List, Set, Dict, Tuple, Optional, Union

import argparse
import os
import sys

import json

from pgconnection import PgConnection
from course_list_qualifier import CourseListQualifier

DEBUG = os.getenv('DEBUG_UTILS')

# Dict of known colleges
colleges = dict()
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
for row in cursor.fetchall():
  colleges[row.code] = row.name
conn.close()


CatalogYears = namedtuple('CatalogYears', 'catalog_type first_year last_year text')


# class_name()
# =================================================================================================
def class_name(obj):
  return obj.__class__.__name__.replace('Context', '')


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
def context_path(ctx, interpret=[]):
  """ Given a context (or any object, actually), return a string showing the
      inheritance path for the object.
  """
  ctx_list = []
  cur_ctx = ctx
  while cur_ctx:
    ctx_list.insert(0, type(cur_ctx).__name__.replace('Context', ''))
    cur_ctx = cur_ctx.parentCtx
  return ' => '.join(ctx_list[1:])


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


# num_class_or_num_credir(ctx)
# -------------------------------------------------------------------------------------------------
def num_class_or_num_credit(ctx) -> dict:
  """ A context can have one num_classes, one num_credits, or both. When both are allowed, they will
      be lists of len 1, but if only one is allowed, it will be a scalar. Depends on the context.
      num_classes     : NUMBER CLASS allow_clause?;
      num_credits     : NUMBER CREDIT allow_clause?;
  """
  if DEBUG:
    print(f'{class_name(ctx)}')
  if ctx.num_classes():
    if isinstance(ctx.num_classes(), list):
      class_ctx = ctx.num_classes()[0]
    else:
      class_ctx = ctx.num_classes()
    num_classes = class_ctx.NUMBER().getText().strip()
    if class_ctx.allow_clause():
      allow_classes = class_ctx.allow_clause().NUMBER().getText().strip()
    else:
      allow_classes = None
  else:
    num_classes = allow_classes = None

  if ctx.num_credits():
    if isinstance(ctx.num_credits(), list):
      credit_ctx = ctx.num_credits()[0]
    else:
      credit_ctx = ctx.num_credits()
    num_credits = credit_ctx.NUMBER().getText().strip()
    if credit_ctx.allow_clause():
      allow_credits = credit_ctx.allow_clause().NUMBER().getText().strip()
    else:
     allow_credits = None
  else:
    num_credits = allow_credits = None

  if getattr(ctx, 'logical_op', None) and ctx.logical_op():
    conjunction = ctx.logical_op().getText()
  else:
    conjunction = None

  if conjunction is None:
    assert bool(num_classes) is not bool(num_credits), (f'Bad num_classes_or_num_credits: '
                                                        f'{ctx.getText()}')
  else:
    assert num_classes and num_credits, f'Bad num_classes_or_num_credits: {ctx.getText()}'

  return {'tag': 'num_class_credit',
          'num_classes': num_classes,
          'allow_classes': allow_classes,
          'num_credits': num_credits,
          'allow_credits': allow_credits,
          'conjunction': conjunction}


# class_or_credit()
# -------------------------------------------------------------------------------------------------
def class_or_credit(ctx) -> str:
  """ class_or_credit   : (CLASS | CREDIT);
      Tell whether it's 'class' or 'credit' regardless of how it was spelled/capitalized.
  """
  if DEBUG:
    print('*** class_or_credit()', file=sys.stderr)
  if ctx.CREDIT():
    return 'credit'
  return 'class'


# _with_clause()
# -------------------------------------------------------------------------------------------------
def _with_clause(ctx):
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
      This is a place where some interpretation could take place ... but does not do so yet.
  """
  if DEBUG:
    print('*** with_clause()', file=sys.stderr)
  assert ctx.__class__.__name__ == 'With_clauseContext', (f'{ctx.__class__.__name__} '
                                                          'is not With_clauseContext')
  return ctx.expression().getText()


# get_scribed_courses()
# -------------------------------------------------------------------------------------------------
def get_scribed_courses(ctx):
  """
  """
  context_name = ctx.__class__.__name__
  assert ctx.__class__.__name__ == 'Course_listContext', (f'{ctx.__class__.__name__} '
                                                          f'is not Course_listContext')
  if DEBUG:
    print(f'*** get_scribed_courses({ctx.__class__.__name__})', file=sys.stderr)
  if ctx is None:
    return []

  scribed_courses = []

  # The list has to start with both a discipline and catalog number, but sometimes just a wildcard
  # is given.
  discipline, catalog_number, with_clause = (None, None, None)

  catalog_number = ctx.course_item().catalog_number().getText()
  # The next two might be absent
  try:
    discipline = ctx.course_item().discipline().getText()
  except AttributeError as ae:
    discipline = '@'
  try:
    with_list = ctx.course_item().with_clause()
    for with_ctx in with_list:
      if with_ctx.__class__.__name__ == 'With_clauseContext':
        if with_clause is None:
          with_clause = _with_clause(with_ctx)
        else:
          with_clause += ' ' + _with_clause(with_ctx)
  except AttributeError as ae:
    pass
  scribed_courses.append((discipline, catalog_number, with_clause))

  # For the remaining scribed courses, distribute disciplines across elided elements
  list_fun = None
  if ctx.and_list():
    list_fun = ctx.and_list
  if ctx.or_list():
    list_fun = ctx.or_list

  if list_fun is not None:
    course_items = list_fun().course_item()
    catalog_number = None  # Must be present
    with_clause = None  # Does not distribute (as discipline does)
    for course_item in course_items:
      for child in course_item.children:
        if child.__class__.__name__ == 'DisciplineContext':
          discipline = child.getText()
        elif child.__class__.__name__ == 'Catalog_numberContext':
          catalog_number = child.getText()
        elif child.__class__.__name__ == 'With_clauseContext':
          with_clause = child.getText()   # Need to interpret this
          with_clause = _with_clause(child)
          # print(discipline, catalog_number, with_clause)
        else:
          # This is where square brackets show up
          print(f'Unexpected token type: {child.__class__.__name__}, text: {child.getText()}',
                file=sys.stderr)
      assert catalog_number is not None, (f'Course Item with no catalog number: '
                                          f'{course_item.getText()}')
      scribed_courses.append((discipline, catalog_number, with_clause))

  return scribed_courses


# get_qualifiers()
# -------------------------------------------------------------------------------------------------
def get_qualifiers(ctx):
  """
  """
  valid_qualifiers = ['dont_share', 'maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer',
                      'minarea', 'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc',
                      'minspread', 'ruletag', 'samedisc', 'share']
  qualifier_list = []
  siblings = ctx.parentCtx.getChildren()
  for sibling in siblings:
    for qualifier in valid_qualifiers:
      if qualifier_fun := getattr(sibling, qualifier, None):
        if qualifier_fun():
          class_credit = None

          if getattr(qualifier_fun(), 'CLASS', None) is not None:
            class_credit = 'class'
          if getattr(qualifier_fun(), 'CREDIT', None) is not None:
            class_credit = 'credit'

          # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
          if qualifier == 'maxpassfail':
            qualifier_list.append({'tag': qualifier,
                                   'number': qualifier_fun().NUMBER().getText(),
                                   'class_credit': class_credit})

          # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
          # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
          # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
          elif qualifier in ['maxperdisc', 'maxtransfer', 'minperdisc']:
            disciplines = qualifier_fun().SYMBOL()
            if isinstance(disciplines, list):
              disciplines = [d.getText() for d in disciplines]

            qualifier_list.append({'tag': qualifier,
                                   'number': qualifier_fun().NUMBER().getText(),
                                   'class_credit': class_credit,
                                   'disciplines': disciplines})

          # maxspread       : MAXSPREAD NUMBER
          # minarea         : MINAREA NUMBER
          # mingrade        : MINGRADE NUMBER
          # minspread       : MINSPREAD NUMBER
          elif qualifier in ['maxspread', 'minarea', 'mingrade', 'minspread']:
            qualifier_list.append({'tag': qualifier,
                                   'number': qualifier_fun().NUMBER().getText()})

          # minclass        : MINCLASS NUMBER course_list tag? display* label?;
          # mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
          elif qualifier in ['minclass', 'mincredit']:
            course_list_obj = build_course_list(institution, qualifier_fun().course_list())
            qualifier_list.append({'tag': qualifier,
                                   'number': qualifier_fun().NUMBER().getText(),
                                   'courses': course_list_obj})

          # mingpa          : MINGPA NUMBER (course_list | expression)?
          elif qualifier == 'mingpa':
            course_list_obj = qualifier_fun().course_list()
            if course_list_obj:
              course_list_obj = build_course_list(institution, qualifier_fun().course_list())

            expression_str = qualifier_fun().expression()
            if expression_str:
              expression_str = expression.getText()

            qualifier_list.append({'tag': qualifier,
                                   'number': qualifier_fun().NUMBER().getText(),
                                   'course_list': course_list_obj,
                                   'expression': expression_str})

          # ruletag         : RULE_TAG expression;
          # samedisc        : SAME_DISC expression
          elif qualifier in ['ruletag', 'samedisc']:
            qualifier_list.append({'tag': qualifier,
                                   'expression': qualifier_fun().expression().getText()})

          # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
          elif qualifier == 'share':
            print(qualifier_fun().getText())
            print(dir(qualifier_fun()))
            if qualifier_fun().DONT_SHARE():
              qualifier = 'dont_share'
            if qualifier_fun().CLASS:
              class_credit = 'class'
            elif qualifier_fun().CREDIT:
              class_credit = 'credit'
            else:
              class_credit = None
            if qualifier_fun().NUMBER():
              number = qualifier_fun().NUMBER().getText()
            else:
              number = None

            expression = qualifier_fun().expression()
            if expression:
              expression = expression.getText()

            qualifier_list.append({'tag': qualifier,
                                   'number': number,
                                   'class_credit': class_credit,
                                   'expression': expression})

          else:
            qualifier_list.append({'tag': qualifier})

  return qualifier_list


# get_course_list_qualifiers()
# -------------------------------------------------------------------------------------------------
def get_course_list_qualifiers(institution, ctx):
  """ Use parser info to generate and return a possibly-empty list of CourseListQualifier objects.
  """
  valid_qualifiers = ['dont_share', 'maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer',
                      'minarea', 'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc',
                      'minspread', 'ruletag', 'samedisc', 'share']
  qualifier_list = []
  siblings = ctx.parentCtx.getChildren()
  for sibling in siblings:
    for qualifier in valid_qualifiers:
      if qualifier_fun := getattr(sibling, qualifier, None):
        if qualifier_fun():
          class_credit = None

          if getattr(qualifier_fun(), 'CLASS', None) is not None:
            class_credit = 'class'
          if getattr(qualifier_fun(), 'CREDIT', None) is not None:
            class_credit = 'credit'

          if DEBUG:
            print(f'*** {qualifier}', file=sys.stderr)

          # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
          if qualifier == 'maxpassfail':
            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=qualifier_fun().NUMBER().getText(),
                                                      class_credit=class_credit))

          # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
          # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
          # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
          elif qualifier in ['maxperdisc', 'maxtransfer', 'minperdisc']:
            disciplines = qualifier_fun().SYMBOL()
            if isinstance(disciplines, list):
              disciplines = [d.getText() for d in disciplines]

            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=qualifier_fun().NUMBER().getText(),
                                                      class_credit=class_credit,
                                                      disciplines=disciplines))

          # maxspread       : MAXSPREAD NUMBER
          # minarea         : MINAREA NUMBER
          # mingrade        : MINGRADE NUMBER
          # minspread       : MINSPREAD NUMBER
          elif qualifier in ['maxspread', 'minarea', 'mingrade', 'minspread']:
            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=qualifier_fun().NUMBER().getText()))

          # minclass        : MINCLASS (NUMBER|RANGE) course_list
          # mincredit       : MINCREDIT (NUMBER|RANGE) course_list
          elif qualifier in ['minclass', 'mincredit']:
            if qualifier_fun().NUMBER() is not None:
              number_str = qualifier_fun().NUMBER().getText()
            else:
              number_str = None
            if qualifier_fun().RANGE() is not None:
              range_str = qualifier_fun().RANGE().getText()
            else:
              range_str = None
            course_list_obj = build_course_list(institution, qualifier_fun().course_list())
            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=number_str,
                                                      range=range_str,
                                                      course_list=course_list_obj['scribed_'
                                                                                  'courses']))

          # mingpa          : MINGPA NUMBER (course_list | expression)?
          elif qualifier == 'mingpa':
            course_list_obj = qualifier_fun().course_list()
            if course_list_obj:
              course_list_obj = build_course_list(institution, qualifier_fun().course_list())

            expression_str = qualifier_fun().expression()
            if expression_str:
              expression_str = expression.getText()

            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=qualifier_fun().NUMBER().getText(),
                                                      course_list=course_list_obj,
                                                      expression=expression_str))

          # ruletag         : RULE_TAG expression;
          # samedisc        : SAME_DISC expression
          elif qualifier in ['ruletag', 'samedisc']:
            qualifier_list.append(CourseListQualifier(qualifier,
                                                      expression=qualifier_fun().expression()
                                                      .getText()))

          # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
          elif qualifier == 'share':
            if qualifier_fun().DONT_SHARE():
              qualifier = 'dont_share'
            if qualifier_fun().CLASS():
              class_credit = 'class'
            elif qualifier_fun().CREDIT():
              class_credit = 'credit'
            else:
              class_credit = None
            if qualifier_fun().NUMBER():
              number = qualifier_fun().NUMBER().getText()
            else:
              number = None

            expression = qualifier_fun().expression()
            if expression:
              expression = expression.getText()

            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=number,
                                                      class_credit=class_credit,
                                                      expression=expression))

          else:
            qualifier_list.append(CourseListQualifier(qualifier))

  return qualifier_list


# build_string()
# -------------------------------------------------------------------------------------------------
def build_string(ctx) -> str:
  """ string          : DBL_QUOTE ~DBL_QUOTE* DBL_QUOTE;
      What’s between the double quotes has been tokenized, so the tokens have to be joined with a
      space between them.
      Ad hoc fixups: "C + +" is "C++"
  """
  assert ctx.__class__.__name__ == 'StringContext', (f'{ctx.__class__.__name} '
                                                     f'is not StringContext')
  fixups = {'C + +': 'C++'}
  tokens = [child.getText() for child in ctx.children]
  return_str = ' '.join(tokens[1:-1])
  for fixup in fixups:
    return_str = return_str.replace(fixup, fixups[fixup])
  return return_str


# build_course_list()
# -------------------------------------------------------------------------------------------------
def build_course_list(ctx, institution) -> dict:
  """
      The returned dict has the following structure:
        Scribed and Active course lists.
        scribed_courses     List of all (discipline, catalog_number, with_clause) tuples in the list
                            after distributing disciplines across catalog_numbers. (Show "BIOL 1, 2"
                            as "BIOL 1, BIOL 2")
        active_courses      Catalog information and WITH clause (if any) for all active courses that
                            match the scribed_courses list after expanding wildcards and
                            catalog_number ranges.

        list_type           'AND' or 'OR'
        exclusions          List of course_lists for excluded courses
        attributes          List of all attribute values the active courses list have in common,
                            currently limited to WRIC and BKCR

      Except clause: add active courses to except_courses list and remove from the active_courses
      Including clause: add to including_courses or missing_courses as the case may be.
        *** What is missing_courses supposed to be? Right now it's nothing, but it should be any
        *** scribed course that fails course catalog lookup. It would be for reporting purposes
        *** only. The issue is that we can only detect explicitly-scribed courses, not when there
        *** are wildcards involved.
  """
  if DEBUG:
    print(f'*** build_course_list({institution}, {ctx.__class__.__name__})', file=sys.stderr)
  if ctx is None:
    return None
  assert ctx.__class__.__name__ == 'Course_listContext', (f'{ctx.__class__.__name__} '
                                                          f'is not Course_listContext')

  # The dict to be returned:
  return_dict = {'tag': 'course_list',
                 'scribed_courses': [],
                 'list_type': '',
                 'qualifiers': [],
                 'label': None,
                 'active_courses': [],
                 'inactive_courses': [],
                 'except_courses': [],
                 'including_courses': [],
                 'missing_courses': [],
                 'attributes': []}
  # Shortcuts to the lists in return_dict
  scribed_courses = return_dict['scribed_courses']
  qualifiers = return_dict['qualifiers']
  active_courses = return_dict['active_courses']
  inactive_courses = return_dict['inactive_courses']
  except_courses = return_dict['except_courses']
  including_courses = return_dict['including_courses']
  missing_courses = return_dict['missing_courses']
  attributes = return_dict['attributes']

  # The Scribe context in which the list appeared
  return_dict['context_path'] = context_path(ctx)

  # Pick up the label, if there is one
  # It belongs to the parent (course_list_body, etc.)
  parent_ctx = ctx.parentCtx
  try:
    for child in parent_ctx.children:
      if child.__class__.__name__ == 'LabelContext':
        return_dict['label'] = child.string().getText().strip('"').replace('\'', '’')
  except AttributeError as ae:
    if DEBUG:
      print('No Label', file=sys.stderr)
    pass

  # Drill into ctx to determine which type of list
  if ctx.and_list():
    return_dict['list_type'] = 'AND'
    list_fun = ctx.and_list
  elif ctx.or_list():
    return_dict['list_type'] = 'OR'
    list_fun = ctx.or_list
  else:
    return_dict['list_type'] = 'None'
    list_fun = None

  scribed_courses += get_scribed_courses(ctx)
  if ctx.except_list():
    # Strip with_clause from courses to be excluded (it's always None anyway)
    except_courses += [[c[0], c[1]] for c in get_scribed_courses(ctx.except_list().course_list())]
  if ctx.include_list():
    including_courses += get_scribed_courses(ctx.include_list().course_list())

  qualifiers = get_qualifiers(ctx)

  # Active Courses (skip if no institution given, such as in a course list qualifier course list)
  all_blanket = True
  all_writing = True
  check_missing = True  # Unless there are wildcards or ranges
  conn = PgConnection()
  cursor = conn.cursor()
  for scribed_course in scribed_courses:
    # For display to users
    display_discipline, display_catalog_number, display_with_clause = scribed_course
    # For course db query
    discipline, catalog_number, with_clause = scribed_course

    # discipline part
    discp_op = '='

    if '@' in discipline:
      discp_op = '~*'
      check_missing = False
      discipline = '^' + discipline.replace('@', '.*') + '$'

    #   0@ means any catalog number < 100 according to the Scribe manual, but CUNY has no catalog
    #   numbers that start with zero. But other patterns might be used: 1@, for example.
    catalog_numbers = catalog_number.split(':')
    if len(catalog_numbers) == 1:
      if '@' in catalog_numbers[0]:
        check_missing = False
        catnum_clause = "catalog_number ~* '^" + catalog_numbers[0].replace('@', '.*') + "$'"
      else:
        catnum_clause = f"catalog_number = '{catalog_numbers[0]}'"
    else:
      check_missing = False
      low, high = catalog_numbers
      #  Assume no wildcards in range ...
      try:
        catnum_clause = f"""(numeric_part(catalog_number) >= {float(low)} and
                             numeric_part(catalog_number) <=' {float(high)}')
                         """
      except ValueError:
        #  ... but it looks like there were.
        check_missing = False

        #  Assume:
        #    - the range is being used for a range of course levels (1@:3@, for example)
        #    - catalog numbers are 3 digits (so 1@ means 100 to 199, for example
        #  Otherwise, 1@ would match 1, 10-19, 100-199, and 1000-1999, which would be strange, or
        #  at least fragile in the case of Lehman, which uses 2000-level numbers for blanket
        #  credit courses at the 200 level.
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
          # Either low or high is not in the form: \d+@
          catnum_clause = "catalog_number = ''"  # Will match no courses
    course_query = f"""
select institution, course_id, offer_nbr, discipline, catalog_number, title,
       requisites, description, course_status, contact_hours, max_credits, designation,
       replace(regexp_replace(attributes, '[A-Z]+:', '', 'g'), ';', ',')
       as attributes
  from cuny_courses
 where institution ~* '{institution}'
   and discipline {discp_op} '{discipline}'
   and {catnum_clause}
   order by discipline, numeric_part(catalog_number)
              """
    cursor.execute(course_query)
    if cursor.rowcount > 0:
      for row in cursor.fetchall():
        # skip excluded courses
        if (row.discipline, row.catalog_number) in except_courses:
          continue
        if row.course_status == 'A':
          active_courses.append((row.course_id, row.offer_nbr, row.discipline, row.catalog_number,
                                 row.title, with_clause))
        else:
          inactive_courses.append((row.course_id, row.offer_nbr, row.discipline, row.catalog_number,
                                   row.title, with_clause))
        if row.max_credits > 0 and 'BKCR' not in row.attributes:
          all_blanket = False
        if 'WRIC' not in row.attributes:
          all_writing = False

  conn.close()
  if len(active_courses) > 0:
    if all_blanket:
      attributes.append('Blanket Credit')
    if all_writing:
      attributes.append('Writing Intensive')

  # Make sure each scribed course was found. Check only if there were no wildcards scribed.
  if check_missing:
    found_courses = [(course[2], course[3]) for course in active_courses]
    found_courses += [(course[2], course[3]) for course in inactive_courses]
    for scribed_course in return_dict['scribed_courses']:
      if (scribed_course[0], scribed_course[1]) not in found_courses:
        missing_courses.append(scribed_course)

  return return_dict


# =================================================================================================
if __name__ == '__main__':
  parser = argparse.ArgumentParser('Test utils')
  parser.add_argument('-d', '--debug', action='store_true')
  parser.add_argument('-c', '--calendar_year', nargs=2)
  args = parser.parse_args()

  if args.calendar_year:
    result = catalog_years(args.calendar_year[0], args.calendar_year[1])
    print(f'{result.catalog_type} bulletin for {result.text}')
