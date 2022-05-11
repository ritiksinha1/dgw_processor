#! /usr/local/bin/python3
""" Convert Lexer and metadata items into JSON elements
"""

import argparse
import json
import os
import psycopg
import sys

from collections import namedtuple
from traceback import print_stack
from pprint import pprint
from typing import List, Set, Dict, Tuple, Optional, Union, Any

from psycopg.rows import namedtuple_row

import dgw_handlers
from scriberror import ScribeError

DEBUG = os.getenv('DEBUG_UTILS')

# Dicts of CUNY college names and requirement block block_types
with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as cursor:
    cursor.execute('select code, name from cuny_institutions')
    college_names = {row.code: row.name for row in cursor.fetchall()}

    cursor.execute("""
    select institution, requirement_id, block_type
    from requirement_blocks
    where period_stop ~* '^9'
    """)
    block_types = {(row.institution, row.requirement_id): row.block_type
                   for row in cursor.fetchall()}
    # Special entry for parsing raw scribe blocks
    block_types[('TST01', 'RA000000')] = 'TESTING'
conn.close()


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
    print('*** with_clause({class_name(ctx)})', file=sys.stderr)
  if isinstance(ctx, list):
    return ' '.join([expression_to_str(context.expression()) for context in ctx])
  assert class_name(ctx) == 'With_clause', (f'Assertion Error: {class_name(ctx)} is not With_clause'
                                            f' in _with_clause')
  return expression_to_str(ctx.expression())


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
    print(f'*** class_or_credit({class_name(ctx)})', file=sys.stderr)

  try:
    if ctx.CREDIT():
      return 'credit'
    else:
      return 'class'
  except AttributeError as ae:
    return 'Neither Class nor Credit'


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
  assert class_name(ctx) == 'Expression', (f'Assertion Error: {class_name(ctx)} is not Expression'
                                           f' in expression_to_str')
  return_str = ''
  for child in ctx.getChildren():
    if class_name(child) == 'Expression':
      return_str += expression_to_str(child) + ' '
    else:
      return_str += child.getText() + ' '

  return return_str.strip()


# analyze_expression()
# -------------------------------------------------------------------------------------------------
def analyze_expression(ctx, institution, requirement_id):
  """ Analysis report consists of context info (institution, requirement_id, context_path, and
      a list of rel_op triples (lhs, op, rhs))

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

    The dict keys are rel_op, log_op, list, noncourse, and string. Children of rel_op and log_op are
    lhs and rhs.
  """
  assert class_name(ctx) == 'Expression', (f'Assertion Error: {class_name(ctx)} is not Expression'
                                           f' in expression_to_str')

  report = {'instituion': institution,
            'requirement_id': requirement_id,
            'block_type': block_types[(institution, requirement_id)],
            'context_path': context_path(ctx).split(' => ')[0:-1],
            }

  children = ctx.children
  # Clear all levels of top-level outer parens
  while children[0].getText() == '(':
    if children[-1].getText() == ')':
      del children[0]
      del children[-1]
    else:
      break

  # Use expression_tree to recurse through the expression tree.
  relop_expressions = set()
  expression_tree(children, relop_expressions)
  report['relop_expressions'] = list(relop_expressions)
  with open('relop_expressions.txt', 'a') as relop_report:
    print(institution, requirement_id, file=relop_report)
    print(json.dumps(report), file=relop_report)
  return


# expression_tree()
# -------------------------------------------------------------------------------------------------
def expression_tree(node_list: Any, relop_expressions: set):
  """ Given a list of nodes, update list of lhs rel_op rhs terminal nodes.
  """
  nodes = node_list if isinstance(node_list, list) else [node_list]
  if len(nodes) == 3 and class_name(nodes[1]) == 'Relational_op':
    lhs = ' '.join([c.getText() for c in nodes[0].children])
    rel_op = nodes[1].getText()
    rhs = ' '.join([c.getText() for c in nodes[2].children])
    relop_expressions.add((lhs, rel_op, rhs))
  else:
    for node in nodes:
      if class_name(node) == 'Expression':
        expression_tree(node.children, relop_expressions)


