#! /usr/local/bin/python3
""" Convert Lexer and metadata items into JSON elements
"""

from collections import namedtuple
from typing import List, Set, Dict, Tuple, Optional, Union, Any

import argparse
import os
import sys
from pprint import pprint

import json

from Any import ANY
from pgconnection import PgConnection

import dgw_handlers
# from course_list_qualifier import CourseListQualifier

DEBUG = os.getenv('DEBUG_UTILS')

# Dict of CUNY college names
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
college_names = {row.code: row.name for row in cursor.fetchall()}
conn.close()

CatalogYears = namedtuple('CatalogYears', 'catalog_type first_year last_year text')


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
  if isinstance(ctx, list):
    return ' '.join([expression_to_str(context.expression()) for context in ctx])
  assert class_name(ctx) == 'With_clause', f'{class_name(ctx)} is not \'With_clause\''
  return expression_to_str(ctx.expression())


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


# class_name()
# -------------------------------------------------------------------------------------------------
def class_name(obj):
  return obj.__class__.__name__.replace('Context', '')


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


# expression_to_str()
# -------------------------------------------------------------------------------------------------
def expression_to_str(ctx):
  """ Un-parse an expression, returning a space-separated string of tokens. Handles recursive
      definition of expression rule.

      expression      : expression relational_op expression
                      | expression logical_op expression
                      | expression ',' expression
                      | full_course
                      | discipline
                      | NUMBER
                      | QUESTION_MARK
                      | SYMBOL
                      | string
                      | CATALOG_NUMBER
                      | LP NONCOURSE? expression RP
  """
  assert class_name(ctx) == 'Expression', f'{class_name(ctx)} is not \'Expression\''
  return_str = ''
  for child in ctx.getChildren():
    if class_name(child) == 'Expression':
      return_str += expression_to_str(child) + ' '
    else:
      return_str += child.getText() + ' '

  return return_str.strip()


# concentration_list()
# -------------------------------------------------------------------------------------------------
def concentration_list(condition: str, institution: str, requirement_id: str) -> list:
  """ If the condition string contains equality operators (= or <>), lookup the latest concentration
      for that institution with that block_value.
      However, if there is no equality operator, find the subplans for the current major and return
      figure out what the matching scribe blocks are.
      The return array gives the titles of the concentrations, the requirement_ids, and hypertext
      links for use by htmlificization.
  """
  assert 'conc' in condition.lower(), f'No CONC in “{condition}”'
  print(f'*** concentration_list({condition}) not implemented yet', file=sys.stderr)
  return ['concentration_list not implemented yet']


# get_rules()
# -------------------------------------------------------------------------------------------------
def get_rules(ctx, institution, requirement_id):
  """ Return a list of rule dicts for the children of ctx.
  """

  return_list = []
  if isinstance(ctx, list):
    rule_list = ctx
  else:
    rule_list = [ctx]

  for rule in rule_list:
    rule_name = class_name(rule).lower()
    children = rule.getChildren()
    for child in children:
      rule_dict = dgw_handlers.dispatch(child, institution, requirement_id)
    return_list.append(rule_dict)

  return return_list


# get_requirements()
# -------------------------------------------------------------------------------------------------
# def get_requirements(ctx, institution, requirement_id):
#   """ These show up in the context of if-then or group_items in the body. Just build a dict with the
#       "requirement" tag and a list of dicts returned by the respective handlers.
#       It's not at all confusing that a requirement dict should contain a list of requirement dicts,
#       each of which will have its own tag, from this list:

#       requirement     : maxpassfail
#                       | maxperdisc
#                       | maxtransfer
#                       | minclass
#                       | mincredit
#                       | mingpa
#                       | mingrade
#                       | minperdisc
#                       | proxy_advice
#                       | samedisc
#                       | rule_tag
#                       | share
#   """
#   assert isinstance(ctx, list)
#   valid_requirements = ['maxpassfail', 'maxperdisc', 'maxtransfer', 'minclass', 'mincredit',
#                         'mingpa', 'mingrade', 'minperdisc', 'proxy_advice', 'samedisc', 'rule_tag']

