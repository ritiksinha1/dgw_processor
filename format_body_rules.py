#! /usr/local/bin/python3
""" Functions to format the dicts that can appear in the body section
"""

import html_utils
import os
import psycopg
import sys

from psycopg.rows import namedtuple_row
from traceback import print_stack
from typing import Any


if os.getenv('DEBUG_BODY_RULES'):
  DEBUG = True
else:
  DEBUG = False

# The sequence of the following imports matters
from format_body_qualifiers import dispatch_body_qualifiers
import format_utils
import format_body_qualifiers


# format_block()
# -------------------------------------------------------------------------------------------------
def format_block(block_list_arg: Any) -> str:
  """
  """

  if isinstance(block_list_arg, list):
    block_dict = block_list_arg[0]
  else:
    block_dict = block_list_arg

  try:
    label_str = block_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  number = int(block_dict['number'])
  if number != 1:
    block_str = (f'<p class="error">Number of blocks other than one ({number}) encountered) '
                 f'not implemented yet</p>')
  else:
    block_type = block_dict['block_type']
    block_value = block_dict['block_value'].upper()
    institution = block_dict['institution']
    # Get the block
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute(f"""
          select parse_tree from requirement_blocks
          where institution = %s
          and block_type ~* %s
          and block_value ~* %s
          and period_stop ~* '^9'
          """, [institution, block_type, f'^{block_value}$'])
        block_type_str = 'Concentration'if block_type.lower() == 'conc' else block_type.title()
        block_str = f'<p>{block_value} {block_type_str.title()} Requirements:</p>'
        if cursor.rowcount == 0:
          block_str += f'<p class="error">Requirement Block not found!</p>'
        elif cursor.rowcount > 1:
          block_str += f'<p class="error">Multiple matching Requirement Blocks found!</p>'
        else:
          parse_tree = cursor.fetchone().parse_tree
          if parse_tree == {}:
            parse_results = f'<p class="error">No parse tree available for this block.</p>'
          elif 'error' in parse_tree.keys():
            err_msg = parse_tree['error']
            parse_results = f'<p>There was an error when this block was parsed: {err_msg}</p>'
          else:
            try:
              parse_results = html_utils.list_to_html(parse_tree['header_list'], section='header')
              parse_results += html_utils.list_to_html(parse_tree['body_list'], section='body')
            except Exception as e:
              print(f'{e=}')
          block_str += parse_results

  if summary:
    return f'<details>{summary}{block_str}</details>'
  else:
    return block_str


# format_blocktype()
# -------------------------------------------------------------------------------------------------
def format_blocktype(blocktype_arg: Any) -> str:
  """
  """

  if isinstance(blocktype_arg, list):
    blocktype_dict = blocktype_arg[0]
  else:
    blocktype_dict = blocktype_arg

  try:
    label_str = blocktype_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  number = int(blocktype_dict['number'])
  block_type = blocktype_dict['block_type'].title()
  if block_type == 'Conc':
    block_type = 'Concentration'

  if number == 1:
    blocktype_str = f'<p>A {block_type} is required.</p>'
  else:
    try:
      number = format_utils.number_names[number].title()
    except IndexError:
      pass
    blocktype_str = f'<p>{number} {block_type}s are required.</p>'

  if summary:
    return f'<details>{summary}{blocktype_str}</details>'
  else:
    return f'{blocktype_str}'


