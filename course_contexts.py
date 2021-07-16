#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?

    The goal is to extract both the context (the label structure) and the specificity (how many
    alternatives there are) for each course.

    Block, blocktype, copy_rules, noncourse, and remarks are all irrelevant for present purposes.
    Specificity depends on the structure of the course_list, the group (and area) structure, and
    conditional factors.

    This code is modeled on htmlificization, and assumes that the header and body lists in the
    database never need to be interpreted unless they are missing.
"""

import os
import sys

from argparse import ArgumentParser
from collections import namedtuple
from pgconnection import PgConnection
from dgw_interpreter import dgw_interpreter
from quarantined_blocks import quarantine_dict

from pprint import pprint
from inspect import currentframe, getframeinfo

DEBUG = os.getenv('DEBUG_CONTEXTS')

# Information about active courses found in course lists.
ActiveCourse = namedtuple('ActiveCourse',
                          'course_id offer_nbr discipline catalog_number title credits qualifiers')

# A Requirement’s context is a list of labels, conditions, and group info; active_courses is a list
# of ActiveCourse tuples. If the Requirement is disjunctive (OR), the length of the active_courses
# list gives the number of alternative courses that can satisfy the requirement (“may take”). But if
# the Requirement is conjunctive (AND), the course is required (“must take”). But note that this
# doesn’t tell whether the requirement itself is required or optional: that depends on its group and
# conditional contexts, if any.
Requirement = namedtuple('Requirement',
                         'title num_credits_courses is_disjunctive active_courses')


# Context Handlers
# =================================================================================================
def do_course_list(item: dict) -> str:
  """ For a course list, the label gives the requirement name, the length of the list and the
      conjunction determine how many alternatives there are.
  """
  if DEBUG:
    print('*** do_course_list()', file=sys.stderr)
  return_str = ''

  return return_str


def do_group_items(item: dict) -> str:
  """
  """
  if DEBUG:
    print('*** do_group_items()', file=sys.stderr)
  return ''


def do_conditional(item: dict) -> str:
  """
  """
  if DEBUG:
    print('*** do_conditional()', file=sys.stderr)
  return ''


def iter_list(items: list) -> list:
  """
  """
  if DEBUG:
    print(f'*** iter_list({len(items)=})', file=sys.stderr)
  return_list = []
  for value in items:
    if isinstance(value, list):
      return_list += iter_list(value)
    elif isinstance(value, dict):
      return_list += iter_dict(value)
    else:
      print(f'iter_list: Neither list nor dict: {value=} {len(return_list)=}', file=sys.stderr)

  return return_list


def iter_dict(item: dict) -> list:
  """ If there is just a label, that gets added to the context list. If there is a course_list,
      that's used to build a new Requirement to be added; groups have to be recognized because they
      add context. Subsets do not have to be recognized because their label is all that matters,
      and that will be picked up.
  """
  if DEBUG:
    print(f'*** iter_dict({item.keys()=})', file=sys.stderr)
  return_list = []

  if 'label' in item.keys():
    return_list.append(item.pop('label'))
    print(f'Label: {return_list[-1]}', file=sys.stderr)

  if 'course_list' in item.keys():
    # If there is a course_list, there's also info about num classes/credits,as well as whether
    # the list is disjunctive of conjunctive.
    min_credits = item.pop('min_credits')
    max_credits = item.pop('max_credits')
    min_classes = item.pop('min_classes')
    max_classes = item.pop('max_classes')
    conjunction = item.pop('conjunction')  # This is the credit/classes conjunction
    # Build requirement description
    if min_credits:
      if min_credits == max_credits:
        num_credits = f'{float(min_credits):0.1f}'
      else:
        num_credits = f'{float(min_credits):0.1f}-{float(max_credits):0.1f}'
    else:
      num_credits = None
    cr_sfx = '' if num_credits == '1.0' else 's'

    if min_classes:
      if min_classes == max_classes:
        num_classes = f'{min_classes}'
      else:
        num_classes = f'{min_classes}-{max_classes}'
    else:
      num_classes = None
    cl_sfx = '' if num_classes == '1' else 'es'

    if num_classes and num_credits:
      assert conjunction, f'classes and credits with no conjunction'
      class_credit_str = f'{num_classes} class{cl_sfx} {conjunction} {num_credits} credit{cr_sfx}'
    elif num_classes:
      class_credit_str = f'{num_classes} class{cl_sfx}'
    elif num_credits:
      class_credit_str = f'{num_credits} credit{cr_sfx}'
    else:
      class_credit_str = None
    if class_credit_str:
      print(f'{class_credit_str=}', file=sys.stderr)

    # Discard course_list['allow_xxx'] entries.
    item.pop('allow_credits')
    item.pop('allow_classes')

    # Process the course_list itself
    course_list = item.pop('course_list')
    try:
      label_str = course_list['label']
    except KeyError as ke:
      label_str = None

    try:
      list_type = course_list['list_type']
    except KeyError as ke:
      list_type = None
    print(f'Conjunction: {list_type}', file=sys.stderr)

    active_courses = course_list['active_courses']
    assert list_type or len(active_courses) == 1, (f'No list_type for list length '
                                                   f'{len(active_courses)}')
    requirement = Requirement._make([label_str, class_credit_str, list_type == 'OR', []])
    for active_course in active_courses:
      requirement.active_courses.append(ActiveCourse._make(active_course))
    print(f'{requirement}', file=sys.stderr)

  try:
    conditional = item.pop('conditional')
    print('Condition:', conditional['condition'], file=sys.stderr)
  except KeyError as ke:
    pass

  try:
    groups = item.pop('group')
    assert len(groups) == 1
    group = groups[0]
    label_str = group['label']
    num_required = group['num_groups_required']
    num_groups = len(group['group_items'])
    suffix = '' if int(num_groups) == 1 else 's'
    group_str = f'{num_required} of {num_groups} group{suffix}'
    print(f'Group Requirement: {group_str}', file=sys.stderr)
  except KeyError as ke:
    if ke.args[0] != 'group':
      print(f'Group KeyError: {ke=}', file=sys.stderr)

  # That should be all we‘re intersted in, but double-check:
  for key, value in item.items():
    if isinstance(value, list):
      return_list += iter_list(value)
    elif isinstance(value, dict):
      return_list += iter_dict(value)
    else:
      print(f'iter_dict: Not label, condition, group, list, or dict: {key=} {value=}',
            file=sys.stderr)

  return return_list


# __main__()
# =================================================================================================
if __name__ == '__main__':
  parser = ArgumentParser('Look up course list contexts')
  parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
  parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
  parser.add_argument('-v', '--block_values', nargs='*', default=['csci-ba'])
  parser.add_argument('-f', '--force', action='store_true', default=False)
  parser.add_argument('-p', '--period', default='current')
  args = parser.parse_args()
  period = args.period.lower()

  # Allowable values for period
  assert period in ['all', 'current']

  with open('./debug', 'w') as debug:
    conn = PgConnection()
    cursor = conn.cursor()
    institutions = [inst.upper().strip('01') for inst in args.institutions]
    for institution in institutions:
      institution = institution + '01'
      block_types = [arg.upper() for arg in args.block_types]
      for block_type in block_types:
        assert block_type in ['MAJOR', 'CONC', 'MINOR']
        block_values = [value.upper() for value in args.block_values]
        if 'ALL' in block_values:
          cursor.execute(f"""
        select distinct block_value
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
        order by block_value
    """)
          block_values = [row.block_value.upper() for row in cursor.fetchall()
                          if not row.block_value.isdigit()
                          and '?' not in row.block_value]
        for block_value in block_values:
          if block_value.startswith('MHC') or block_value.isdigit():
            continue
          cursor.execute(f"""
        select requirement_id, period_stop, requirement_text, header_list, body_list
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
           and block_value ~* '^{block_value}$'
    """)
          for row in cursor.fetchall():
            if (institution, row.requirement_id) in quarantine_dict:
              print(f'{institution}, {row.requirement_id} is quarantined')
              continue
            if period == 'current' and row.period_stop != '99999999':
              continue
            print(f'{institution} {block_type} {block_value} {period}')
            header_list, body_list = (row.header_list, row.body_list)
            if (len(header_list) == 0 and len(body_list) == 0) or args.force:
              print(f'[{len(header_list)=}] {args.force=} reinterpret')
              header_list, body_list = dgw_interpreter(institution, block_type, block_value,
                                                       period_range=period)

            print(f'*** {institution} {block_type} {block_value} {period}', file=debug)
            pprint(body_list, stream=debug)
            print('\n', file=debug)

            # Iterate over the body
            pprint(iter_list(body_list))
