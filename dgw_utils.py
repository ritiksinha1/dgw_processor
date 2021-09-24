#! /usr/local/bin/python3
""" Convert Lexer and metadata items into JSON elements
"""

from collections import namedtuple
from typing import List, Set, Dict, Tuple, Optional, Union, Any

import argparse
import json
import os
import sys

from pprint import pprint
from traceback import print_stack

from Any import ANY

from pgconnection import PgConnection

import dgw_handlers

DEBUG = os.getenv('DEBUG_UTILS')

# Dict of CUNY college names
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
college_names = {row.code: row.name for row in cursor.fetchall()}
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
  assert class_name(ctx) == 'Expression', (f'Assertion Error: {class_name(ctx)} is not Expression'
                                           f' in expression_to_str')
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
  if DEBUG:
    print(f'*** concentration_list({condition}. {institution}. {requirement_id})', file=sys.stderr)

  assert 'conc' in condition.lower(), (f'Assertion Error: No CONC in {condition} in '
                                       f'concentration_list')
  print(f'*** concentration_list({condition}) not implemented yet', file=sys.stderr)
  return ['Concentration lookup not implemented yet']


# get_rules()
# -------------------------------------------------------------------------------------------------
def get_rules(ctx, institution, requirement_id):
  """ Return a list of rule dicts for the children of head_rule or body_rule ctx.
      head_rule       : conditional_head
                      | block
                      | blocktype
                      | class_credit_head
                      | copy_rules
                      | lastres
                      | maxcredit
                      | maxpassfail_head
                      | maxterm
                      | maxtransfer_head
                      | minclass_head
                      | mincredit_head
                      | mingpa
                      | mingrade
                      | minperdisc_head
                      | minres
                      | minterm
                      | noncourse
                      | proxy_advice
                      | remark
                      | rule_complete
                      | share_head

      body_rule       : conditional_body
                      | block
                      | blocktype
                      | class_credit_body
                      | copy_rules
                      | group_requirement
                      | lastres
                      | maxcredit
                      | maxtransfer
                      | minclass
                      | mincredit
                      | mingrade
                      | minres
                      | noncourse
                      | proxy_advice
                      | remark
                      | rule_complete
                      | share
                      | subset

  """
  if DEBUG:
    print(f'*** get_rules({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)

  # try:
  #   assert(class_name(ctx).lower()) in ['head_rule', 'body_rule'], (f'Assertion Error: '
  #                                                                   f'{class_name(ctx).lower()} is '
  #                                                                   f'not head_rule or body_rule'
  #                                                                   f' in get_rules')
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
        print('xxxx', class_name(child), file=sys.stderr)
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
  """
  if DEBUG:
    print(f'*** get_label({class_name(ctx)})', file=sys.stderr)

  if ctx.label():
    if isinstance(ctx.label(), list):
      label_str = ''
      for context in ctx.label():
        label_str += ' '.join([context.string().getText().strip(' "')])
    else:
      label_str = ctx.label().string().getText().strip(' "')
  else:
    label_str = None

  if DEBUG:
    print(f'    {label_str=}', file=sys.stderr)

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
  if DEBUG:
    print(f'*** get_scribed_courses({class_name(course_item)}, {len(list_items)} list items)',
          file=sys.stderr)

  assert class_name(course_item) == 'Course_item', (f'Assertion Error: {class_name(ctx)} is not '
                                                    f'Course_item in get_scribed_courses')

  # The list of (discipline: str, catalog_number: str, with_clause: str) tuples to return.
  scribed_courses = []

  # The course_item at the start of the list has to start with both a discipline and catalog number,
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
    assert catalog_number is not None, (f'Assertion Error: Course Item with no catalog number: '
                                        f'{list_item.getText()} in get_scribed_courses')
    scribed_courses.append((discipline, catalog_number, with_clause))
    if list_item.area_end():
      scribed_courses.append('area_end')

  if DEBUG:
    print(f'    {scribed_courses=}', file=sys.stderr)

  return scribed_courses


# get_groups()
# -------------------------------------------------------------------------------------------------
def get_groups(ctx: list, institution: str, requirement_id: str) -> list:
  """ Given a groups ctx, return a list of groups.
      group_requirement : NUMBER GROUP groups qualifier* label? ;
      groups            : group (logical_op group)*; // But only OR should occur
      group             : LP
                        (block
                         | blocktype
                         | course_list
                         | class_credit_body
                         | group_requirement
                         | noncourse
                         | rule_complete)
                        qualifier* label?
                        RP
                      ;
  """
  if DEBUG:
    print(f'*** getgroups({class_name(ctx)}, {institution}, {requirement_id})', file=sys.stderr)

  return_list = []
  for group_ctx in ctx.group():
    children = group_ctx.getChildren()

    for child in children:
      # Ignore LP | RP
      item_class = class_name(child)
      if item_class.lower() == 'terminalnodeimpl':
        continue

      if 'Course_list' == class_name(child):
        return_list.append(build_course_list(child, institution, requirement_id))
      else:
        return_list.append(dgw_handlers.dispatch(child, institution, requirement_id))

    return_dict = {'groups': return_list}

    if qualifier_ctx := group_ctx.qualifier():
      return_dict.update(get_qualifiers(qualifier_ctx, institution, requirement_id))

    if group_ctx.label():
      return_dict['label'] = get_label(group_ctx)
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
            # ruletag         : RULE_TAG expression;
            # samedisc        : SAME_DISC expression

            elif valid_qualifier in ['proxy_advice', 'rule_tag', 'samedisc']:
              # These are used for managing the audit process and are ignored here
              pass

            elif valid_qualifier == 'share':
              qualifier_dict.update(dgw_handlers.share(qualifier_ctx, institution, requirement_id))

            else:
              print(f'Unexpected qualifier: {valid_qualifier} in {requirement_id} for '
                    f'{institution}', file=sys.stderr)

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
    print(f'*** build_course_list({class_name(ctx)}, {institution}, {requirement_id})',
          file=sys.stderr)

  if ctx is None:
    return None
  assert class_name(ctx) == 'Course_list', (f'Assertion Error: {class_name(ctx)} is not Course_list'
                                            f' in build_course_list')

  # The dict to be returned:
  return_dict = {'scribed_courses': [],
                 'list_type': None,
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
  active_courses = return_dict['active_courses']
  inactive_courses = return_dict['inactive_courses']
  except_courses = return_dict['except_courses']
  include_courses = return_dict['include_courses']
  missing_courses = return_dict['missing_courses']
  attributes = return_dict['attributes']

  # get context of the required course_item and list of optional additional course_items.
  return_dict['context_path'] = context_path(ctx)

  # Pick up the label, if there is one
  if label_str := get_label(ctx):
    return_dict['label'] = label_str

  if qualifiers := get_qualifiers(ctx, institution, requirement_id):
    if DEBUG:
      print(f'*** qualifiers in build_course_list: {qualifiers}', file=sys.stderr)
    return_dict['qualifiers'] = qualifiers

  # The Scribe context in which the list appeared
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

  list_type = return_dict['list_type']

  scribed_courses += get_scribed_courses(course_item, list_items)
  if len(scribed_courses) > 1 and list_type is None:
    # This would be a grammar/parser error. But see the active_course list check at the end of this
    # function.
    print(f'{institution} {requirement_id} {list_type=} {len(scribed_courses)=}', file=sys.stderr)

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

  # Qualifiers:
  # print(f'\n{ctx.getText()}')
  # print(dir(ctx))
  # qualifiers = get_qualifiers(ctx, institution, requirement_id)
  # print(qualifiers)
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

  # Check there is a list_type when multiple active courses. This happens when there is just one
  # scribed course, thus no and_list or or_list, but it expanded to  multiple active courses because
  # of wildcard(s). It’s an OR list.
  if len(active_courses) > 1 and list_type is None:
    return_dict['list_type'] = 'OR'

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
