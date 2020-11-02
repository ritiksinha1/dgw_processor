#! /usr/local/bin/python3
""" Convert Lexer and metadata items into JSON elements
"""

from collections import namedtuple
from typing import List, Set, Dict, Tuple, Optional, Union

import argparse
import os
import sys

import json

from Any import ANY
from pgconnection import PgConnection

import dgw_handlers
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


# get_rules()
# -------------------------------------------------------------------------------------------------
def get_rules(ctx, institution):
  """ Return a list of rules that appear in either the head or body of a block. The parse tree has
      already differentiated between the head and the body so, for example, if_then_head and
      if_then_body will never both appear.

      Given a head_rule or body_rule context, determine which of the following productions are
      present by testing each one's visitor function to see whether it returns None or not. And if
      not, generate a production-specific dict, which gets added to the returned list of dicts.

  """
  possible_rules = ['if_then_head', 'if_then_body', 'block', 'blocktype', 'class_credit_head',
                    'class_credit_body', 'copy_rules', 'lastres', 'maxcredit', 'maxpassfail',
                    'maxterm', 'maxtransfer', 'minclass', 'mincredit', 'mingpa', 'mingrade',
                    'minperdisc', 'minres', 'minterm', 'noncourse', 'proxy_advice', 'remark',
                    'rule_complete', 'share', 'subset']

  return_list = []
  if 'group' in class_name(ctx).lower():
    # List of rules
    list_of_rules = ctx.head_rule()
  else:
    # Single rule; convert it to a list
    list_of_rules = [ctx]

  for rule in list_of_rules:
    for possible_rule in possible_rules:
      rule_fun = getattr(rule, possible_rule, None)
      if rule_fun and rule_fun() is not None:
        rule_dict = {'tag': possible_rule}

        # Use the value of possible_rule to dispatch the corresponding handler, with rule_fun()
        # providing the context.
        # =========================================================================================

        # These are head-body dependent
        # -----------------------------------------------------------------------------------------
        # if_then_head
        if possible_rule == 'if_then_head':
          # This can be done by the handler
          return_list.append(dgw_handlers.if_then_head(rule_fun(), institution))

        # if_then_body
        if possible_rule == 'if_then_body':
          # This can be done by the handler
          return_list.append(dgw_handlers.if_then_body(rule_fun(), institution))

        # class_credit_head
        if possible_rule == 'class_credit_head':
          return_list.append(dgw_handlers.class_credit_head(rule_fun(), institution))

        # class_credit_body
        if possible_rule == 'class_credit_body':
          return_list.append(dgw_handlers.class_credit_body(rule_fun(), institution))

        # These are independent of whether they are in the head or the body
        # -----------------------------------------------------------------------------------------
        # block
        if possible_rule == 'block':
          return_list.append(dgw_handlers.block(rule_fun(), institution))

        # blocktype
        if possible_rule == 'blocktype':
          return_list.append(dgw_handlers.blocktype(rule_fun(), institution))

        # copy_rules
        if possible_rule == 'copy_rules':
          return_list.append(dgw_handlers.copy_rules(rule_fun(), institution))

        # lastres
        if possible_rule == 'lastres':
          return_list.append(dgw_handlers.lastres(rule_fun(), institution))

        # maxcredit
        if possible_rule == 'maxcredit':
          return_list.append(dgw_handlers.maxcredit(rule_fun(), institution))

        # maxpassfail
        if possible_rule == 'maxpassfail':
          return_list.append(dgw_handlers.maxpassfail(rule_fun(), institution))

        # maxterm
        if possible_rule == 'maxterm':
          return_list.append(dgw_handlers.maxterm(rule_fun(), institution))

        # maxtransfer
        if possible_rule == 'maxtransfer':
          return_list.append(dgw_handlers.maxtransfer(rule_fun(), institution))

        # maxtransfer
        if possible_rule == 'maxtransfer':
          return_list.append(dgw_handlers.maxtransfer(rule_fun(), institution))

        # minclass
        if possible_rule == 'minclass':
          return_list.append(dgw_handlers.minclass(rule_fun(), institution))

        # mincredit
        if possible_rule == 'mincredit':
          return_list.append(dgw_handlers.mincredit(rule_fun(), institution))

        # mingpa
        if possible_rule == 'mingpa':
          return_list.append(dgw_handlers.mingpa(rule_fun(), institution))

        # mingrade
        if possible_rule == 'mingrade':
          return_list.append(dgw_handlers.mingrade(rule_fun(), institution))

        # minperdisc
        if possible_rule == 'minperdisc':
          return_list.append(dgw_handlers.minperdisc(rule_fun(), institution))

        # minres
        if possible_rule == 'minres':
          return_list.append(dgw_handlers.minres(rule_fun(), institution))

        # minterm
        if possible_rule == 'minterm':
          return_list.append(dgw_handlers.minterm(rule_fun(), institution))

        # noncourse
        if possible_rule == 'noncourse':
          return_list.append(dgw_handlers.noncourse(rule_fun(), institution))

        # remark
        if possible_rule == 'remark':
          return_list.append(dgw_handlers.remark(rule_fun(), institution))

        # rule_complete
        if possible_rule == 'rule_complete':
          return_list.append(dgw_handlers.rule_complete(rule_fun(), institution))

        # share
        if possible_rule == 'share':
          return_list.append(dgw_handlers.share(rule_fun(), institution))

        # subset
        if possible_rule == 'subset':
          return_list.append(dgw_handlers.subset(rule_fun(), institution))

  # print(f'{return_list=}', file=sys.stderr)
  return return_list