#   return_list = []
#   for requirement in ctx:
#     for valid_requirement in valid_requirements:
#       if fun := getattr(requirement, valid_requirement, None):
#         if fun is not None and fun():
#           return_list.append(dgw_handlers.dispatch(fun(),
#                                                    institution,
#                                                    requirement_id))
#   return_list = return_list if len(return_list) > 0 else None
#   # if return_list is not None:
#   #   print('get_requirements returning: ', return_list)
#   return return_list

# get_display()
# -------------------------------------------------------------------------------------------------
def get_display(ctx: Any) -> str:
  """ Gather subsstrings from a list of display items into a single string.
  """
  if ctx.display():
    if instance(ctx.display(), list):
      display_str = ''
      for item in ctx.display():
        display_str += item.string().getText().strip(' "') + ' '
    else:
      display_str = ctx.display().getText().strip(' "')
  else:
    display_str = None

  return display_str


# get_label()
# -------------------------------------------------------------------------------------------------
def get_label(ctx: Any) -> str:
  """ Like get_display, only for labels.
  """
  if ctx.label():
    if isinstance(ctx.label(), list):
      label_str = ''
      for context in ctx.label():
        label_str += ' '.join([context.string().getText().strip(' "')])
    else:
      label_str = ctx.label().string().getText().strip(' "')
  else:
    label_str = None

  return label_str


# get_scribed_courses()
# -------------------------------------------------------------------------------------------------
def get_scribed_courses(course_item, list_items: list) -> list:
  """ Generate list of (discipline, catalog_number, with_clause) tuples for courses in a course
      list. Distribute wildcards across the list so that each “scribed course” is a complete
      (discipline, catalog_number, with_clause) tuple, even if the with clause is None.

      NOT IMPLEMENTED YET: For analysis purposes, with clauses should be logged.

      course_list     : course_item (and_list | or_list)? (except_list | include_list)*
                        proxy_advice? label?;
      full_course     : discipline catalog_number with_clause*;   // Used only in expressions
      course_item     : area_start? discipline? catalog_number with_clause* area_end?;
      and_list        : (list_and area_end? course_item)+ ;
      or_list         : (list_or area_end? course_item)+ ;
      except_list     : EXCEPT course_item (and_list | or_list)?;     // Always OR
      include_list    : INCLUDING course_item (and_list | or_list)?;  // Always AND
      catalog_number  : symbol | NUMBER | CATALOG_NUMBER | WILD;
      discipline      : symbol
                      | string // For "SPEC." at BKL
                      | WILD
                      // Include keywords that appear as discipline names
                      | BLOCK
                      | IS;
  """
  assert class_name(course_item) == 'Course_item', (f'“{class_name(ctx)}” is not “Course_item”')
  if DEBUG:
    print(f'*** get_scribed_courses({class_name(course_item)})', file=sys.stderr)

  # The list of (discipline: str, catalog_number: str, with_clause: str) tuples to return.
  scribed_courses = []

  # The course_item at the start of the list has to have with both a discipline and catalog number,
  # but sometimes just a wildcard is given.
  discipline, catalog_number, with_clause = (None, None, None)

  catalog_number = course_item.catalog_number().getText().strip()
  # The next two might be absent
  try:
    discipline = course_item.discipline().getText()
  except AttributeError as ae:
    discipline = '@'
  try:
    with_list = course_item.with_clause()
    for with_ctx in with_list:
      if class_name(with_ctx) == 'With_clause':
        if with_clause is None:
          with_clause = _with_clause(with_ctx)
        else:
          with_clause += ' ' + _with_clause(with_ctx)
  except AttributeError as ae:
    # No with clause
    pass

  # Enter the first course
  if course_item.area_start():
    scribed_courses.append('area_start')
  scribed_courses.append((discipline, catalog_number, with_clause))
  if course_item.area_end():
    scribed_courses.append('area_end')
  # For the remaining scribed courses (if any), the discipline determined above will be the "seed"
  # for distributing across succeeding courses where the discipline is not specified.
  catalog_number = None  # Must be present
  with_clause = None     # Does not distribute (as discipline does)
  for list_item in list_items:
    if list_item.area_end():
      scribed_courses.append('area_end')
    if list_item.area_start():
      scribed_courses.append('area_start')
    if list_item.discipline():
      discipline = list_item.discipline().getText().strip()
    if list_item.catalog_number():
      catalog_number = list_item.catalog_number().getText().strip()
    if list_item.with_clause():
      with_clause = _with_clause(list_item.with_clause())
    assert catalog_number is not None, (f'Course Item with no catalog number: '
                                        f'{list_item.getText()}')
    scribed_courses.append((discipline, catalog_number, with_clause))
    if list_item.area_end():
      scribed_courses.append('area_end')

  if DEBUG:
    print(f'\n{scribed_courses=}', file=sys.stderr)

  return scribed_courses


