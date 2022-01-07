#! /usr/local/bin/python3
"""
    Convert a scribe block and it (json-encoded) parsed representation into a web page.

    The json-encoded lists and dicts produced by the dgw_interpreter can be nested within one
    another to any depth.

    Everything is presented as HTML details elements, with the label of a dict being the
    summary element. Subsets, Groups, Conditionals, and course lists are handles specially.

"""

import argparse
import csv
import os
import sys

from pprint import pprint
from collections import namedtuple

from course_lookup import lookup_course

import html_utils
import format_utils

from format_body_qualifiers import dispatch_body_qualifiers
from format_header_productions import dispatch_header_productions

from quarantine_manager import QuarantineManager
from dgw_parser import dgw_parser, catalog_years

from pgconnection import PgConnection

DEBUG = os.getenv('DEBUG_HTML')

# Module Initialization
# =================================================================================================

# Dict of CUNY college names
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
college_names = {row.code: row.name for row in cursor.fetchall()}
conn.close()

# Dict of quarantined requirement_blocks
quarantined_dict = QuarantineManager()


# requirement_to_details_element()
# -------------------------------------------------------------------------------------------------
def requirement_to_details_element(requirement: dict) -> str:
  """ This starts as class_credit_body in the grammar; dgw_parser has turned it into a list of
      dicts. This method interprets one element of that list.
      If there is a label, return a full details element with the label as the summary. Otherwise,
      just return the HTML that will make up the body of an enclosing details element.
      Keys: allow_classes, allow_credits, conjunction, course_list, is_pseudo, label, num_classes,
            num_credits.
      Ignoring allow_classes and allow_credits: they are audit controls.
  """
  if DEBUG:
    print(f'*** requirement_to_details_element({list(requirement.keys())})', file=sys.stderr)

  return '<p class="error">Requirements</p>'
  try:
    label = requirement.pop('label')
    if not label:
      raise KeyError
    outer_label_str = label
  except KeyError as ke:
    outer_label_str = ''

  requirement_list = []
  if 'is_pseudo' in requirement.keys() and requirement['is_pseudo']:
    requirement_list.append('<p>This requirement does not have a strict credit limit.</p>')

  requirements_str = format_utils.format_num_class_credit(requirement)
  if requirements_str is None:
    requirements_str = '<span class="error">Missing number of classes/credits information</span>'

  # If nothing else, expect a list of courses for the requirement
  try:
    if DEBUG:
      print('    From requirement_to_details_element()', file=sys.stderr)
    inner_label_str, course_str = format_utils.format_course_list(requirement.pop('course_list'))
  except KeyError as ke:
    inner_label_str = course_str = ''

  # Not expecting both inner and outer labels; combine if present
  # if DEBUG:
  #   print(f'    returning <details><summary>{requirements_str} in '
  #         f'{inner_label_str}{outer_label_str}</summary>'
  #         f'[{course_str}]</details>', file=sys.stderr)
  return (f'<details><summary>{requirements_str} in {inner_label_str}{outer_label_str}</summary>'
          f'{course_str}</details>')


# group_requirement_to_details_elements()
# -------------------------------------------------------------------------------------------------
def group_requirement_to_details_elements(info: dict, outer_label=None) -> str:
  """
      Returns a details element for each dict in the info list.
      The summary for each group is the label; the body starts with a paragraph that tells how many
      group items are required, and how many group items there are, followed by the html for each
      group item.
  """
  if DEBUG:
    print(f'*** group_requirement_to_details_elements({list(info.keys())}, '
          f'{outer_label=})', file=sys.stderr)
  assert isinstance(info, dict), f'{info} is not a dict'

  return '<p class="error">Group</p>'
  group_requirement = info.pop('group_requirement')
  return_str = ''
  num_required = int(group_requirement['number'])
  if num_required < len(format_utils.number_names):
    num_required = format_utils.number_names[num_required]
  group_list = group_requirement['group_list']
  assert isinstance(group_list, dict)
  num_groups = len(group_list['groups'])
  num_groups_suffix = '' if num_groups == 1 else 's'
  if num_groups < len(format_utils.number_names):
    num_groups = format_utils.number_names[num_groups]
  if num_required == 'one':
    if num_groups == 'one':
      requirement_str = '<p>The following group'
    elif num_groups == 'two':
      requirement_str = '<p>Either of the following two groups'
    else:
      requirement_str = f'<p>One of the following {num_groups} groups'
  else:
    requirement_str = f'<p>Any {num_required} of the following {num_groups} groups'
  label_str = group_requirement['label'].title()

  try:
    qualifiers = ''.join(f'<p>{q}</p>' for q in group_requirement['qualifiers'])
  except KeyError as ke:
    qualifiers = ''

  summary = f'<summary>{label_str}</summary>'
  body = requirement_str + qualifiers

  # Each group gets its own details element telling which group it is
  group_number = 0
  for group_item in group_list['groups']:
    group_number += 1
    if isinstance(group_item, list):
      group_body = html_utils.list_to_html(group_item)
    elif isinstance(group_item, dict):
      group_body = html_utils.dict_to_html(group_item)
    else:
      group_body = f'<div class="error">Error: {group_item} is neither a list nor a dict</div>'
    index = format_utils.number_names[group_number] if group_number < len(format_utils.number_names) else group_number
    body += f"""
    <details>
      <summary>Group {index} of {num_groups} group{num_groups_suffix}</summary>
      {group_body}
    </details>
    """
  return_str += f'<details open="open">{summary}{body}</details>'
  return return_str


