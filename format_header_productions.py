#! /usr/local/bin/python3
""" Format header productions. Return a formatted string for each type of rule that can appear
    in the header section of a block.

    Header productions may, optionally, include a label. Header-only productions are completely
    formatted here. Others use helper functions from format_body_productions to handle their
    non-label parts.

      _format_maxclass_head*
      _format_maxcredit_head*
      _format_maxpassfail_head
      _format_maxperdisc_head
      _format_maxtransfer_head
      _format_minclass_head
      _format_mincredit_head
      _format_mingpa_head
      _format_mingrade_head
      _format_minperdisc_head
      _format_minres_head*
      _format_share_head
      _format_under
      _dispatch_production
      format_header_productions
"""

import os
import sys
import psycopg


import format_body_rules

from format_body_qualifiers import format_maxpassfail, format_maxperdisc, format_maxtransfer, \
    format_minclass, format_mincredit, format_mingpa, format_mingrade, format_minperdisc, \
    format_minres, format_share

from format_utils import format_proxy_advice, format_remark, format_course_list, format_number, \
    format_num_class_credit, number_names

import format_utils

from catalogyears import catalog_years
from psycopg.rows import namedtuple_row
from typing import Any

DEBUG = os.getenv('DEBUG_HEADER')


# Header Qualifier Handlers
# =================================================================================================
""" About Labels and Course Lists

      The grammar differentiates between labels in the header (header_label) and body (label). But
      dgw_parser has turned them both into 'label' keys, so this module doesn't have to deal with
      that difference.

      In all cases where a header production allows (but does not require) a label, dgw_parser will
      supply a 'label' key for the dict, but its value can be None or the empty string. That is,
      there should be no KeyErrors when calling format_course_list(), but the result
      needs to be checked for emptiness.

      Likewise, in all cases where a header production allows (but does not require) a course_list,
      dgw_parser will supply a 'course_list' key for the dict, but its value can be None. That is,
      there should be no KeyErrors when calling format_course_list(), but the result
      needs to be checked for emptiness.
"""


# _format_conditional()
# -------------------------------------------------------------------------------------------------
def _format_conditional(conditional_dict: dict) -> str:
  """
  """
  return_str = f'<details><summary>If {conditional_dict["condition_str"]} is true</summary>'
  for rule_dict in conditional_dict['if_true']:
    return_str += '\n'.join([item for item in dispatch_header_productions(rule_dict)])
  if 'if_false' in conditional_dict.keys():
    else_details = '<details><summary>Otherwise</summary>'
    for rule_dict in conditional_dict['if_false']:
      else_details += '\n'.join([item for item in dispatch_header_productions(rule_dict)])
    else_details += '</details>'
    return_str += else_details

  return return_str + '</details>'


# _format_copy_header()
# -------------------------------------------------------------------------------------------------
def _format_copy_header(copy_header_dict: dict) -> str:
  """
  """
  institution = copy_header_dict['institution']
  requirement_id = copy_header_dict['requirement_id']

  # Get the (parsed) header_list from the target block
  return_str = f'<details><summary>Header Copied From {requirement_id}</summary>'
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      cursor.execute("""
      select institution, requirement_id, block_type, block_value, title as block_title,
             period_start, period_stop, parse_tree
        from requirement_blocks
       where institution = %s
         and requirement_id = %s
      """, (institution, requirement_id))
      if cursor.rowcount != 1:
        return f'<p class="error">Copy Header references non-existent block ({requirement_id})</p>'
      row = cursor.fetchone()

      if not row.period_stop.startswith('9'):
        years_text = catalog_years(row.period_start, row.period_stop).text
        return f'<p class="error">Copy Header: {requirement_id} is not current ({years_text})</p>'

      parse_tree = row.parse_tree
      try:
        header_list = parse_tree['header_list']
      except KeyError:
        parse_tree = dgw_parser(institution, requirement_id)
        if 'error' in parse_tree:
          return f'<p class="error">Copy Header: Error parsing header from {requirement_id}</p>'
        else:
          header_list = parse_tree['header_list']

  # Process the header list
  for rule_dict in header_list:
    return_str += '\n'.join([item for item in dispatch_header_productions(rule_dict)])

  return return_str + '</details>'


