#! /usr/local/bin/python3
""" Functions to format the dicts that can appear in the body section
"""

import os
import sys

if os.getenv('DEBUG_BODY_RULES'):
  DEBUG = True
else:
  DEBUG = False

import htmlificization


# format_block()
# -------------------------------------------------------------------------------------------------
def format_block(block_dict: dict) -> str:
  """
  """

  try:
    label_str = block_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  number = int(block_dict['number'])
  if number != 1:
    block_str = ('<p class="error">Number of blocks other than one ({number} encountered) '
                 f'not implemented yet</p>')
  else:
    block_type = block_dict['block_type'].title()
    if block_type == 'Conc':
      block_type = 'Concentration'
    block_value = block_dict['block_value']
    block_str = f'<p>The {block_value} {block_value} is required</p>'

  if summary:
    return f'<details>{summary}{block_str}</details>'
  else:
    return f'{block_str}'


# format_blocktype()
# -------------------------------------------------------------------------------------------------
def format_blocktype(blocktype_dict: dict) -> str:
  """
  """

  try:
    label_str = blocktype_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  blocktype_str = '<p class="error">Blocktype not implemented yet</p>'

  if summary:
    return f'<details>{summary}{blocktype_str}</details>'
  else:
    return f'{blocktype_str}'


# format_class_credit_body()
# -------------------------------------------------------------------------------------------------
def format_class_credit_body(class_credit_body_dict: dict) -> str:
  """
  """

  try:
    label_str = class_credit_body_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  class_credit_body_str = '<p class="error">Class-Credit not implemented yet</p>'

  if summary:
    return f'<details>{summary}{class_credit_body_str}</details>'
  else:
    return f'{class_credit_body_str}'


# format_copy_rules()
# -------------------------------------------------------------------------------------------------
def format_copy_rules(copy_rules_dict: dict) -> str:
  """
  """

  try:
    label_str = copy_rules_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  copy_rules_str = '<p class="error">Copy rules not implemented yet</p>'

  if summary:
    return f'<details>{summary}{copy_rules_str}</details>'
  else:
    return f'{copy_rules_str}'


# format_group_requirement()
# -------------------------------------------------------------------------------------------------
def format_group_requirement(group_requirement_dict: dict) -> str:
  """
  """

  try:
    label_str = group_requirement_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  group_requirement_str = '<p class="error">Group requirement not implemented yet</p>'

  if summary:
    return f'<details>{summary}{group_requirement_str}</details>'
  else:
    return f'{group_requirement_str}'


# format_conditional()
# -------------------------------------------------------------------------------------------------
def format_conditional(conditional_dict: dict) -> str:
  """
  """

  try:
    label_str = conditional_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  conditional_str = '<p class="error">Conditional not implemented yet</p>'

  if summary:
    return f'<details>{summary}{conditional_str}</details>'
  else:
    return f'{conditional_str}'


# format_maxperdisc()
# -------------------------------------------------------------------------------------------------
def format_maxperdisc(maxperdisc_dict: dict) -> str:
  """
  """

  try:
    label_str = maxperdisc_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  maxperdisc_str = '<p class="error">Maxperdisc not implemented yet</p>'

  if summary:
    return f'<details>{summary}{maxperdisc_str}</details>'
  else:
    return f'{maxperdisc_str}'


# format_noncourse()
# -------------------------------------------------------------------------------------------------
def format_noncourse(noncourse_dict: dict) -> str:
  """
  """

  try:
    label_str = noncourse_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  number = int(noncourse_dict['number'])
  suffix = '' if number == 1 else 's'
  if number < len(htmlificization.number_names):
    number_str = htmlificization.number_names[number].title()
  else:
    number_str = f'{number:,}'

  expression = noncourse_dict['expression']
  # Not interpreting the expression yet
  noncourse_str = '<p>{number_str} ({expression}){suffix) required'

  if summary:
    return f'<details>{summary}{noncourse_str}</details>'
  else:
    return noncourse_str


# format_proxy_advice()
# -------------------------------------------------------------------------------------------------
def format_proxy_advice(proxy_advice_dict: dict) -> str:
  """ Ignoring proxy advice
  """

  proxy_advice_str = '<p class="error">proxy_advice not implemented (yet)</p>'

  return ''


# format_remark()
# -------------------------------------------------------------------------------------------------
def format_remark(remark_str: str) -> str:
  """
  """
  return f'<p>{remark_str}</p>'


# format_rule_complete()
# -------------------------------------------------------------------------------------------------
def format_rule_complete(rule_complete_dict: dict) -> str:
  """
  """

  try:
    label_str = rule_complete_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  if rule_complete['is_complete']:
    rule_complete_str = '<p>This rule is satisfied.</p>'
  else:
    rule_complete_str = '<p>This rule is <strong>not</strong> satisfied.</p>'

  if summary:
    return f'<display>{summary}{rule_complete_str}</display>'
  else:
    return rule_complete_str


# format_rule_tag()
# -------------------------------------------------------------------------------------------------
def format_rule_tag(rule_tag_dict: dict) -> str:
  """ Ignoring rule_tag
  """

  rule_tag_str = '<p class="error">Rule tag not implemented yet</p>'

  return ''


# format_subset()
# -------------------------------------------------------------------------------------------------
def format_subset(subset_dict: dict) -> str:
  """
  """

  try:
    label_str = subset_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  subset_str = '<p class="error">Subset not implemented yet</p>'

  if summary:
    return f'<details>{summary}{subset_str}</details>'
  else:
    return f'{subset_str}'


# format_dispatch_table {}
# -------------------------------------------------------------------------------------------------
dispatch_table = {'block': format_block,
                  'blocktype': format_blocktype,
                  'class_credit_body': format_class_credit_body,
                  'copy_rules': format_copy_rules,
                  'group_requirement': format_group_requirement,
                  'conditional': format_conditional,
                  'maxperdisc': format_maxperdisc,
                  'noncourse': format_noncourse,
                  'proxy_advice': format_proxy_advice,
                  'remark': format_remark,
                  'rule_complete': format_rule_complete,
                  'rule_tag': format_rule_tag,
                  'subset': format_subset
                  }


# format_body_rule()
# -------------------------------------------------------------------------------------------------
def format_body_rule(dict_key: str, rule_dict: dict) -> str:
  """ If this fails, the formatter is not one of the top-level ones, and will have to be called
      directly.
  """
  try:
    return dispatch_table[dict_key](rule_dict)
  except KeyError:
    return None