# get_course_list_qualifiers()
# -------------------------------------------------------------------------------------------------
# def get_course_list_qualifiers(institution, ctx):
#   """ Use parser info to generate and return a possibly-empty list of CourseListQualifier objects.
#   """
#   valid_qualifiers = ['dont_share', 'maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer',
#                       'minarea', 'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc',
#                       'minspread', 'ruletag', 'samedisc', 'share']
#   qualifier_list = []
#   siblings = ctx.parentCtx.getChildren()
#   for sibling in siblings:
#     for qualifier in valid_qualifiers:
#       if qualifier_fun := getattr(sibling, qualifier, None):
#         if qualifier_fun():
#           class_credit = None

#           if getattr(qualifier_fun(), 'CLASS', None) is not None:
#             class_credit = 'class'
#           if getattr(qualifier_fun(), 'CREDIT', None) is not None:
#             class_credit = 'credit'

#           if DEBUG:
#             print(f'*** {qualifier}', file=sys.stderr)

#           # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
#           if qualifier == 'maxpassfail':
#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       number=qualifier_fun().NUMBER().getText(),
#                                                       class_credit=class_credit))

#           # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
#           # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
#           # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
#           elif qualifier in ['maxperdisc', 'maxtransfer', 'minperdisc']:
#             disciplines = qualifier_fun().SYMBOL()
#             if isinstance(disciplines, list):
#               disciplines = [d.getText() for d in disciplines]

#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       number=qualifier_fun().NUMBER().getText(),
#                                                       class_credit=class_credit,
#                                                       disciplines=disciplines))

#           # maxspread       : MAXSPREAD NUMBER
#           # minarea         : MINAREA NUMBER
#           # mingrade        : MINGRADE NUMBER
#           # minspread       : MINSPREAD NUMBER
#           elif qualifier in ['maxspread', 'minarea', 'mingrade', 'minspread']:
#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       number=qualifier_fun().NUMBER().getText()))

#           # minclass        : MINCLASS (NUMBER|RANGE) course_list
#           # mincredit       : MINCREDIT (NUMBER|RANGE) course_list
#           elif qualifier in ['minclass', 'mincredit']:
#             if qualifier_fun().NUMBER() is not None:
#               number_str = qualifier_fun().NUMBER().getText()
#             else:
#               number_str = None
#             if qualifier_fun().RANGE() is not None:
#               range_str = qualifier_fun().RANGE().getText()
#             else:
#               range_str = None
#             course_list_obj = build_course_list(qualifier_fun().course_list(),
#                                                 institution, requirement_id)
#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       number=number_str,
#                                                       range=range_str,
#                                                       course_list=course_list_obj['scribed_'
#                                                                                   'courses']))

#           # mingpa          : MINGPA NUMBER (course_list | expression)?
#           elif qualifier == 'mingpa':
#             course_list_obj = qualifier_fun().course_list()
#             if course_list_obj:
#               course_list_obj = build_course_list(qualifier_fun().course_list(),
#                                                   institution, requirement_id)

#             expression_str = qualifier_fun().expression()
#             if expression_str:
#               expression_str = expression.getText()

#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       number=qualifier_fun().NUMBER().getText(),
#                                                       course_list=course_list_obj,
#                                                       expression=expression_str))

#           # ruletag         : RULE_TAG expression;
#           # samedisc        : SAME_DISC expression
#           elif qualifier in ['ruletag', 'samedisc']:
#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       expression=qualifier_fun().expression()
#                                                       .getText()))