# concentration_list()
# -------------------------------------------------------------------------------------------------
def concentration_list(condition: str, institution: str, requirement_id: str) -> list:
  """ If the condition string contains equality operators (= or <>), lookup the latest concentration
      for that institution with that block_value.
      However, if there is no equality operator, find the subplans for the current major and return
      figure out what the matching scribe blocks are.
      The return array gives the titles of the concentrations, the requirement_ids, and hypertext
      links for use by htmlificization.
      KINKY: the condition can be very elaborate, mentioning things like, “MAJOR=XXX and CONC=YYY or
      MAJOR=WWW and CONC=ZZZ...”
  """
  if DEBUG:
    print(f'*** concentration_list({condition}. {institution}. {requirement_id})', file=sys.stderr)

  assert 'conc' in condition.lower(), (f'Assertion Error: No CONC in {condition} in '
                                       f'concentration_list')
  # print(f'*** concentration_list({condition}) not implemented yet', file=sys.stderr)
  return ['Concentration lookup not implemented yet']


# get_nv_pairs()
# -------------------------------------------------------------------------------------------------
def get_nv_pairs(ctx):
  """
      nv_pair         : (nv_lhs '=' nv_rhs)+;
      nv_lhs          : SYMBOL;
      nv_rhs          : (STRING | SYMBOL);

      Given a (list of) name-value pairs, create a list of dicts with the names and values. If the
      name is RemarkJump or AdviceJump, the URL value might span more than one pair, in which case
      they are concatenated into a single one.
  """
  if DEBUG:
    print(f'*** get_nv_pairs({ctx}', file=sys.stderr)

  contexts = ctx if isinstance(ctx, list) else [ctx]
  pairs_list = []
  for context in contexts:
    nv_pairs = context.nv_pair()
    last_lhs = None
    url_str = ''
    for nv_pair in nv_pairs:
      lhs = nv_pair.nv_lhs()
      rhs = nv_pair.nv_rhs()
      assert isinstance(lhs, list) and isinstance(rhs, list) and len(lhs) == 1 and len(rhs) == 1
      lhs = lhs[0].getText()
      rhs = rhs[0].getText()
      this_lhs = lhs.lower()

      # AdviceJump and RemarkJump have URLs, which might span multiple nv_pairs
      if this_lhs in ['advicejump', 'remarkjump']:
        if this_lhs == last_lhs:
          # Extend URL
          url_str += rhs.strip('"')
          continue
        if url_str:
          # Complete pending xxxJump item
          pairs_list.append({last_lhs.title().replace('j', 'J'): url_str})
        # Start new xxxJump
        last_lhs = this_lhs
        url_str = rhs.strip('"')
        continue

      if url_str:
        # Complete pending xxxJump
        pairs_list.append({last_lhs.title().replace('j', 'J'): url_str})
      pairs_list.append({this_lhs.title(): rhs})
      last_lhs = this_lhs
      url_str = ''

  return pairs_list