# _format_class_credit()
# -------------------------------------------------------------------------------------------------
def _format_class_credit(class_credit_dict: dict) -> str:
  """ No course list in the head. But pseudo, if true, means the number of classes and/or credits
      is not actually meaningful.
  """
  try:
    label_str = class_credit_dict['label']
  except KeyError:
    label_str = None

  return_str = f'<p>{format_num_class_credit(class_credit_dict)} required</p>'

  try:
    if class_credit_dict['pseudo']:
      return_str = return_str.replace('</p>', ' (nominal)</p>')
  except KeyError:
    pass

  try:
    return_str += format_proxy_advice(class_credit_dict['proxy_advice'])
  except KeyError as err:
    pass

  try:
    return_str += format_body_rules.format_remark(class_credit_dict['remark'])
  except KeyError:
    pass

  if label_str is not None:
    return f'<details><summary>{label_str}</summary>{return_str}</details>'
  else:
    return return_str


# _format_lastres()
# -------------------------------------------------------------------------------------------------
def _format_lastres(lastres_dict: dict) -> str:
  """
      lastres : LASTRES NUMBER (OF NUMBER)? class_or_credit \
                                                     course_list? tag? proxy_advice? header_label?;
  """
  try:
    label_str = lastres_dict['label']
  except KeyError:
    label_str = None

  try:
    course_list_str = format_course_list(lastres_dict['course_list'])
  except KeyError:
    course_list_str = ''

  class_credit = lastres_dict['class_or_credit']
  number = float(lastres_dict['number'])

  try:
    of_number = float(lastres_dict['of_number'])
    # ('m of n format')
    match (class_credit, course_list_str):
      case ['class', '']:
        lastres_str = (f'<p>At least {number} of the last {of_number} classes must be taken in '
                       f'residence</p>')
      case ['credit', '']:
        lastres_str = (f'<p>At least {number:.2f} of the last {of_number:.2f} credits must be '
                       f'taken in residence</p>')
      case ['class', class_str]:
        lastres_str = (f'<p>At least {number} of the last {of_number} of these classes must be '
                       f'taken in residence:</p>{class_str}')
      case ['credit', credit_str]:
        lastres_str = (f'<p>At least {number:2f} of the last {of_number:.2f} credits in these '
                       f'classes must be taken in residence:</p>{credit_str}')

  except KeyError:
    # ('m-only format')
    match (class_credit, course_list_str):
      case ['class', '']:
        lastres_str = (f'<p>At least {number} classes must be taken in residence</p>')
      case ['credit', '']:
        lastres_str = (f'<p>At least {number:.2f} credits must be taken in residence</p>')
      case ['class', class_str]:
        lastres_str = (f'<p>At least {number} of these classes must be taken in residence:</p>'
                       f'{class_str}')
      case ['credit', credit_str]:
        lastres_str = (f'<p>At least {number:.2f} credits in these classes must be taken in '
                       f'residence:</p>{credit_str}')

  try:
    lastres_str += format_proxy_advice(lastres_dict['proxy_advice'])
  except KeyError:
    pass

  if label_str:
    return f'<details><summary>{label_str}</summary>{lastres_str}</details>'
  else:
   return lastres_str


# _format_maxclass_head()
# -------------------------------------------------------------------------------------------------
def _format_maxclass_head(maxclass_head_dict: dict) -> str:
  """
      maxclass_head : maxclass label?;
      maxclass.     : MAXCLASS NUMBER course_list? tag?;

      This is a header-only production, so there is no body formatter available.
  """
  if DEBUG:
    print(f'_format_maxclass_head({maxclass_head_dict}', file=sys.stderr)

  try:
    label_str = maxclass_head_dict['label']
  except KeyError:
    label_str = None

  maxclass_dict = maxclass_head_dict['maxclass']
  number_str, is_unity = format_number(maxclass_dict['number'], is_int=True)
  suffix = '' if is_unity else 'es'
  if number_str == '0':
    maxclass_str = 'Zero classes allowed'
  else:
    maxclass_str = f'No more than {number_str} class{suffix} allowed'
  if course_list := format_course_list(maxclass_dict['course_list']):
    maxclass_str = (f'<details><summary>{maxclass_str} in the following courses:</summary>'
                    f'{course_list}</details>')
  else:
    maxclass_str = f'<p>{maxclass_str}</p>'

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxclass_str}</details>'
  else:
    return maxclass_str