#           # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
#           elif qualifier == 'share':
#             if qualifier_fun().DONT_SHARE():
#               qualifier = 'dont_share'
#             if qualifier_fun().CLASS():
#               class_credit = 'class'
#             elif qualifier_fun().CREDIT():
#               class_credit = 'credit'
#             else:
#               class_credit = None
#             if qualifier_fun().NUMBER():
#               number = qualifier_fun().NUMBER().getText()
#             else:
#               number = None

#             expression = qualifier_fun().expression()
#             if expression:
#               expression = expression.getText()

#             qualifier_list.append(CourseListQualifier(qualifier,
#                                                       number=number,
#                                                       class_credit=class_credit,
#                                                       expression=expression))

#           else:
#             qualifier_list.append(CourseListQualifier(qualifier))

#   return qualifier_list


# get_group_items()
# -------------------------------------------------------------------------------------------------
def get_group_items(ctx: list, institution: str, requirement_id: str) -> list:
  """ group_list      : group_item (logical_op group_item)*; // logical_op is always OR
      group_item      : LP
                        (  block
                         | blocktype
                         | course_list
                         | class_credit_body
                         | group
                         | noncourse
                         | rule_complete
                        )
                        requirement* label?
                        RP
  """
  return_list = []
  for group_item_context in ctx.group_item():
    children = group_item_context.getChildren()

    for child in children:
      item_class = class_name(child)

      # Ignore LP | RP
      if item_class.lower() == 'terminalnodeimpl':
        continue
      return_list.append(dgw_handlers.dispatch(child, institution, requirement_id))

    if group_item_context.qualifier():
      return_list[-1].update({'group item requirement': 'Not yet'})

    if group_item_context.label():
      return_list[-1].update({'group item label': 'Not yet'})

  return return_list