# get_rules()
# -------------------------------------------------------------------------------------------------
def get_rules(ctx, institution, requirement_id):
  """ Return a list of rule dicts for the children of head_rule or body_rule ctx.
      head_rule         : class_credit_head
                        | conditional_head
                        | copy_rules
                        | lastres_head
                        | maxclass_head
                        | maxcredit_head
                        | maxpassfail_head
                        | maxterm_head
                        | maxtransfer_head
                        | minclass_head
                        | mincredit_head
                        | mingpa_head
                        | mingrade_head
                        | minperdisc_head
                        | minres_head
                        | minterm_head
                        | noncourse
                        | proxy_advice
                        | remark
                        | rule_complete
                        | share_head
                        ;

        body_rule       : block
                        | blocktype
                        | class_credit_body
                        | conditional_body
                        | course_list_rule
                        | copy_rules
                        | group_requirement
                        | noncourse
                        | proxy_advice
                        | remark
                        | rule_complete
                        | subset
                        ;

  """
  if DEBUG:
    print(f'*** get_rules({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)

  # try:
  #   assert(class_name(ctx).lower()) in ['head_rule', 'body_rule'], (f'Assertion Error: '
  #                                                                   f'{class_name(ctx).lower()} '
  #                                                                   f'is not head_rule or '
  #                                                                   f'body_rule in get_rules')
  # except AssertionError as ae:
  #   print(f'{ae}', file=sys.stderr)
  #   print_stack(file=sys.stderr)
  #   raise

  return_list = []
  if isinstance(ctx, list):
    rules_ctx = ctx
  else:
    rules_ctx = [ctx]
  for rule_ctx in rules_ctx:
    for child in rule_ctx.getChildren():
      if DEBUG:
        print('...', class_name(child), file=sys.stderr)
      return_list.append(dgw_handlers.dispatch(child, institution, requirement_id))

  return return_list


# get_display()
# -------------------------------------------------------------------------------------------------
def get_display(ctx: Any) -> str:
  """ Gather subsstrings from a list of display items into a single string.
  """
  if ctx.display():
    if isinstance(ctx.display(), list):
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
      If in the header, labels are children of header_label.
  """
  if DEBUG:
    print(f'*** get_label({class_name(ctx)})', file=sys.stderr)

  label_ctx = None
  try:
    match 'header' if context_path(ctx).lower().startswith('head') else 'body':
      case 'header':
        if header_label_ctx := ctx.header_label():
          if label_ctx := header_label_ctx.label():
            pass
      case 'body':
        if label_ctx := ctx.label():
          pass
      case _: exit(f'Invalid match: {_}')
  except AttributeError:
    pass

  if label_ctx is None:
    return None

  if isinstance(label_ctx, list):
    label_str = ''
    for context in label_ctx:
      label_str += ' '.join([context.string().getText().strip(' "')])
  else:
    label_str = label_ctx.string().getText().strip(' "')

  if DEBUG:
    print(f'    {label_str=}', file=sys.stderr)

  return label_str


# get_scribed_courses()
# -------------------------------------------------------------------------------------------------
def get_scribed_courses(first_course, other_courses=None) -> list:
  """ Generate list of (discipline, catalog_number, with_clause) tuples for courses in a course
      list. Distribute wildcards across the list so that each “scribed course” is a complete
      (discipline, catalog_number, with_clause) tuple, even if the with clause is None.

      For analysis purposes, with clauses should be logged, but are not.

course_list     : course_item (and_list | or_list)? (except_list | include_list)* proxy_advice?;
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
                // Include keywords that appear as discipline names at CUNY
                | BLOCK
                | IS;
  """
  if DEBUG:
    print(f'\n*** get_scribed_courses({class_name(first_course)}, {class_name(other_courses)})',
          end='', file=sys.stderr)

  try:
    assert class_name(first_course) == 'Course_item', (f'Assertion Error: '
                                                       f'{class_name(first_course)} is not '
                                                       f'Course_item in get_scribed_courses')
    if other_courses is not None:
      assert class_name(other_courses).endswith('_list'), (f'Other courses is not And_list or '
                                                           f'Or_list in get_scribed_courses')
  except AssertionError as ae:
    print(ae)
    print_stack(limit=4)

  # The list of (discipline: str, catalog_number: str, with_clause: str) tuples to return.
  scribed_courses = []

  discipline, catalog_number, with_clause = (None, None, None)

  # The first_course of the list should start with both a discipline and catalog number, but
  # sometimes just a wildcard is given, which will be recognized as a catalog number. But if there
  # is no discipline, and the catalog_number is not the wildcard (@), it's an error that the grammar
  # didn't catch.

  catalog_number = first_course.catalog_number().getText().strip()
  try:
    discipline = first_course.discipline().getText()
  except AttributeError:
    if catalog_number == '@':
      discipline = '@'
    else:
      raise ScribeError(f'Invalid first course item, “{catalog_number}”, at '
                        f'{context_path(first_course)}')

  try:
    with_list = first_course.with_clause()
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
  if first_course.area_start():
    scribed_courses.append('area_start')
  scribed_courses.append((discipline, catalog_number, with_clause))
  if first_course.area_end():
    scribed_courses.append('area_end')

  # For the remaining scribed courses (if any), the discipline determined above will be the "seed"
  # for distributing across succeeding courses where the discipline is not specified.
  catalog_number = None  # Must be present
  with_clause = None     # Does not distribute (as discipline does)

  if other_courses is not None:
    for child in other_courses.getChildren():
      # Children might be list_and/list_or (ignore), area_end, or course_item
      if class_name(child) == 'Area_end':
        scribed_courses.append('area_end')
        continue

      elif class_name(child) == 'Course_item':
        # course_items can have area start, area_end, discipline, catalog number
        if child.area_end():
          scribed_courses.append('area_end')
        if child.area_start():
          scribed_courses.append('area_start')
        if child.discipline():
          discipline = child.discipline().getText().strip()
        if child.catalog_number():
          catalog_number = child.catalog_number().getText().strip()
        if child.with_clause():
          with_clause = _with_clause(child.with_clause())

        assert catalog_number is not None, (f'Assertion Error: Course Item with no catalog number: '
                                            f'{child.getText()} in get_scribed_courses')
        scribed_courses.append((discipline, catalog_number, with_clause))

  if DEBUG:
    print(f'    {scribed_courses=}', file=sys.stderr)

  return scribed_courses


# get_groups()
# -------------------------------------------------------------------------------------------------
def get_groups(ctx: list, institution: str, requirement_id: str) -> list:
  """ Given a groups ctx, return a list of groups.
        group_requirement : NUMBER GROUP groups (qualifier tag? | proxy_advice | remark)* label? ;
        groups            : group (logical_op group)*; // But only OR should occur
        group             : LP
                           ( block
                           | blocktype
                           | body_class_credit
                           | course_list_rule
                           | group_requirement
                           | noncourse
                           | rule_complete ) (qualifier tag? | proxy_advice | remark)* label?
                           RP ;
  """
  if DEBUG:
    print(f'*** getgroups({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)
    print(context_path(ctx))
    print_stack()

  return_dict = {'groups': []}
  for group_ctx in ctx.group():
    children = group_ctx.getChildren()

    for child in children:
      # Ignore LP | RP
      item_class = class_name(child)
      if item_class.lower() == 'terminalnodeimpl':
        continue

      # group_dict = {'label': get_label(child)}
      group_dict = dict()
      group_dict.update(get_qualifiers(child, institution, requirement_id))
      try:
        group_dict.update(dgw_handlers.remark(child.remark(), institution, requirement_id))
      except AttributeError:
        pass
      if class_name(child).lower() in dgw_handlers.dispatch_body.keys():
        group_dict.update(dgw_handlers.dispatch(child, institution, requirement_id))
      else:
        print(f'xxxx {class_name(child)} is not a dispatchable body key', file=sys.stderr)
      return_dict['groups'].append(group_dict)

  if DEBUG:
    print('   ', return_dict, file=sys.stderr)

  return return_dict


# get_qualifiers()
# -------------------------------------------------------------------------------------------------
def get_qualifiers(ctx: any, institution: str, requirement_id: str) -> list:
  """ Build qualifier-specific dicts for various possible qualifiers. The grammar, and this method,
      recognize any qualifier, even though Degree Works allows only certain subsets in different
      contexts. On the other hand, we ignore qualifiers that apply to the operation of degree audits
      but which are not part of a degree or program’s requirement structure.

      The ctx can be either a single context of a list of them. But within a list, we don't expect
      the same qualifier to be repeated.

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

  if DEBUG:
    print(f'*** get_qualifiers({class_name(ctx)=})', file=sys.stderr)
    print_stack()

  valid_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                      'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                      'proxy_advice', 'rule_tag', 'samedisc', 'share']

  if isinstance(ctx, list):
    contexts = ctx
  else:
    contexts = [ctx]
  qualifier_dict = dict()
  for context in contexts:
    if class_name(context) == 'Qualifier':
      # See which qualifiers, if any, are part of this context
      for valid_qualifier in valid_qualifiers:
        class_credit_str = None
        if qualifier_func := getattr(context, valid_qualifier, None):
          if qualifier_ctx := qualifier_func():
            if getattr(qualifier_ctx, 'class_or_credit', None):
              # Class or credit is an attribute of several qualifiers. Extract it here.
              if coc_ctx := qualifier_ctx.class_or_credit():
                class_str = qualifier_ctx.class_or_credit().CLASS()
                credit_str = qualifier_ctx.class_or_credit().CREDIT()
                if class_str:
                  class_credit_str = 'class'
                elif credit_str:
                  class_credit_str = 'credit'
                else:
                  print(f'*** Error: neither {class_str=} nor {credit_str=} in get_qualifiers',
                        file=sys.stderr)
              if DEBUG:
                print(f'    get_qualifiers got {valid_qualifier=} with {class_credit_str=}',
                      file=sys.stderr)

            # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
            if valid_qualifier == 'maxpassfail':
              qualifier_dict[valid_qualifier] = {'number': qualifier_ctx.NUMBER().getText(),
                                                 'class_or_credit': class_credit_str}

            # maxperdisc  : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
            # maxtransfer : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
            # minperdisc  : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
            elif valid_qualifier in ['maxperdisc', 'maxtransfer', 'minperdisc']:
              disciplines = qualifier_ctx.SYMBOL()
              if isinstance(disciplines, list):
                disciplines = [d.getText() for d in disciplines]

              qualifier_dict[valid_qualifier] = {'number': qualifier_ctx.NUMBER().getText(),
                                                 'class_or_credit': class_credit_str,
                                                 'disciplines': disciplines}

            # maxspread       : MAXSPREAD NUMBER
            # minarea         : MINAREA NUMBER
            # mingrade        : MINGRADE NUMBER
            # minspread       : MINSPREAD NUMBER
            elif valid_qualifier in ['maxspread', 'minarea', 'mingrade', 'minspread']:
              qualifier_dict[valid_qualifier] = {'number': qualifier_ctx.NUMBER().getText()}

            # minclass        : MINCLASS NUMBER course_list tag? display* label?;
            # mincredit       : MINCREDIT NUMBER course_list tag? display* label?;
            elif valid_qualifier in ['minclass', 'mincredit']:
              # build_course_list returns its own dict, with "course_list" as the key, so we start
              # with that, and add the number, display, and label elements to that.
              qualifier_dict[valid_qualifier] = build_course_list(qualifier_ctx.course_list(),
                                                                  institution, requirement_id)
              qualifier_dict[valid_qualifier]['number'] = qualifier_ctx.NUMBER().getText()
              if qualifier_ctx.display():
                qualifier_dict[valid_qualifier]['display'] = get_display(qualifier_ctx)

            # mingpa : MINGPA NUMBER (course_list | expression)? tag? display* proxy_advice? label?;
            elif valid_qualifier == 'mingpa':
              qualifier_dict.update(dgw_handlers.mingpa(qualifier_ctx, institution, requirement_id))

            # proxy_advice    : (PROXY_ADVICE STRING)+;
            elif valid_qualifier == 'proxy_advice':
              qualifier_dict.update(dgw_handlers.proxy_advice(qualifier_ctx,
                                                              institution, requirement_id))
            # rule_tag         : (RULE_TAG expression)+;
            elif valid_qualifier == 'rule_tag':
              qualifier_dict.update(dgw_handlers.rule_tag(qualifier_ctx,
                                                          institution, requirement_id))

            # samedisc        : SAME_DISC expression
            elif valid_qualifier == 'samedisc':
              # This is used strictly for managing the audit process and is ignored here
              pass

            elif valid_qualifier == 'share':
              qualifier_dict.update(dgw_handlers.share(qualifier_ctx, institution, requirement_id))

            else:
              print(f'Unexpected qualifier: {valid_qualifier} in {requirement_id} for '
                    f'{institution}', file=sys.stderr)

  if DEBUG:
    print(f'    {qualifier_dict=}', file=sys.stderr)

  return qualifier_dict


# num_class_or_num_credit(ctx)
# -------------------------------------------------------------------------------------------------
def num_class_or_num_credit(ctx) -> dict:
  """
      Expected context: (num_classes | num_credits) (logical_op (num_classes | num_credits))?

      If there is a logical_op it tells whether the requirement is for either or both, and we assume
      that the lhs and rhs are mutually exclusive (classes ^ credits). That is, the class_contexts
      and credit_contexts lists will be either empty or of length one.
      The number of classes can be either an int or a range of ints. The number of credits can be
      either a float or a range of floats. For ranges, return both min_x and max_x

      num_classes     : NUMBER CLASS allow_clause?;
      num_credits     : NUMBER CREDIT allow_clause?;
  """
  if DEBUG:
    print(f'*** num_class_or_num_credit({class_name(ctx)})', file=sys.stderr)

  if class_contexts := ctx.num_classes():
    if not isinstance(class_contexts, list):
      class_contexts = [class_contexts]
    for class_ctx in class_contexts:
      num_classes = class_ctx.NUMBER().getText().split(':')
      if len(num_classes) == 1:
        min_classes = max_classes = int(num_classes[0])
      else:
        min_classes, max_classes = [int(num) for num in num_classes]

      if class_ctx.allow_clause():
        allow_classes = class_ctx.allow_clause().NUMBER().getText().strip()
      else:
        allow_classes = None
  else:
    min_classes = max_classes = allow_classes = None

  if credit_contexts := ctx.num_credits():
    if not isinstance(credit_contexts, list):
      credit_contexts = [credit_contexts]
    for credit_ctx in credit_contexts:
      try:
        num_credits = credit_ctx.NUMBER().getText().split(':')
        if len(num_credits) == 1:
          min_credits = max_credits = float(num_credits[0])
        else:
            min_credits, max_credits = [float(num) for num in num_credits]
      except ValueError as ve:
        min_credits = max_credits = -1.0  # syntax indicator: the grammar allows '1-2' as a number.
      if credit_ctx.allow_clause():
        allow_credits = credit_ctx.allow_clause().NUMBER().getText().strip()
      else:
       allow_credits = None
  else:
    min_credits = max_credits = allow_credits = None

  if getattr(ctx, 'logical_op', None) and ctx.logical_op():
    conjunction = ctx.logical_op().getText()
  else:
    conjunction = None

  return {'min_classes': min_classes,
          'max_classes': max_classes,
          'allow_classes': allow_classes,
          'min_credits': min_credits,
          'max_credits': max_credits,
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
  assert class_name(ctx) == 'String', (f'Assertion Error: {class_name(ctx)} is not String in '
                                       f'build_string')
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

      2021-12-09
      This is the parser: there is no reason to look up courses here. That task is deferred to
      applications that use the parsed blocks as input (htmlificization and course-requirement
      mappings). So this process becomes much simpler: no active/inactive/missing course lists;
      no counts of attributes (bkcr and wric). Some of the old code for handling course lookups
      is left here as comments, but those comments should be removed once the new htmlificization
      app shows how to handle that issue.

      The returned dict has the following structure:

        institution         Needed for subsequent course lookups
        scribed_courses     List of course tuples (discipline, catalog_number, with_clause) after
                            catalog numbers are distributed across disciplines, but with wildcards
                            (@) remaining. To handle course areas, this is a two-dimensional list;
                            where there are no areas, the entire list will be in area zero.
        except_courses      Scribed list used for culling from active_courses.
        include_courses     Like except_courses, except this list is not actually used for anything
                            in this method.
        qualifiers          Qualifiers that apply to all courses in the list
        list_type           'AND' or 'OR'

      The except_courses list is an OR list no matter how it is scribed. (Ellucian accepts either
      conjunction, even though documentation says AND is illegal.)

      The include_courses list is an AND list no matter how it is scribed. (Ellucian documentation
      makes this explicit.)

  """
  if DEBUG:
    print(f'*** build_course_list({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  # Preconditions, with error recovery
  if ctx is None:
    # Should not occur, but return an empty dict just in case
    print('Error: build_course_list() with missing context value', file=sys.stderr)
    print_stack(limit=5)
    return {}

  if class_name(ctx) != 'Course_list':
    print(f'{class_name(ctx)} is not Course_list in build_course_list', file=sys.stderr)
    print_stack(limit=5)
    return {}

  # The dict to be returned:
  return_dict = {'institution': institution,
                 'requirement_id': requirement_id,  # development aid
                 'scribed_courses': [[]],
                 'list_type': None,
                 'except_courses': [],
                 'include_courses': [],
                 'context_path': context_path(ctx)  # development aid
                 }

  #   A course list has no label, but a course_list_rule can (should) have one, and so also should
  #   xxx_head productions, where the label is attached to the production, not the list.
  #
  #   Leaving this note here in the hope of finding it the next time the question of whether or not
  #   to look for a label here comes up.
  # if label_str := get_label(ctx):
  #   return_dict['label'] = label_str

  if qualifiers := get_qualifiers(ctx, institution, requirement_id):
    print(f'*** {institution} {requirement_id}: Qualifiers in build_course_list: {qualifiers}',
          file=sys.stderr)
    return_dict['qualifiers'] = qualifiers

  # Determine the list structure and, if specified, whether it is disjunctive or conjunctive.
  # If there is no and_list or or_list (only a first_course) it might be that the first_course has
  # wildcards or a range that will expand to multiple courses. In that case, it will be an OR list.
  return_dict['list_type'] = 'OR'

  other_courses = None
  first_course = ctx.course_item()
  if ctx.and_list():
    return_dict['list_type'] = 'AND'
    other_courses = ctx.and_list()
  elif ctx.or_list():
    other_courses = ctx.or_list()

  # Get the one-dimensional list of tuples and area delimiters; convert to a two-dimensional areas
  # list. To handle imbalanced area_start/area_end pairs, ignore area ends and just start a new
  # area area for each area_start (unless the current area is empty).
  current_area = 0
  for item in get_scribed_courses(first_course, other_courses):
    if isinstance(item, tuple):
      return_dict['scribed_courses'][current_area].append(item)
    elif (item == 'area_start') and (len(return_dict['scribed_courses'][current_area]) > 0):
      return_dict['scribed_courses'].append([])
      current_area += 1

  if ((num_tuples := len(return_dict['scribed_courses'][0])) > 1
     and return_dict['list_type'] is None):
    # This would be a grammar/parser error.
    print(f'Grammar/Parser Error: {institution} {requirement_id} {list_type=} {num_tuples=}',
          file=sys.stderr)

  """ Sublists (except and/or include)
  course_list : course_item (and_list | or_list)? (except_list | include_list)* proxy_advice?;
  The grammar allows them to be in either order, but to do that they show up as lists. Expect
  0 or 1 element per list, but report cases of more than one.
  """
  # Except List
  if ctx.except_list():
    if list_len := len(ctx.except_list()) > 1:
      print(f'Unexpected: except_list occurs {list_len} times. Only first one processed.',
            file=sys.stderr)
    first_course = ctx.except_list()[0].course_item()
    # Ellucian allows either AND or OR even though it has to be OR
    if ctx.except_list()[0].and_list():
      other_courses = ctx.except_list()[0].and_list()
    elif ctx.except_list()[0].or_list():
      other_courses = ctx.except_list()[0].or_list()
    else:
      other_courses = None
    return_dict['except_courses'] = get_scribed_courses(first_course, other_courses)

  # Include List
  if ctx.include_list():
    if list_len := len(ctx.include_list()) > 1:
      print(f'Unexpected: include_list occurs {list_len} times. Only first one processed.',
            file=sys.stderr)
    first_course = ctx.include_list()[0].course_item()
    # Ellucian allows either AND or OR even though it has to be OR
    if ctx.include_list()[0].and_list():
      other_courses = ctx.include_list()[0].and_list()
    elif ctx.include_list()[0].or_list():
      other_courses = ctx.include_list()[0].or_list()
    else:
      other_courses = None
    return_dict['include_courses'] += get_scribed_courses(first_course, other_courses)

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