# _format_maxcredit_head()
# -------------------------------------------------------------------------------------------------
def _format_maxcredit_head(maxcredit_head_dict: dict) -> str:
  """
      maxcredit_head : maxcredit label?;
      maxcredit.     : MAXCREDIT NUMBER course_list? tag?;

      This is a header-only production, so there is no body formatter available.
  """
  if DEBUG:
    print(f'_format_maxcredit_head({maxcredit_head_dict}', file=sys.stderr)

  try:
    label_str = maxcredit_head_dict['label']
  except KeyError:
    label_str = None

  maxcredit_dict = maxcredit_head_dict['maxcredit']

  # Number of maxcredits can be a range (weird)
  number_str, is_unity = format_number(maxcredit_dict['number'], is_int=False)
  suffix = '' if is_unity else 's'
  if number_str == '0.00':
    maxcredit_str = 'No credits allowed'
  else:
    maxcredit_str = f'No more than {number_str} credit{suffix} allowed'

  if course_list_str := format_course_list(maxcredit_dict['course_list']):
    maxcredit_str = (f'<details><summary>{maxcredit_str} in the following courses:</summary>'
                     f'{course_list_str}</details>')
  else:
    max_credit_str = f'<p>{max_credit_str}</p>'

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxcredit_info}</details>'
  else:
    return maxcredit_str