# get_qualifiers()
# -------------------------------------------------------------------------------------------------
def get_qualifiers(ctx: any, institution: str, requirement_id: str) -> list[dict]:
  """ Build qualifier-specific dicts for various possible qualifiers. The grammar, and this method,
      recognize any qualifier, even though Degree Works allows only certain subsets in different
      contexts. On the other hand, we ignore qualifiers that apply to the operation of degree audits
      but which are not part of a degree or program’s requirement structure.

      The ctx can be either a single context of a list of them. But within a list, we don't expect
      the same qualifier to be repeated.

      And Ignore the next paragraph.

      The ctx parameter might be for a list of grammar-rules or for a single grammar-rule. In the
      latter case, get a list of all the siblings of this ctx (i.e., the children of this rule's
      parents in the parse tree). If this seems confusing, it's because it is.

  The list of qualifiers recognized here:
  qualifier       : maxpassfail
                  | maxperdisc
                  | maxspread
                  | maxtransfer
                  | minarea
                  | minclass
                  | mincredit
                  | mingpa
                  | mingrade
                  | minperdisc
                  | minspread
                  | proxy_advice
                  | rule_tag
                  | samedisc
                  | share
  """

  valid_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                      'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                      'proxy_advice', 'rule_tag', 'samedisc', 'share']

  if DEBUG:
    print(f'get_qualifiers({class_name(ctx)})', file=sys.stderr)

  if isinstance(ctx, list):
    contexts = ctx
  else:
    contexts = [ctx]
  qualifier_dict = dict()
  for context in contexts:

    class_credit = None
    if getattr(context, 'class_credit', None):
      # Class or credit is an attribute of several qualifiers. Extract it here.
      if getattr(qualifier_func(), 'CLASS', None) is not None:
        class_credit = 'class'
      if getattr(qualifier_func(), 'CREDIT', None) is not None:
        class_credit = 'credit'

    # See which qualifiers, if any, are part of this context
    for valid_qualifier in valid_qualifiers:
      if qualifier_func := getattr(context, valid_qualifier, None):
        if qualifier_ctx := qualifier_func():
          print(f'Got {valid_qualifier}', file=sys.stderr)
          assert valid_qualifier not in qualifier_dict.keys()

          # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
          if valid_qualifier == 'maxpassfail':
            qualifier_dict[valid_qualifier] = {'number': qualifier_ctx.NUMBER().getText(),
                                               'class_credit': class_credit}
            print('maxpassfail says', qualifier_dict, file=sys.stderr)

          # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
          # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
          # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
          elif qualifier in ['maxperdisc', 'maxtransfer', 'minperdisc']:
            disciplines = qualifier_ctx.SYMBOL()
            if isinstance(disciplines, list):
              disciplines = [d.getText() for d in disciplines]

            qualifier_dict[valid_qualifier] = {'number': qualifier_ctx.NUMBER().getText(),
                                               'class_credit': class_credit,
                                               'disciplines': disciplines}

          # maxspread       : MAXSPREAD NUMBER
          # minarea         : MINAREA NUMBER
          # mingrade        : MINGRADE NUMBER
          # minspread       : MINSPREAD NUMBER
          elif valid_qualifier in ['maxspread', 'minarea', 'mingrade', 'minspread']:
            qualifier_dict[valid_qualifier] = qualifier_ctx.NUMBER().getText()

          # minclass        : MINCLASS NUMBER course_list tag? display* label?;
          # mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
          elif qualifier in ['minclass', 'mincredit']:
            # build_course_list returns its own dict, with "course_list" as the key, so we start
            # with that, and add the number, display, and label elements to that.
            qualifier_dict[valid_qualifier] = build_course_list(qualifier_ctx.course_list(),
                                                                institution, requirement_id)
            qualifier_dict[valid_qualifier]['number'] = qualifier_ctx.NUMBER().getText()
            if qualifier_ctx.display():
              qualifier_dict[valid_qualifier]['display'] = get_display(qualifier_ctx)

        #   # mingpa          : MINGPA NUMBER (course_list | expression)?
        #   elif qualifier == 'mingpa':
        #     course_list_obj = qualifier_func().course_list()
        #     if course_list_obj:
        #       course_list_obj = build_course_list(qualifier_func().course_list(),
        #                                           institution, requirement_id)

        #     expression_str = qualifier_func().expression()
        #     if expression_str:
        #       expression_str = expression.getText()

        #     qualifier_list.append({'number': qualifier_func().NUMBER().getText(),
        #                            'course_list': course_list_obj,
        #                            'expression': expression_str})

        #   # ruletag         : RULE_TAG expression;
        #   # samedisc        : SAME_DISC expression
        #   elif qualifier in ['ruletag', 'samedisc']:
        #     qualifier_list.append({'expression': qualifier_func().expression().getText()})

        #   # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
        #   elif qualifier == 'share':
        #     if qualifier_func().DONT_SHARE():
        #       qualifier = 'dont_share'

        #     if qualifier_func().NUMBER():
        #       number = qualifier_func().NUMBER().getText()
        #     else:
        #       number = None

        #     expression = qualifier_func().expression()
        #     if expression:
        #       expression = expression.getText()

        #     qualifier_list.append({'number': number,
        #                            'class_credit': class_credit,
        #                            'expression': expression})

        #   else:
        #     print(f'Unrecognized qualifier: {qualifier} in {context_path(ctx)} for {institution}',
        #           file=sys.stderr)
        #     # qualifier_list.append({'tag': qualifier})
    pprint(qualifier_dict, stream=sys.stderr)
  return {'qualifiers': qualifier_dict}


# num_class_or_num_credit(ctx)
# -------------------------------------------------------------------------------------------------
def num_class_or_num_credit(ctx) -> dict:
  """ A context can have one num_classes, one num_credits, or both. When both are allowed, they will
      be lists of len 1, but if only one is allowed, it will be a scalar. Depends on the context.
      num_classes     : NUMBER CLASS allow_clause?;
      num_credits     : NUMBER CREDIT allow_clause?;
  """
  if DEBUG:
    print(f'{class_name(ctx)}', file=sys.stderr)
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

  return {'num_classes': num_classes,
          'allow_classes': allow_classes,
          'num_credits': num_credits,
          'allow_credits': allow_credits,
          'conjunction': conjunction}


# build_string()
# -------------------------------------------------------------------------------------------------
def build_string(ctx) -> str:
  """ string          : DBL_QUOTE ~DBL_QUOTE* DBL_QUOTE;
      What’s between the double quotes has been tokenized, so the tokens have to be joined with a
      space between them.
      Ad hoc fixups:
        Change "C + +" to "C++"
        - add others as needed
  """
  assert class_name(ctx) == 'String', (f'{class_name(ctx)} 'f'is not String')
  fixups = {'C + +': 'C++'}
  tokens = [child.getText() for child in ctx.children]
  return_str = ' '.join(tokens[1:-1])
  for fixup in fixups:
    return_str = return_str.replace(fixup, fixups[fixup])
  return return_str