# format_class_credit()
# -------------------------------------------------------------------------------------------------
def format_class_credit(class_credit_arg: Any, prefix_str: str = None) -> str:
  """
  """
  if isinstance(class_credit_arg, list):
    if len(class_credit_arg) > 1:
      print(f'Multiple class_credit requirements not expected {class_credit_arg}', file=sys.stderr)
      return '<p class="error"> Multiple class/credit requirements not expected.</p>'
    else:
      class_credit_dict = class_credit_arg[0]
  else:
    class_credit_dict = class_credit_arg

  if prefix_str is None:
    prefix_str = ''

  try:
    label_str = class_credit_dict['label']
    summary = f'<summary>{prefix_str}{label_str}</summary>'
  except KeyError:
    summary = None

  # There has to be num classes and/or num credits
  class_credit_str = f'<p>{format_utils.format_num_class_credit(class_credit_dict)} required</p>'

  try:
    num_areas_required = int(class_credit_dict['minarea']['number'])
  except KeyError:
    num_areas_required = 0

  # There might be pseudo, remark, display, and/or share items. They get shown next as paragraphs.
  try:
    if class_credit_dict['is_pseudo']:
      class_credit_str += '<p>This requirement does not have a strict credit limit.</p>'
  except KeyError:
    pass
  try:
    if remark_str := class_credit_dict['remark']:
      class_credit_str += f'<p>Remark: <em>{remark_str}</em></p>'
  except KeyError:
    pass

  # display is student-specific
  try:
    if display_str := class_credit_dict['display']:
      class_credit_str += f'<p><em>{display_str}</em></p>'
      print('Examine this display_str in format_class_credit. Is it student-specific?:',
            display_str, file=sys.stderr)
  except KeyError:
    pass

  try:
    # print('dispatching body qualifiers')
    # Qualifiers: Expect list of html paragraphs, but it might be empty
    if qualifiers_list := dispatch_body_qualifiers(class_credit_dict):
      class_credit_str += '\n'.join(qualifiers_list)
    # print('ok so far')
    # If there is a list of courses, it gets shown as a display element.
    if courses_str := format_utils.format_course_list(class_credit_dict['course_list'],
                                                      num_areas_required):
      class_credit_str += courses_str
    # print('no prob w/ class_credit_dict')
  except TypeError as te:
    # This isn't supposed to happen
    print(te)
    print(class_credit_dict)
    exit()
  except KeyError as ke:
    pass

  if summary:
    return f'<details>{summary}{class_credit_str}</details>'
  else:
    return f'{prefix_str}{class_credit_str}'


# format_conditional()
# -------------------------------------------------------------------------------------------------
def format_conditional(conditional_dict: dict) -> str:
  """ Format a single conditional item from a list of them.
  """
  # Preconditions
  assert isinstance(conditional_dict, dict)

  condition_str = conditional_dict['condition_str']
  true_type = true_op = true_name = None
  # Simple case: major, minor, concentration is, or is not, something
  try:
    lp, true_type, true_op, true_name, rp = condition_str.split()
    if true_op not in ['=', '<>']:
      raise ValueError('Wrong true_op')
    true_type = 'Concentration' if true_type.lower() == 'conc' else true_type.title()
    op_name = 'is' if true_op == '=' else 'is not'
    summary_str = f'<summary>If {true_type} {op_name} {true_name.upper()}</summary>'
  except ValueError:
    # Not the simple case
    summary_str = f'<summary>If {condition_str} is True</summary>'

  conditional_body = ''
  for rule in conditional_dict['if_true']:
    for key, value in rule.items():
      if body_rule_str := dispatch_body_rule(key, value):
        conditional_body += body_rule_str
  else_summary = else_body = ''
  try:
    for rule in conditional_dict['if_false']:
      for key, value in rule.items():
        else_body += dispatch_body_rule(key, value)
    else_summary = f'<details><summary>Otherwise</summary>'
    else_body += '</details>'
  except KeyError:
    pass

  return f'<details>{summary_str}{conditional_body}{else_summary}{else_body}</details>'


# format_conditional_list()
# -------------------------------------------------------------------------------------------------
def format_conditional_list(conditional_list: list) -> str:
  """ Expect a conditional expression string, an if_true list of rules, and an optional if_false
      list of rules. (Note: conditionals don't have labels: they aren't requirements per se.)
      As a reminder of work to be done, we call format_conditional() to interpret the condition
      string and return a list of conditions required. But that function is only a stub, pending
      determination of what should actually be done to interpret the condition string.

      The list of rules gets dispatched back into this module, which requires this function to
      determine whether to dispatch through format_header_productions of format_body_rules.
  """
  assert isinstance(conditional_list, list), (f'conditional_list is {type(conditional_list)}, not '
                                              f'list')
  return_str = ''
  for conditional_item in conditional_list:
    try:
      conditional_dict = conditional_item['conditional']
    except KeyError:
      raise ValueError(f'Conditional item with no conditional key in [{conditional_item.keys()}]')

    return_str += format_conditional(conditional_dict)

  return return_str


