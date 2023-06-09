#! /usr/local/bin/python3
""" Format strings representing qualifiers.
      format_maxpassfail
      format_maxperdisc
      format_maxspread
      format_maxtransfer
      format_minarea
      format_minclass
      format_mincredit
      format_mingpa
      format_mingrade
      format_minperdisc
      format_minres
      format_minspread
      format_share
      _dispatch_qualifier
      format_body_qualifiers
"""

import os
import sys
import format_utils

from traceback import print_stack
from typing import Any

from format_utils import format_num_class_credit, format_course_list, format_proxy_advice

DEBUG = os.getenv('DEBUG_QUALIFIERS')


# Qualifier Handlers
# =================================================================================================

# format_maxpassfail()
# -------------------------------------------------------------------------------------------------
def format_maxpassfail(maxpassfail_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_maxpassfail({maxpassfail_dict})', file=sys.stderr)

  try:
    number = float(maxpassfail_dict.pop('number'))
    class_credit = maxpassfail_dict.pop('class_or_credit')
    if class_credit == 'credit':
      if number == 0:
        return '<p>No credits may be taken pass/fail.</p>'
      suffix = '' if number == 1 else 's'
      return f'<p>A maximum of {number:0.1f} credit{suffix} may be taken pass/fail.</p>'
    else:
      if number == 0:
        return '<p>No classes may be taken pass/fail.</p>'
      suffix = '' if number == 1 else 'es'
    return f'<p>A maximum of {number:0} {class_credit}{suffix} may be taken pass/fail.</p>'
  except KeyError as ke:
    return f'<p class="error"> invalid MaxPassFail {ke} {maxperdisc_dict}.</p>'
  except ValueError as ve:
    return f'<p class="error"> invalid MaxPassFail {ve} {maxperdisc_dict}.</p>'


# format_maxperdisc()
# -------------------------------------------------------------------------------------------------
def format_maxperdisc(maxperdisc_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'*** format_maxperdisc({maxperdisc_dict=})', file=sys.stderr)

  try:
    class_credit = maxperdisc_dict.pop('class_or_credit').lower()
    number = maxperdisc_dict.pop('number')
    if class_credit == 'class':
      number = int(number)
      suffix = '' if number == 1 else 's'
    elif class_credit == 'credit':
      number = float(number)
      suffix = '' if number == 1.0 else 'es'
    else:
      number = float('NaN')
      suffix = 'x'
    disciplines = sorted(maxperdisc_dict.pop('disciplines'))
    suffix += ' in ' if len(disciplines) == 1 else ' in each of: '
    return (f'<p>Up to {number} {class_credit}{suffix}{" and ".join(disciplines)}.</p>')
  except KeyError as ke:
    return f'<p class="error"> invalid MaxPerDisc {ke} {maxperdisc_dict}.</p>'
  except ValueError as ve:
    return f'<p class="error"> invalid MaxPerDisc {ve} {maxperdisc_dict}.</p>'


# format_maxspread()
# -------------------------------------------------------------------------------------------------
def format_maxspread(maxspread_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'*** format_maxspread({maxspread_dict})', file=sys.stderr)

  number = int(maxspread_dict['number'])
  suffix = '' if number == 1 else 's'
  return f'<p>No more than {number} discipline{suffix} allowed.</p>'


# format_maxtransfer()
# -------------------------------------------------------------------------------------------------
def format_maxtransfer(maxtransfer_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'format_maxtransfer({maxtransfer_dict})', file=sys.stderr)

  number = float(maxtransfer_dict.pop('number'))
  class_credit = maxtransfer_dict.pop('class_or_credit').lower()
  suffix = ''
  if number != 1:
    suffix = 's' if class_credit == 'credit' else 'es'

  number_str = f'{number:0.1f}' if class_credit == 'credit' else f'{int(number)}'

  discipline_str = ''
  try:
    disciplines = maxtransfer_dict.pop('disciplines')
    if len(disciplines) > 0:
      discipline_str = ' in ' + ', '.join(disciplines)
  except KeyError as ke:
    pass

  return (f'<p>No more than {number_str} transfer {class_credit}{suffix}{discipline_str} '
          f'allowed.</p>')


# format_minarea()
# -------------------------------------------------------------------------------------------------
def format_minarea(minarea_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'format_minarea({minarea_dict})', file=sys.stderr)

  try:
    number = int(minarea_dict.pop('number'))
    suffix = '' if number == 1 else 's'
    return f'<p>At least {number} area{suffix} required.</p>'
  except KeyError as ke:
    return f'<p class="error"> Missing minimum number of areas.</p>'
  except ValueError as ve:
    return f'<p class="error"> Invalid minimum number of areas ({number}).</p>'


# format_minclass()
# -------------------------------------------------------------------------------------------------
def format_minclass(minclass_dict: dict) -> str:
  """ dict_keys(['number', 'course_list'])
  """
  if DEBUG:
    print(f'*** format_minclass({minclass_dict=})', file=sys.stderr)

  try:
    number = int(minclass_dict['number'])
    if number < 1:
      raise ValueError('MinClass with minimum less than 1.')
    s = '' if number == 1 else 'es'
    return_str = f'<details><summary>At least {number} class{s} required in ...</summary>'
    try:
      return_str += format_course_list(minclass_dict['course_list']) + '</details>'
    except KeyError:
      return_str += '<p class="error">Error: Missing course list</p>'
  except ValueError as ve:
    return f'<p class="error"> Invalid MinClass {ve} {minclass_dict=}.</p>'
  except KeyError as ke:
    return f'<p class="error"> Invalid MinClass {ke} {minclass_dict=}.</p>'

  return return_str


# format_mincredit()
# -------------------------------------------------------------------------------------------------
def format_mincredit(mincredit_dict: dict) -> str:
  """ MINCREDIT NUMBER course_list tag? proxy_advice?;
  """
  if DEBUG:
    print(f'format_mincredit({mincredit_dict})', file=sys.stderr)

  try:
    return_html = format_proxy_advice(mincredit_dict)
  except KeyError:
    return_html = ''

  number = float(mincredit_dict.pop('number'))
  suffix = '' if number == 1.0 else 's'
  summary_str = f'At least {number:0.1f} credit{suffix} required in the following courses:'

  course_list_html = format_course_list(mincredit_dict['course_list'])

  return f'<details><summary>{summary_str}</summary>{course_list_html}</details>'


# format_mingpa()
# -------------------------------------------------------------------------------------------------
def format_mingpa(mingpa_dict: dict) -> str:
  """ MINGPA NUMBER (course_list | expression)? tag? proxy_advice?;
  """
  if DEBUG:
    print(f'*** format_mingpa({mingpa_dict=})', file=sys.stderr)

  # Possible display text
  try:
    display_str = f'<p><strong>{mingpa_dict["proxy_advice"]}</strong>.</p>'
  except KeyError:
    display_str = ''

  number = float(mingpa_dict.pop('number'))
  mingpa_html = f'{display_str}<p>A GPA of at least {number:0.2f} is required'

  # There might be either an expression or a course list, but not both
  # ------------------------------------------------------------------
  # If there is an expression, add that to the return string.
  try:
    mingpa_html += f' in <span class="warning">{mingpa_dict["expression"]}</span>.'
  except KeyError:
    pass

  # If there is a course list, it may come back as a string or, if there were areas, as a details
  # element.
  try:
    if course_list_html := format_course_list(mingpa_dict['course_list']):
      if '<details>' in course_list_html:
        mingpa_html += f' in the following courses:.</p>{course_list_html}'
      else:
        mingpa_html += f' in the following courses: {course_list_html}.</p>'
  except KeyError:
    pass

  return mingpa_html


# format_mingrade()
# -------------------------------------------------------------------------------------------------
def format_mingrade(mingrade_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'*** format_mingrade({mingrade_dict=})', file=sys.stderr)

  # Convert GPA values to letter grades by table lookup.
  # int(round(3×GPA)) gives the index into the letters table.
  # Index positions 0 and 1 aren't actually used.
  """
          GPA  3×GPA  Index  Letter
          4.3   12.9     13      A+
          4.0   12.0     12      A
          3.7   11.1     11      A-
          3.3    9.9     10      B+
          3.0    9.0      9      B
          2.7    8.1      8      B-
          2.3    6.9      7      C+
          2.0    6.0      6      C
          1.7    5.1      5      C-
          1.3    3.9      4      D+
          1.0    3.0      3      D
          0.7    2.1      2      D-
    """
  letters = ['F', 'F', 'D-', 'D', 'D+', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+']

  number = float(mingrade_dict.pop('number'))
  if number < 1.0:
    number = 0.7
  # Lots of values greater than 4.0 have been used to mean "no upper limit."
  if number > 4.0:
    number = 4.0
  letter = letters[int(round(number * 3))]
  return f'<p>Minimum grade of {letter} required.</p>'


# format_minperdisc()
# -------------------------------------------------------------------------------------------------
def format_minperdisc(minperdisc_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText(),
       'class_or_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'format_minperdisc({minperdisc_dict})', file=sys.stderr)

  number = float(minperdisc_dict.pop('number'))
  class_credit = minperdisc_dict.pop('class_or_credit').lower()
  suffix = ''
  if number != 1:
    suffix = 's' if class_credit == 'credit' else 'es'

  number_str = f'{number:0.1f}' if class_credit == 'credit' else f'{int(number)}'

  discipline_str = ''
  try:
    disciplines = minperdisc_dict.pop('disciplines')
    if len(disciplines) > 0:
      discipline_str = ' in ' + ', '.join(disciplines)
  except KeyError as ke:
    pass

  return f'<p>No more than {number_str} {class_credit}{suffix}{discipline_str} allowed.</p>'


# format_minres()
# -------------------------------------------------------------------------------------------------
def format_minres(minres_dict: dict) -> str:
  """ MINRES (num_classes | num_credits) proxy_advice? tag?;
  """
  if DEBUG:
    print(f'format_minres({minres_dict})', file=sys.stderr)

  try:
    proxy_str = format_proxy_advice(minres_dict['proxy_advice'])
  except KeyError:
    proxy_str = ''

  return (f'{proxy_str}<p>{format_num_class_credit(minres_dict)} must be completed in '
          f'residence.</p>')


# format_minspread()
# -------------------------------------------------------------------------------------------------
def format_minspread(minspread_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'format_minspread({minspread_dict})', file=sys.stderr)

  number = int(minspread_dict.pop('number'))
  suffix = '' if number == 1 else 's'
  return f'<p>At least {number} discipline{suffix} required.</p>'


# format_ruletag()
# -------------------------------------------------------------------------------------------------
def format_ruletag(rule_tag_obj: Any) -> str:
  """ rule_tag      : (RULE_TAG nv_pair)+;
  """
  rule_tag_list = rule_tag_obj if isinstance(rule_tag_obj, list) else [rule_tag_obj]
  return_html = ''
  for rule_tag_dict in rule_tag_list:
    assert isinstance(rule_tag_dict, dict)
    for key, value in rule_tag_dict.items():
      match key.lower():
        case 'advicejump' | 'rulejump':
          return_html += f'<p>For more information, see <a href="{value}">{value}</a></p>'
        case _:
          value_str = 'Unspecified' if value is None else value
          return_html += f'<p>Degree Audit {key.title()} is {value_str}</p>'

  return return_html


# format_share()
# -------------------------------------------------------------------------------------------------
def format_share(share_dict: dict) -> str:
  """ share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
      Template: “{num class_credit(s)} {Mm}ay {not} be shared {with expression requirements}”
  """
  if DEBUG:
    print(f'format_share({share_dict})', file=sys.stderr)

  try:
    number = float(share_dict['number'])
    class_credit = share_dict['class_credit']
    if class_credit == 'class':
      suffix = '' if number == 1.0 else 'es'
      number_str = f'{number:.0f}'
    else:
      suffix = '' if number == 1.0 else 's'
      number_str = f'{number:.1f}'
    prefix_str = f'{number_str} {class_credit}{suffix} may'
  except KeyError as ke:
    prefix_str = 'May'

  not_str = ' ' if share_dict['allow_sharing'] else ' not '

  try:
    expression_str = share_dict['expression'].strip(')(')
    suffix_str = f' with “<span class="warning">{expression_str}</span>” requirements'
  except KeyError as ke:
    suffix_str = f''

  return f'<p>{prefix_str}{not_str}be shared{suffix_str}.</p>'


# _dispatch_table {}
# -------------------------------------------------------------------------------------------------
_dispatch_table = {'maxpassfail': format_maxpassfail,
                   'maxperdisc': format_maxperdisc,
                   'maxspread': format_maxspread,
                   'maxtransfer': format_maxtransfer,
                   'minarea': format_minarea,
                   'minclass': format_minclass,
                   'mincredit': format_mincredit,
                   'mingpa': format_mingpa,
                   'mingrade': format_mingrade,
                   'minperdisc': format_minperdisc,
                   'minres': format_minres,
                   'minspread': format_minspread,
                   'rule_tag': format_ruletag,
                   'share': format_share,
                   }


# _dispatch_qualifier()
# -------------------------------------------------------------------------------------------------
def _dispatch_qualifier(qualifier: str, qualifier_info: Any) -> str:
  """ Dispatch a dict key:value pair, where the key is the name of a qualifier, use the matching
      format_xxx function to format the value into an English string.
  """
  if DEBUG:
    print(f'*** _dispatch_qualifier({qualifier}, {qualifier_info=})', file=sys.stderr)

  return _dispatch_table[qualifier](qualifier_info)


# dispatch_body_qualifiers()
# -------------------------------------------------------------------------------------------------
def dispatch_body_qualifiers(node: dict) -> list:
  """ Given a dict that may or may not have keys for known qualifiers return a list of HTML
      formatted strings representing the handled qualifiers found. Remove the ones found; report any
      unhandled ones.
  """
  assert isinstance(node, dict), (f'{type(node)} is not dict in format_body_qualifiers. {node=}')

  if DEBUG:
    print(f'*** dispatch_body_qualifiers({node.keys()=}', file=sys.stderr)

  possible_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                         'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                         'proxy_advice', 'rule_tag', 'samedisc', 'share']
  handled_qualifiers = _dispatch_table.keys()
  qualifier_strings = []
  for qualifier in possible_qualifiers:
    if qualifier in node.keys():
      if qualifier in handled_qualifiers:
        qualifier_dict = node.pop(qualifier)
        # print('*** qualifier:', qualifier)
        if qualifier_str := _dispatch_qualifier(qualifier, qualifier_dict):
          qualifier_strings.append(qualifier_str)
      else:
        print(f'Unhandled body qualifier: {qualifier_dict}', file=sys.stderr)

  return qualifier_strings