# build_course_list()
# -------------------------------------------------------------------------------------------------
def build_course_list(ctx, institution, requirement_id) -> dict:
  """
      course_list     : course_item (and_list | or_list)? (except_list | include_list)*
                        proxy_advice? label?;
      full_course     : discipline catalog_number with_clause*;   // Used only in expressions
      course_item     : area_start? discipline? catalog_number with_clause* area_end?;
      and_list        : (list_and area_end? course_item)+ ;
      or_list         : (list_or area_end? course_item)+ ;
      except_list     : EXCEPT course_item (and_list | or_list)?;     // Always OR
      include_list    : INCLUDING course_item (and_list | or_list)?;  // Always AND

      The returned dict has the following structure:

        scribed_courses     List of all (discipline, catalog_number, with_clause) tuples in the list
                            after distributing disciplines across catalog_numbers. (Show "BIOL 1, 2"
                            as "BIOL 1, BIOL 2")
        active_courses      Catalog information and WITH clause (if any) for all active courses that
                            match the scribed_courses list after expanding wildcards and
                            catalog_number ranges.
        inactive_courses    Catalog information for all inactive courses that match the scribed
                            course list after wildcard and range expansions.
        missing_courses     Explicitly-scribed courses that do not exist in CUNYfirst.
        qualifiers          Qualifiers that apply to all courses in the list
        label               The name of the property (head) or requirement (body)
        course_areas        List of active_courses divided into distribution areas; presumably the
                            full course list will have a MinArea qualifier, but this is not checked
                            here. Omit inactive, missing, and except courses because they are
                            handled in the full course list.
        except_courses      Scribed list used for culling from active_courses.
        include_courses     Like except_courses, except this list is not actually used for anything
                            in this method.

        list_type           'AND' or 'OR'
        attributes          List of all attribute values the active courses list have in common,
                            currently limited to WRIC and BKCR

      Missing courses: Any explicitly-scribed course that fails course catalog lookup. Obviously,
      wildcard-expanded lists will find only active and inactive courses, and thus will never add
      to the missing courses list

      The except_courses list is an OR list no matter how it is scribed. (Ellucian accepts either
      conjunction, even though documentation says AND is illegal.)

      The include_courses list is an AND list no matter how it is scribed. (Ellucian documentation
      makes this explicit.)

  """
  if DEBUG:
    print(f'*** build_course_list({institution}, {class_name(ctx)})', file=sys.stderr)
  if ctx is None:
    return None
  assert class_name(ctx) == 'Course_list', f'{class_name(ctx)} is not Course_list'

  # The dict to be returned:
  return_dict = {'scribed_courses': [],
                 'list_type': '',
                 'qualifiers': ['I don’t think so'],
                 'label': None,
                 'active_courses': [],
                 'inactive_courses': [],
                 'except_courses': [],
                 'include_courses': [],
                 'course_areas': [],
                 'missing_courses': [],
                 'attributes': []}
  # Shortcuts to the lists in return_dict
  scribed_courses = return_dict['scribed_courses']
  qualifiers = return_dict['qualifiers']
  active_courses = return_dict['active_courses']
  inactive_courses = return_dict['inactive_courses']
  except_courses = return_dict['except_courses']
  include_courses = return_dict['include_courses']
  missing_courses = return_dict['missing_courses']
  attributes = return_dict['attributes']

  # The Scribe context in which the list appeared
  return_dict['context_path'] = context_path(ctx)

  # Pick up the label, if there is one
  return_dict['label'] = get_label(ctx)

  # get context of the required course_item and list of optional additional course_items.
  course_item = ctx.course_item()
  if ctx.and_list():
    return_dict['list_type'] = 'AND'
    list_items = ctx.and_list().course_item()
  elif ctx.or_list():
    return_dict['list_type'] = 'OR'
    list_items = ctx.or_list().course_item()
  else:
    return_dict['list_type'] = None
    list_items = []

  scribed_courses += get_scribed_courses(course_item, list_items)

  # Sublists
  if ctx.except_list():
    course_item = ctx.except_list()[0].course_item()
    # Ellucian allows either AND or OR even though it has to be OR
    if ctx.except_list()[0].and_list():
      list_items = ctx.except_list()[0].and_list().course_item()
    elif ctx.except_list()[0].or_list():
      list_items = ctx.except_list()[0].or_list().course_item()
    else:
      list_items = []
    except_courses += get_scribed_courses(course_item, list_items)

  if ctx.include_list():
    course_item = ctx.include_list()[0].course_item()
    # Ellucian allows either AND or OR even though it has to be OR
    if ctx.include_list()[0].and_list():
      list_items = ctx.include_list()[0].and_list().course_item()
    elif ctx.include_list()[0].or_list():
      list_items = ctx.include_list()[0].or_list().course_item()
    else:
      list_items = []
    include_courses += get_scribed_courses(course_item, list_items)

  # Qualifiers: course lists don't have them.
  # qualifiers = get_qualifiers(ctx.qualifier(), institution, requirement_id)

  # Active Courses (skip if no institution given, such as in a course list qualifier course list)
  all_blanket = True
  all_writing = True
  check_missing = True  # Unless there are wildcards or ranges
  conn = PgConnection()
  cursor = conn.cursor()

  current_area = None
  for scribed_course in scribed_courses:

    # Start and end course areas. Active courses will be added to current_area if it exists
    if scribed_course == 'area_start':
      current_area = []
      continue
    if scribed_course == 'area_end':
      if current_area and len(current_area) > 0:
        return_dict['course_areas'].append(current_area)
      current_area = None
      continue

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
       requisites, description, course_status, contact_hours, min_credits, max_credits, designation,
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
        if (row.discipline, row.catalog_number, ANY) in except_courses:
          continue
        if row.min_credits == row.max_credits:
          credits = f'{row.min_credits:0.1f}'
        else:
          credits = f'{row.min_credits:0.1f}:{row.max_credits:0.1f}'
        if row.course_status == 'A':
          active_course_tuple = (row.course_id, row.offer_nbr, row.discipline, row.catalog_number,
                                 row.title, credits, with_clause)
          active_courses.append(active_course_tuple)
          if current_area is not None:
            current_area.append(active_course_tuple)
          # Check BKCR and WRIC only for active courses
          if row.max_credits > 0 and 'BKCR' not in row.attributes:
            # if all_blanket:
            #   print(f'*** wet blanket: {row.course_id} {row.discipline} {row.catalog_number} '
            #         f'{row.max_credits} {row.attributes}', file=sys.stderr)
            all_blanket = False
          if 'WRIC' not in row.attributes:
            all_writing = False
        else:
          inactive_courses.append((row.course_id, row.offer_nbr, row.discipline, row.catalog_number,
                                   row.title, credits, with_clause))

  conn.close()
  if len(active_courses) > 0:
    if all_blanket:
      attributes.append('Blanket Credit')
    if all_writing:
      attributes.append('Writing Intensive')

  # Clean out any (area_start and area_end) strings from the scribed_courses list
  return_dict['scribed_courses'] = [item for item in return_dict['scribed_courses']
                                    if isinstance(item, tuple)]

  # Make sure each scribed course was found. Check only if there were no wildcards scribed.
  if check_missing:
    found_courses = [(course[2], course[3]) for course in active_courses]
    found_courses += [(course[2], course[3]) for course in inactive_courses]
    for scribed_course in return_dict['scribed_courses']:
      if (scribed_course[0], scribed_course[1]) not in found_courses:
        missing_courses.append(scribed_course)

  return {'course_list': return_dict}


# =================================================================================================
if __name__ == '__main__':
  parser = argparse.ArgumentParser('Test utils')
  parser.add_argument('-d', '--debug', action='store_true')
  parser.add_argument('-c', '--calendar_year', nargs=2)
  args = parser.parse_args()

  if args.calendar_year:
    result = catalog_years(args.calendar_year[0], args.calendar_year[1])
    print(f'{result.catalog_type} bulletin for {result.text}')