# get_requirements()
# -------------------------------------------------------------------------------------------------
def get_requirements(ctx, institution):
  """
  """
  assert isinstance(ctx, list)
  for context in ctx:
    print(f'get_requirements not implemented yet: {context_path(context)}', file=sys.stderr)
  return 'Requirements list not implemented yet'


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

  catalog_number = ctx.course_item().catalog_number().getText().strip()
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
          discipline = child.getText().strip()
        elif child.__class__.__name__ == 'Catalog_numberContext':
          catalog_number = child.getText().strip()
        elif child.__class__.__name__ == 'With_clauseContext':
          with_clause = child.getText()   # Need to interpret this
          with_clause = _with_clause(child)
          # print(discipline, catalog_number, with_clause)
        else:
          # This is where square brackets show up
          print(f'Unhandled token: {child.getText()}',
                file=sys.stderr)
      assert catalog_number is not None, (f'Course Item with no catalog number: '
                                          f'{course_item.getText()}')
      scribed_courses.append((discipline, catalog_number, with_clause))

  return scribed_courses


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
            course_list_obj = build_course_list(qualifier_fun().course_list(), institution)
            qualifier_list.append(CourseListQualifier(qualifier,
                                                      number=number_str,
                                                      range=range_str,
                                                      course_list=course_list_obj['scribed_'
                                                                                  'courses']))

          # mingpa          : MINGPA NUMBER (course_list | expression)?
          elif qualifier == 'mingpa':
            course_list_obj = qualifier_fun().course_list()
            if course_list_obj:
              course_list_obj = build_course_list(qualifier_fun().course_list(), institution)

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


# get_group_list()
# -------------------------------------------------------------------------------------------------
def get_group_list(ctx: list) -> list:
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
  for group_item in ctx.group_item():
    childs = group_item.getChildren()
    for child in childs:
      item_class = class_name(child)
      if item_class == 'TerminalNodeImpl':
        pass
      elif item_class == 'Block':
        return_list.append({'tag': 'block'})
      elif item_class == 'Blocktype':
        return_list.append({'tag': 'blocktype'})
      elif item_class == 'Course_list':
        return_list.append({'tag': 'course_list'})
      elif item_class == 'Class_credit_body':
        return_list.append({'tag': 'class_credit_body'})
      elif item_class == 'Group':
        return_list.append({'tag': 'group'})
      elif item_class == 'Noncourse':
        return_list.append({'tag': 'noncourse'})
      elif item_class == 'Rule_complete':
        return_list.append({'tag': 'rule_complete'})
      else:
        return_list.append({'tag': f'Unknown group_item: “{item_class}”'})
    if group_item.requirement():
      return_list[-1].update({'requirement': 'Not yet'})
    if group_item.label():
      return_list[-1].update({'label': 'Not yet'})

  return return_list