# format_copy_rules()
# -------------------------------------------------------------------------------------------------
def format_copy_rules(copy_rules_dict: dict) -> str:
  """ Get the body of the referenced block, and display the rules from there.
  """

  try:
    try:
      label_str = copy_rules_dict['label']
      summary = f'<summary>{label_str}</summary>'
    except KeyError:
      summary = None

    institution = copy_rules_dict['institution']
    requirement_id = copy_rules_dict['requirement_id']
    block_type = copy_rules_dict['block_type']
    block_type = 'Concentration' if block_type == 'CONC' else block_type.title()
    block_value = copy_rules_dict['block_value']
    copy_rules_str = ''
    # Check that the block exists and is current
    if 'error' in copy_rules_dict.keys():
      error_msg = copy_rules_dict['error']
      copy_rules_str = f'<p class="error">{error_msg}</p>'
    else:
      # Get the parse_tree (this was not done by dgw_parser to avoid bloating the db)
      with psycopg.connect('dbname=cuny_curriculum') as conn:
        with conn.cursor(row_factory=namedtuple_row) as cursor:
          cursor.execute(f"""
            select parse_tree, title
              from requirement_blocks
             where institution = %s
               and requirement_id= %s
               and period_stop ~* '^9'
             """, [institution, requirement_id])
          if cursor.rowcount != 1:
            copy_rules_str = (f'<p class="error">No current parse tree found for {institution} '
                              f'{requirement_id}</p>')
          else:
            row = cursor.fetchone()
            copy_rules_str += f'<p>“{row.title}” Requirements</p>'
            body_list = row.parse_tree['body_list']
            for body_element in body_list:
              for key, value in body_element.items():
                copy_rules_str += dispatch_body_rule(key, value)

    if summary:
      return f'<details>{summary}{copy_rules_str}</details>'
    else:
      return copy_rules_str

  except psycopg.OperationalError as err:
    print(f'CopyRules from {institution} {requirement_id} Failed', file=sys.stderr)
    return(f'<p class="error">CopyRules Failed. Circular block reference?</p>')


# format_course_list_rule()
# -------------------------------------------------------------------------------------------------
def format_course_list_rule(course_list_rule: dict) -> str:
  """
  """
  return '<p class="error">format_course_list_rule() not implemented yet.</p>'


# format_group_requirements()
# -------------------------------------------------------------------------------------------------
def format_group_requirements(group_requirements: list) -> str:
  """ Each group requirement has a group_list, label, and number
      Each group_list is a list of groups(!)
      Each group can be a block, blocktype, class_credit, course_list, group_requirement,
                        noncourse, or rule_complete)
  """
  assert isinstance(group_requirements, list), (f'{type(group_requirements)} is not list '
                                                f'in format_group_requirements')
  group_requirements_str = ''
  for group_requirement in [gr['group_requirement'] for gr in group_requirements]:

    try:
      label_str = group_requirement['label']
      summary = f'<summary>{label_str}</summary>'
    except KeyError:
      summary = None

    num_required = int(group_requirement['number'])
    suffix = '' if num_required == 1 else 's'
    if num_required < len(format_utils.number_names):
      num_required_str = format_utils.number_names[num_required].lower()
    else:
      num_required_str = f'{num_required:,}'
    num_groups = len(group_requirement['group_list'])
    s = '' if num_groups == 1 else 's'

    if num_groups < len(format_utils.number_names):
      num_groups_str = format_utils.number_names[num_groups].lower()
    else:
      num_groups_str = f'{num_groups:,}'

    if num_required == num_groups:
      if num_required == 1:
        prefix = 'The'
      elif num_required == 2:
        prefix = 'Both of the'
      else:
        prefix = 'All of the'
    elif (num_required == 1) and (num_groups == 2):
      prefix = 'Either of the'
    else:
      prefix = f'Any {num_required_str} of the'
    group_requirement_str = f'<p>{prefix} following {num_groups_str} group{s}</p>'

    for index, requirement in enumerate(group_requirement['group_list']):
      for key in requirement.keys():
        match key:
          case 'block':
            group_requirement_str += format_block(requirement[key])
          case 'blocktype':
            group_requirement_str += format_blocktype(requirement[key])
          case 'class_credit':
            prefix_str = f'Group {format_utils.to_roman(index + 1)}: '
            group_requirement_str += format_class_credit(requirement[key], prefix_str)
          case 'course_list':
            group_requirement_str += format_course_list(requirement[key])
          case 'group_requirements':
            group_requirement_str += format_group_requirements(requirement[key])
          case 'noncourse':
            group_requirement_str += format_noncourse(requirement[key])
          case 'rule_complete':
            group_requirement_str += format_rule_complete(requirement[key])
          case 'label':
            pass  # Labels are extracted by one of the above matches
          case _:
            # Remarks will show up here? Or are they handled like labels??
            group_requirement_str += (f'<p>{key.title()}: {requirement[key]} requirement not '
                                      f'implemented.</p>')

    if summary:
      group_requirements_str += f'<details>{summary}{group_requirement_str}</details>'
    else:
      group_requirements_str += f'{group_requirement_str}'

  return group_requirements_str