# _format_maxpassfail_head()
# -------------------------------------------------------------------------------------------------
def _format_maxpassfail_head(maxpassfail_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_maxpassfail_head({maxpassfail_head_dict}', file=sys.stderr)

  try:
    label_str = maxpassfail_head_dict['label']
  except KeyError:
    label_str = None

  maxpassfail_dict = maxpassfail_head_dict['maxpassfail']
  maxpassfail_info = format_maxpassfail(maxpassfail_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxpassfail_info}</details>'
  else:
    return maxpassfail_info


# _format_maxperdisc()
# -------------------------------------------------------------------------------------------------
def _format_maxperdisc_head(maxperdisc_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** _format_maxperdisc_head({maxperdisc_head_dict=})', file=sys.stderr)

  try:
    label_str = maxperdisc_head_dict['label']
  except KeyError:
    label_str = None

  maxperdisc_dict = maxperdisc_head_dict['maxperdisc']
  maxperdisc_info = format_maxperdisc(maxperdisc_dict)

  try:
    courses_str = format_course_list(maxperdisc_dict['course_list'])
    maxperdisc_info = maxperdisc_info.replace('</p>', ' in these courses:</p>')
    maxperdisc_info += courses_str
  except KeyError:
    pass

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxperdisc_info}</details>'
  else:
    return maxperdisc_info


# _format_maxterm_head()
# -------------------------------------------------------------------------------------------------
def _format_maxterm_head(maxterm_head_dict: dict) -> str:
  """ No course list in the header
  """

  try:
    label_str = maxterm_head_dict['label']
  except KeyError:
    label_str = None

  maxterm_dict = maxterm_head_dict['maxterm']

  class_credit = maxterm_dict['class_or_credit']
  number = int(maxterm_dict['number'])
  try:
    number_str = number_names[number]
  except IndexError:
    number_str = f'{number}'

  suffix = '' if number == 1 else 's'
  maxterm_str = f'<p>No more than {number_str} {class_credit}{suffix} may be taken each term'
  try:
    course_list_str = format_course_list(maxterm_dict['course_list'])
    maxterm_str += f' in the following courses:</p>{course_list_str}'
  except KeyError:
    maxterm_str += ' for this requirement</p>'

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxterm_str}</details>'
  else:
    return maxterm_str


# _format_maxtransfer_head()
# -------------------------------------------------------------------------------------------------
def _format_maxtransfer_head(maxtransfer_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_maxtransfer_head({maxtransfer_head_dict}', file=sys.stderr)

  try:
    label_str = maxtransfer_head_dict['label']
  except KeyError:
    label_str = None

  maxtransfer_dict = maxtransfer_head_dict['maxtransfer']
  maxtransfer_info = format_maxtransfer(maxtransfer_dict)

  try:
    courses_str = format_course_list(maxtransfer_dict['course_list'])
    maxtransfer_info = maxtransfer_info.replace('</p>', ' in these courses:</p>')
    maxtransfer_info += courses_str
  except KeyError:
    pass

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxtransfer_info}</details>'
  else:
    return maxtransfer_info


# _format_minclass_head()
# -------------------------------------------------------------------------------------------------
def _format_minclass_head(minclass_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** _format_minclass_head({minclass_head_dict=})', file=sys.stderr)

  try:
    label_str = minclass_head_dict['label']
  except KeyError:
    label_str = None

  minclass_dict = minclass_head_dict['minclass']
  minclass_info = format_minclass(minclass_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{minclass_info}</details>'
  else:
    return minclass_info


# _format_mincredit_head()
# -------------------------------------------------------------------------------------------------
def _format_mincredit_head(mincredit_head_dict: dict) -> str:
  """ MINCREDIT NUMBER course_list tag? proxy_advice?;
  """
  if DEBUG:
    print(f'_format_mincredit_head({mincredit_head_dict}', file=sys.stderr)

  try:
    label_str = mincredit_head_dict['label']
  except KeyError:
    label_str = None

  mincredit_html = format_mincredit(mincredit_head_dict['mincredit'])

  if label_str:
    print(f'{label_str=}')
    print(f'{mincredit_html=}')
    return f'<details><summary>{label_str}</summary>{mincredit_html}</details>'
  else:
    return mincredit_html


# _format_mingpa_head()
# -------------------------------------------------------------------------------------------------
def _format_mingpa_head(mingpa_head_dict: dict) -> str:
  """ MINGPA NUMBER (course_list | expression)? display*
  """
  if DEBUG:
    print(f'*** _format_mingpa_head({mingpa_head_dict})', file=sys.stderr)

  try:
    label_str = mingpa_head_dict['label']
  except KeyError:
    label_str = None

  mingpa_dict = mingpa_head_dict['mingpa']
  mingpa_info = format_mingpa(mingpa_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{mingpa_info}</details>'
  else:
    return mingpa_info


# _format_mingrade_head()
# -------------------------------------------------------------------------------------------------
def _format_mingrade_head(mingrade_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** _format_mingrade_head({mingrade_head_dict})', file=sys.stderr)

  try:
    label_str = mingrade_head_dict['label']
  except KeyError:
    label_str = None

  mingrade_dict = mingrade_head_dict['mingrade']
  mingrade_info = format_mingrade(mingrade_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{mingrade_info}</details>'
  else:
    return mingrade_info


# _format_minperdisc_head()
# -------------------------------------------------------------------------------------------------
def _format_minperdisc_head(minperdisc_head_dict: dict) -> str:
  """
      minperdisc_head : minperdisc label_head?
      minperdisc      : MINPERDISC NUMBER class_or_credit  LP SYMBOL (list_or SYMBOL)* RP tag?
                        display*;
  """
  if DEBUG:
    print(f'_format_minperdisc_head({minperdisc_head_dict}', file=sys.stderr)

  try:
    label_str = minperdisc_head_dict['label']
  except KeyError:
    label_str = None

  minperdisc_dict = minperdisc_head_dict['minperdisc']
  minperdisc_info = format_minperdisc(minperdisc_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{minperdisc_info}</details>'
  else:
    return minperdisc_info


# _format_minres_head()
# -------------------------------------------------------------------------------------------------
def _format_minres_head(minres_head_dict: dict) -> str:
  """
      minres_head : minres label?;
      minres      : MINRES (num_classes | num_credits) proxy_advice? tag?;
  """
  if DEBUG:
    print(f'_format_minres_head({minres_head_dict}', file=sys.stderr)

  try:
    label_str = minres_head_dict['label']
  except KeyError:
    label_str = None

  minres_html = format_minres(minres_head_dict['minres'])
  if label_str:
    return f'<details><summary>{label_str}</summary>{minres_html}</details>'
  else:
    return minres_html


# _format_header_tag()
# -------------------------------------------------------------------------------------------------
def _format_header_tag(header_tag_obj: Any) -> str:
  """ header_tag      : (HEADER_TAG nv_pair)+;

      This can be subsumed by class_credit_head, or can be a standalone header qualifier.
      if the name-value pair is RemarkJump or AdviceJump, give the link. Otherwise, show the name
      and value. Use hints as the text of anchor elements, if available.
      The hint and url show up as separate dicts because they are separate nv_pairs.
  """
  header_tag_list = header_tag_obj if isinstance(header_tag_obj, list) else [header_tag_obj]
  return_html = ''
  advice_url = advice_hint = remark_url = remark_hint = None
  for header_tag_dict in header_tag_list:
    assert isinstance(header_tag_dict, dict)
    for key, value in header_tag_dict.items():
      match key.lower():  # Even though it's supposed to be case-sensitive
        case 'advicejump':
          advice_url = value
        case 'remarkjump':
          remark_url = value
        case 'advicehint':
          advice_hint = value
        case 'remarkhint':
          remark_hint = value
        case _:
          value_str = 'Unspecified' if value is None else value
          return_html += f'<p>{key.lower()} is {value_str}</p>'
  # Show advice, even though it would not appear in an audit if the rule is complete.
  if advice_url:
    advice_text = advice_hint if advice_hint else 'More Information'
    return_html += f'<p><a href="{advice_url}">{advice_text}</a></p>'

  if remark_url:
    remark_text = remark_hint if remark_hint else 'More Information'
    return_html += f'<p><a href="{remark_url}">{remark_text}</a></p>'

  return return_html


# _format_optional()
# -------------------------------------------------------------------------------------------------
def _format_optional(optional_dict: dict) -> str:
  """
  """
  return '<p>These requirements are optional.</p>'


# _format_share_head()
# -------------------------------------------------------------------------------------------------
def _format_share_head(share_head_dict: dict) -> str:
  """ share_header : share label?;
      share        : (SHARE | DONT_SHARE) (NUMBER class_or_credit)? expression? tag?;
  """
  if DEBUG:
    print(f'_format_share_head({share_head_dict})', file=sys.stderr)

  try:
    label_str = share_head_dict['label']
  except KeyError:
    label_str = None

  share_dict = share_head_dict['share']
  share_info = format_share(share_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{share_info}</details>'
  else:
    return share_info


# _format_standalone()
# -------------------------------------------------------------------------------------------------
def _format_standalone(standalone_dict: dict) -> str:
  """
  """
  return """
  <p>
    Credits used to satisfy these requirements may also be used for any other requirements.
  </p>
  """


# _format_under()
# -------------------------------------------------------------------------------------------------
def _format_under(under_dict: dict) -> str:
  """
      Under Number class_or_credit course_list proxy_advice? header_label?
  """
  return_str = '<details>'

  label_str = under_dict['label']

  number = float(under_dict['number'])
  class_credit_str = under_dict['class_or_credit']
  s = ''
  if number != 1:
    s = 's' if class_credit_str == 'credit' else 'es'
  number_str = f'{int(number)}' if class_credit_str == 'class' else f'{number:.1f}'
  # I'm guessing the course list will never be just one course
  summary_str = f'Under {number_str} {class_credit_str}{s} allowed in these courses:'
  if label_str:
    return_str += f'<summary>{label_str}<br>{summary_str}</summary>'
  else:
    return_str += f'<summary>{summary_str}</summary>'
  try:
    return_str += format_proxy_advice(under_dict['proxy_advice'])
  except KeyError:
    pass

  return_str += format_course_list(under_dict['course_list'])

  return return_str + '</details>'


# dispatch_table {}
# -------------------------------------------------------------------------------------------------
dispatch_table = {'copy_header': _format_copy_header,
                  'header_class_credit': _format_class_credit,
                  'conditional': _format_conditional,
                  'header_maxclass': _format_maxclass_head,
                  'header_maxcredit': _format_maxcredit_head,
                  'header_maxpassfail': _format_maxpassfail_head,
                  'header_maxperdisc': _format_maxperdisc_head,
                  'header_maxterm': _format_maxterm_head,
                  'header_maxtransfer': _format_maxtransfer_head,
                  'header_minclass': _format_minclass_head,
                  'header_mincredit': _format_mincredit_head,
                  'header_mingpa': _format_mingpa_head,
                  'header_mingrade': _format_mingrade_head,
                  'header_minperdisc': _format_minperdisc_head,
                  'header_minres': _format_minres_head,
                  'header_tag': _format_header_tag,
                  'lastres': _format_lastres,
                  'optional': _format_optional,
                  'proxy_advice': format_proxy_advice,
                  'remark': format_remark,
                  'header_share': _format_share_head,
                  'standalone': _format_standalone,
                  'under': _format_under
                  }


# _dispatch_production()
# -------------------------------------------------------------------------------------------------
def _dispatch_production(production: str, production_info: Any) -> str:
  """ Dispatch a dict key:value pair, where the key is the name of a production, use the matching
      _format_xxx function to format the value into an HTML natural language string.
  """
  if DEBUG:
    print(f'*** _dispatch_production({production}, {production_info=})',
          file=sys.stderr)
  return dispatch_table[production](production_info)


# dispatch_header_productions()
# -------------------------------------------------------------------------------------------------
def dispatch_header_productions(node: dict) -> list:
  """ Given a dict that may or may not have keys for known productions return a list of formatted
      strings representing them.
  """
  if DEBUG:
    print(f'*** dispatch_header_productions(keys: {list(node.keys())}', file=sys.stderr)

  production_strings = []
  for key, value in node.items():
    if production_info := _dispatch_production(key, value):
      production_strings.append(production_info)
    else:
      print(f'**** No header info for {key}', file=sys.stderr)

  return production_strings