# conditional_to_details_element()
# -------------------------------------------------------------------------------------------------
def conditional_to_details_element(info: dict, outer_label: str) -> str:
  """  The dict for a conditional construct must have a condition, which becomes the summary of the
       html details element. The optional label goes next, followed by nested details elements for
       the true and the optional false branches.

       There are four possibilities for labels: outer, inner, both, or neither (really?). If both,
       return the parts nested inside a details element with the outer summary
  """
  if DEBUG:
    print(f'*** conditional_to_details_element({list(info.keys())}, {outer_label=})',
          file=sys.stderr)

  return '<p class="error"Conditional</p>'

  try:
    condition = info.pop('condition')
  except KeyError as ke:
    condition = '(Missing Condition)'

  try:
    inner_label = info.pop('label')
  except KeyError as ke:
    inner_label = None

  try:
    true_value = html_utils.to_html(info['if_true'])
    if_true_part = (f'<details open="open"><summary>if ({condition}) is true</summary>'
                    f'{true_value}</details>')
  except KeyError as ke:
    if_true_part = '<p class="error">Empty If-then rule!</p>'

  try:
    false_value = html_utils.to_html(info['if_false'])
    if_false_part = (f'<details open="open"><summary>if ({condition}) is not true</summary>'
                     f'{false_value}</details>')
  except KeyError as ke:
    if_false_part = ''  # Else is optional

  if inner_label:
    inner_details = (f'<details><summary open="open">{inner_label.title()}</summary'
                     f'{if_true_part}{if_false_part}</details>')

    # Return one of the four possibilities
    if outer_label is None:
      return inner_details
    else:
      return (f'<details><summary open="open"><summary{outer_label.title()}</summary>'
              f'<details>{inner_details}</details>')
  else:
    inner_details = f'{if_true_part}{if_false_part}'
    if outer_label is None:
      return inner_details
    else:
      return (f'<details><summary open="open"><summary{outer_label.title()}</summary>'
              f'{inner_details}</details>')


# scribe_block_to_html()
# -------------------------------------------------------------------------------------------------
def scribe_block_to_html(row: tuple, period_range='current') -> str:
  """ Generate html for the scribe block and interpreted head and body lists objects, unless the
      block has been quarantined.
  """

  if DEBUG:
    print(f'*** scribe_block_to_html({row}, {period_range=})', file=sys.stderr)

  if row.requirement_html == 'Not Available':
    return ('<h1 class="error">This scribe block is not available.</h1>'
            '<p><em>Should not occur.</em></p>')

  catalog_type, first_year, last_year, catalog_years_text = catalog_years(row.period_start,
                                                                          row.period_stop)
  college_name = college_names[row.institution]
  disclaimer = """
  <div class="disclaimer">
    <p class="warning">
      This is a display of the requirements specified in this Scribe block, omitting information
      that Degree Works uses to audit any particular student’s progress towards meeting those
      requirements.
      <br>
      If you see any errors or omissions, I would appreciate hearing about them. (<em>Click on my
      name for an email link.</em>)
    </p>
    <p>
      <em>Thanks</em>,<br>
      <a href="mailto:cvickery@qc.cuny.edu?subject=DGW Report"
         class="signature">Christopher Vickery</a>
    </p>
  </div>
  """
  # Interpret the block if it hasn’t been done yet.
  parse_tree = row.parse_tree

  if parse_tree == {}:
    parse_results = (f'<section><h2>Parse tree for this block is unavailable at this time.</h2>'
                     f'</section')
  elif 'error' in parse_tree.keys():
    err_msg = parse_tree['error']
    parse_results = f'<section><h2 class="error">Parsing failed</h2><p>{err_msg}</p></section'
  else:
    parse_results = html_utils.list_to_html(parse_tree['header_list'], section='header')
    parse_results += html_utils.list_to_html(parse_tree['body_list'], section='body')

  return disclaimer + f"""
  <h1>{college_name} {row.requirement_id}: <em>{row.title}</em></h1>
  <p>Requirements for {catalog_type} Catalog Years {catalog_years_text}</p>
  {row.requirement_html}
  {parse_results}
  """


# __main__
# =================================================================================================
if __name__ == '__main__':
  """ Testing is done by running dgw_parser.py, and viewing the results in the website.
  """
  exit('Command line invocation not supported.')