# format_noncourse()
# -------------------------------------------------------------------------------------------------
def format_noncourse(noncourse_list: Any) -> str:
  """
  """

  # Seeing cases where it's a list, others where it's a single dict.
  if isinstance(noncourse_list, dict):
    noncourse_list = [noncourse_list]

  return_str = ''
  for noncourse_dict in noncourse_list:
    assert isinstance(noncourse_dict, dict)
    try:
      label_str = noncourse_dict['label']
      summary = f'<summary>{label_str}</summary>'
    except KeyError:
      summary = None

    number = int(noncourse_dict['number'])
    suffix = '' if number == 1 else 's'
    if number < len(format_utils.number_names):
      number_str = format_utils.number_names[number].title()
    else:
      number_str = f'{number:,}'

    expression = noncourse_dict['expression']
    # Not interpreting the expression yet
    noncourse_str = f'<p>{number_str} ({expression}){suffix}) required'

    if summary:
      return_str += f'<details>{summary}{noncourse_str}</details>'
    else:
      return_str += noncourse_str

  return return_str


# format_remark()
# -------------------------------------------------------------------------------------------------
def format_remark(remark_str: str) -> str:
  """
  """
  return f'<p>{remark_str}</p>'


# format_rule_complete()
# -------------------------------------------------------------------------------------------------
def format_rule_complete(rule_complete_dict: dict) -> str:
  """ rule_complete   : (RULE_COMPLETE | RULE_INCOMPLETE) (proxy_advice | rule_tag | label)*;

  """

  try:
    label_str = rule_complete_dict['label']
    summary = f'<summary>{label_str}</summary>'
  except KeyError:
    summary = None

  if rule_complete_dict['is_complete']:
    rule_complete_str = '<p>This rule is satisfied.</p>'
  else:
    rule_complete_str = '<p>This rule is <strong>not</strong> satisfied.</p>'

  try:
    rule_tag_dicts = rule_complete_dict['rule_tag']
    for rule_tag_dict in rule_tag_dicts:
      advice_url = advice_hint = remark_url = remark_hint = None
      assert isinstance(rule_tag_dict, dict)
      for key, value in rule_tag_dict.items():
        match key.lower():  # Even though it's supposed to be case-sensitive
          case 'advicejump':
            advice_url = value
          case 'remarkjump':
            remark_url = value
          case 'advicehint':
            advice_hint = value
          case 'remarkhint':
            remark_hint = value
            return_html += f'<p>For more information, see <a href="{value}">{value}</a></p>'
          case _:
            value_str = 'Unspecified' if value is None else value
            rule_complete_str += f'<p>{key.lower()} is {value_str}</p>'
    # Show advice, even though it would not appear in an audit if the rule is complete.
    if advice_url:
      advice_text = advice_hint if advice_hint else 'More Information'
      rule_complete_str += f'<p><a href="{advice_url}">{advice_text}</a></p>'
    if remark_url:
      remark_text = remark_hint if remark_hint else 'More Information'
      rule_complete_str += f'<p><a href="{remark_url}">{remark_text}</a></p>'
  except KeyError:
    pass

  if summary:
    return f'<display>{summary}{rule_complete_str}</display>'
  else:
    return rule_complete_str