# get_qualifiers()
# -------------------------------------------------------------------------------------------------
def get_qualifiers(ctx, institution):
  """ Build qualifier-specific dicts for various possible qualifiers.
      The ctx parameter might be for a list of grammar-rules or for a single grammar-rule. In the
      latter case, get a list of all the siblings of this ctx (i.e., the children of this rule's
      parents in the parse tree). If this seems confusing, it's because it is.
  """
  valid_qualifiers = ['dont_share', 'maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer',
                      'minarea', 'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc',
                      'minspread', 'ruletag', 'samedisc', 'share']
  qualifier_list = []
  if isinstance(ctx, list):
    siblings = ctx
  else:
    siblings = ctx.parentCtx.getChildren()
  for sibling in siblings:
    for qualifier in valid_qualifiers:
      # See whether the sibling has this qualifier
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
            course_list_obj = build_course_list(qualifier_fun().course_list(), institution)
            qualifier_list.append({'tag': qualifier,
                                   'number': qualifier_fun().NUMBER().getText(),
                                   'courses': course_list_obj})

          # mingpa          : MINGPA NUMBER (course_list | expression)?
          elif qualifier == 'mingpa':
            course_list_obj = qualifier_fun().course_list()
            if course_list_obj:
              course_list_obj = build_course_list(qualifier_fun().course_list(), institution)

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
            if qualifier_fun().DONT_SHARE():
              qualifier = 'dont_share'

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
            print(f'Unrecognized qualifier: {qualifier} in {context_path(ctx)} for {institution}')
            qualifier_list.append({'tag': qualifier})

  return qualifier_list


# num_class_or_num_credit(ctx)
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
      Including clause: add to include_courses or missing_courses as the case may be.
        *** What is missing_courses supposed to be? Right now it's nothing, but it should be any
        *** scribed course that fails course catalog lookup. It would be for reporting purposes
        *** only. The issue is that we can only detect explicitly-scribed courses, not when there
        *** are wildcards involved.
  """
  if DEBUG:
    print(f'*** build_course_list({institution}, {class_name(ctx)})', file=sys.stderr)
  if ctx is None:
    return None
  assert class_name(ctx) == 'Course_list', f'{class_name(ctx)} is not Course_list'

  # The dict to be returned:
  return_dict = {'tag': 'course_list',
                 'scribed_courses': [],
                 'list_type': '',
                 'qualifiers': [],
                 'label': None,
                 'active_courses': [],
                 'inactive_courses': [],
                 'except_courses': [],
                 'include_courses': [],
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
  if ctx.label():
    return_dict['label'] = ctx.label().string().getText().strip('"').replace('\'', '’')

  # The label and qualifiers may be attached to the parent (course_list_body), so the following
  # code will be removed once they are handled there properly.
  # # It might appear in the parent (course_list_body)
  # parent_ctx = ctx.parentCtx
  # try:
  #   # print(f'\n{context_path(ctx)}')
  #   for child in parent_ctx.children:
  #     # print(f'  {class_name(child)}')
  #     if class_name(child) == 'Label':
  #       if return_dict['label'] is not None:
  #         print(f'Conflicting labels at {context_path(ctx)}', file=sys.stderr)
  #       return_dict['label'] = child.string().getText().strip('"').replace('\'', '’')
  #       # print(return_dict['label'])
  # except AttributeError as ae:
  #     print(f'Label Error in build_course_list(): {context_path(ctx)}', file=sys.stderr)

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
    except_courses += get_scribed_courses(ctx.except_list().course_list())
  if ctx.include_list():
    include_courses += get_scribed_courses(ctx.include_list().course_list())

  qualifiers = get_qualifiers(ctx, institution)

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
    if DEBUG:
      print(f'{discp_op=} {discipline=} {catnum_clause=}', file=sys.stderr)
    cursor.execute(course_query)
    if cursor.rowcount > 0:
      for row in cursor.fetchall():
        # skip excluded courses
        if (row.discipline, row.catalog_number, ANY) in except_courses:
          continue
        if row.course_status == 'A':
          active_courses.append((row.course_id, row.offer_nbr, row.discipline, row.catalog_number,
                                 row.title, with_clause))
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
                                   row.title, with_clause))

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