# format_subset()
# -------------------------------------------------------------------------------------------------
def format_subset(subset_dict: dict) -> str:
  """  Subset dict keys:
         block
         blocktype
         class_credit_body
         conditional
         copy_rules
         course_list
         group
         label
         noncourse
         qualifier
         remark
         rule_complete
  """
  if DEBUG:
    print(f'*** format_subset({list(subset_dict.keys())})', file=sys.stderr)

  valid_keys = ['block', 'blocktype', 'class_credit_list', 'conditional', 'conditional_list',
                'copy_rules', 'course_list', 'group', 'label', 'noncourse', 'qualifier', 'remark',
                'rule_complete']
  for key in subset_dict.keys():
    if key not in valid_keys:
      print(f'Subset with invalid key: {key}', file=sys.stderr)

  try:
    label_str = subset_dict.pop('label')
  except KeyError:
    label_str = None

  subset_str = ''

# If there is a remark, it goes right after the summary
  try:
    subset_str += f'<p>{subset_dict.pop("remark")}</p>'
  except KeyError:
    pass

# Next, any qualifiers.
  try:
    if qualifiers_list := dispatch_body_qualifiers(subset_dict):
      subset_str += '\n'.join(qualifiers_list)
  except KeyError:
    pass

# Is this a non-course requirement?
  try:
    subset_str += format_noncourse(subset_dict.pop('noncourse'))
  except KeyError:
    pass

# Block, blocktype, copy_rules, rule_complete
  try:
    subset_str += format_block(subset_dict.pop('block'))
  except KeyError:
    pass

  try:
    subset_str += format_blocktype(subset_dict.pop('blocktype'))
  except KeyError:
    pass

  try:
    subset_str += format_copy_rules(subset_dict.pop('copy_rules'))
  except KeyError:
    pass

  try:
    subset_str += format_rule_complete(subset_dict.pop('rule_complete'))
  except KeyError:
    pass

# Course lists
  try:
    course_lists = subset_dict.pop('course_lists')
    for course_list in course_lists:
      subset_str += format_utils.format_course_list(course_list)
  except KeyError:
    pass

# this leaves conditional, group, and class_credit_list
  try:
    if conditional_list := subset_dict.pop('conditional_list'):
      subset_str += format_conditional_list(conditional_list)
  except KeyError:
    pass

  try:
    subset_str += format_group_requirements(subset_dict.pop('group_requirements'))
  except KeyError:
    pass

  try:
    if class_credit_list := subset_dict.pop('class_credit_list'):
      # The value of class_credit_list is a list of class_credit dicts.
      for class_credit_dict in class_credit_list:
        try:
          subset_str += format_class_credit(class_credit_dict['class_credit'])
        except KeyError as ke:
          print('Missing class_credit key in class_credit_dict: {ke}', file=sys.stderr)
  except KeyError:
    pass

  assert not subset_dict.keys(), f'Subset unhandled key(s): {list(subset_dict.keys())}'

  if label_str:
    return f'<details><summary>{label_str}</summary>{subset_str}</details>'
  else:
    return (f'<details><summary><span class="error">Missing Requirement Name</span></summary>'
            f'{subset_str}</details>')


# _dispatch_table {}
# -------------------------------------------------------------------------------------------------
_dispatch_table = {'block': format_block,
                   'blocktype': format_blocktype,
                   'class_credit': format_class_credit,
                   'conditional': format_conditional,
                   'conditional_list': format_conditional_list,
                   'copy_rules': format_copy_rules,
                   'course_list_rule': format_course_list_rule,
                   'group_requirements': format_group_requirements,
                   'noncourse': format_noncourse,
                   'proxy_advice': format_body_qualifiers.format_proxyadvice,
                   'remark': format_remark,
                   'rule_complete': format_rule_complete,
                   'subset': format_subset
                   }


# dispatch_body_rule()
# -------------------------------------------------------------------------------------------------
def dispatch_body_rule(dict_key: str, rule_dict: dict) -> str:
  """ If this fails, the formatter is not one of the top-level ones, and will have to be called
      directly.
  """
  try:
    return _dispatch_table[dict_key](rule_dict)
  except KeyError as ke:
    if dict_key not in list(_dispatch_table.keys()):
      print(f'No entry in _dispatch_table for {dict_key}', file=sys.stderr)
    else:
      print(f'KeyError {ke} while dispatching {dict_key} to {_dispatch_table[dict_key].__name__}',
            file=sys.stderr)
    return None
