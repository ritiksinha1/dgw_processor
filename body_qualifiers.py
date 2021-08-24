#! /usr/local/bin/python3
""" Format strings representing qualifiers.
"""

import os
import sys

import Any

DEBUG = os.getenv('DEBUG_QUALIFIERS')


# Qualifier Handlers
# =================================================================================================

# _format_maxpassfail()
# -------------------------------------------------------------------------------------------------
def _format_maxpassfail(maxpassfail_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_maxpassfail({maxpassfail_dict}', file=sys.stderr)

  try:
    number = float(maxpassfail_dict.pop('number'))
    class_credit = maxpassfail_dict.pop('class_credit')
    if class_credit == 'credit':
      if number == 0:
        return 'No credits may be taken pass/fail'
      suffix = '' if number == 1 else 's'
      return f'A maximum of {number:0.1f} credit{suffix} may be taken pass/fail'
    else:
      if number == 0:
        return 'No classes may be taken pass/fail'
      suffix = '' if number == 1 else 'es'
    return f'A maximum of {number:0} {class_credit}{suffix} may be taken pass/fail'
  except KeyError as ke:
    return f'Error: invalid MaxPassFail {ke} {maxperdisc_dict}'
  except ValueError as ve:
    return f'Error: invalid MaxPassFail {ve} {maxperdisc_dict}'


# _format_maxperdisc()
# -------------------------------------------------------------------------------------------------
def _format_maxperdisc(maxperdisc_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'*** _format_maxperdisc({maxperdisc_dict=})', file=sys.stderr)
  try:
    class_credit = maxperdisc_dict.pop('class_credit').lower()
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
    return f'No more than {number} {class_credit}{suffix} in ({", ".join(disciplines)})'
  except KeyError as ke:
    return f'Error: invalid MaxPerDisc {ke} {maxperdisc_dict}'
  except ValueError as ve:
    return f'Error: invalid MaxPerDisc {ve} {maxperdisc_dict}'


# _format_maxspread()
# -------------------------------------------------------------------------------------------------
def _format_maxspread(maxspread_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'*** _format_maxspread({maxspread_dict})', file=sys.stderr)
  print(maxspread_dict.keys())
  number = int(maxspread_dict['number'])

  return f'No more than {number} disciplines allowed'


# _format_maxtransfer()
# -------------------------------------------------------------------------------------------------
def _format_maxtransfer(maxtransfer_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'_format_maxtransfer({maxtransfer_dict}', file=sys.stderr)

  number = float(maxtransfer_dict.pop('number'))
  class_credit = maxtransfer_dict.pop('class_credit').lower()
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

  return f'No more than {number_str} transfer {class_credit}{suffix}{discipline_str} allowed'


# _format_minarea()
# -------------------------------------------------------------------------------------------------
def _format_minarea(minarea_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'_format_minarea({minarea_dict}', file=sys.stderr)

  try:
    number = int(minarea_dict.pop('number'))
    suffix = '' if number == 1 else 'es'
    return f'At least  {number} area{suffix} required'
  except KeyError as ke:
    return f'Error: Missing minimum number of areas'
  except ValueError as ve:
    return f'Error: Invalid minimum number of areas ({number})'


# _format_minclass()
# -------------------------------------------------------------------------------------------------
def _format_minclass(minclass_dict: dict) -> str:
  """ dict_keys(['number', 'course_list'])
  """
  if DEBUG:
    print(f'*** _format_minclass({minclass_dict=})', file=sys.stderr)

  try:
    number = int(minclass_dict.pop('number'))
    if number < 1:
      raise ValueError('MinClass with minimum less than 1.')
    suffix = '' if number == 1 else 'es'
    return f'At least  {number} class{suffix} required'
  except ValueError as ve:
    return f'Error: Invalid MinClass {ve} {minclass_dict=}'
  except KeyError as ke:
    return f'Error: Invalid MinClass {ke} {minclass_dict=}'


# _format_mincredit()
# -------------------------------------------------------------------------------------------------
def _format_mincredit(mincredit_dict: dict) -> str:
  """ dict_keys(['number', 'course_list'])
      We don't show the course_list here; that will or won't happen depending on the application.
  """
  if DEBUG:
    print(f'_format_mincredit({mincredit_dict}', file=sys.stderr)

  number = float(mincredit_dict.pop('number'))
  suffix = '' if number == 1.0 else 's'
  return f'At least {number:0.1f} credit{suffix} required'


# _format_mingpa()
# -------------------------------------------------------------------------------------------------
def _format_mingpa(mingpa_dict: dict) -> str:
  """ MINGPA NUMBER (course_list | expression)? tag? display* label?
      We don't show a course_list here; that will or won't happen depending on the application.
  """
  if DEBUG:
    print(f'*** _format_mingpa({mingpa_dict=})', file=sys.stderr)
  number = float(mingpa_dict.pop('number'))
  # But if there is an expression, do embed that in the response string.
  try:
    expression = f' {mingpa_dict.pop("expression").strip()} '
  except KeyError as ke:
    expression = ' '
  return f'Minimum GPA of {number:0.1f}{expression}required'


# _format_mingrade()
# -------------------------------------------------------------------------------------------------
def _format_mingrade(mingrade_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'*** _format_mingrade({mingrade_dict=})', file=sys.stderr)

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
  return f'Minimum grade of {letter} required'


# _format_minperdisc()
# -------------------------------------------------------------------------------------------------
def _format_minperdisc(minperdisc_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'_format_minperdisc({minperdisc_dict}', file=sys.stderr)

  number = float(minperdisc_dict.pop('number'))
  class_credit = minperdisc_dict.pop('class_credit').lower()
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

  return f'No more than {number_str} {class_credit}{suffix}{discipline_str} allowed'


# _format_minspread()
# -------------------------------------------------------------------------------------------------
def _format_minspread(minspread_dict: dict) -> str:
  """ {'number': qualifier_ctx.NUMBER().getText()}
  """
  if DEBUG:
    print(f'_format_minspread({minspread_dict}', file=sys.stderr)

  number = int(minspread_dict.pop('number'))
  suffix = '' if number == 1 else 's'
  return f'At least {number} discipline{suffix} required'


# dispatch()
# -------------------------------------------------------------------------------------------------
dispatch_table = {'maxpassfail': _format_maxpassfail,
                  'maxperdisc': _format_maxperdisc,
                  'maxspread': _format_maxspread,
                  'maxtransfer': _format_maxtransfer,
                  'minarea': _format_minarea,
                  'minclass': _format_minclass,
                  'mincredit': _format_mincredit,
                  'mingpa': _format_mingpa,
                  'mingrade': _format_mingrade,
                  'minperdisc': _format_minperdisc,
                  'minspread': _format_minspread,
                  }


# _dispatch_qualifier()
# -------------------------------------------------------------------------------------------------
def _dispatch_qualifier(qualifier: str, qualifier_info: Any) -> str:
  """ Dispatch a dict key:value pair, where the key is the name of a qualifier, use the matching
      _format_xxx function to format the value into an English string.
  """
  if DEBUG:
    print(f'*** _dispatch_qualifier({qualifier}, {qualifier_info=})', file=sys.stderr)
  return dispatch_table[qualifier](qualifier_info)


# format_body_qualifiers()
# -------------------------------------------------------------------------------------------------
def format_body_qualifiers(node: dict) -> list:
  """ Given a dict that may or may not have keys for known qualifiers remove all qualifiers from the
      node, and return a list of formatted strings representing the qualifiers found.
  """
  # The following qualifieres are legal, but we ignore ones that we don’t need.
  if DEBUG:
    print(f'*** _format_body_qualifiers({node.keys()=}', file=sys.stderr)
  possible_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                         'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                         'proxy_advice', 'rule_tag', 'samedisc', 'share']
  ignored_qualifiers = ['proxy_advice', 'rule_tag', 'samedisc', 'share']
  handled_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                        'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread']
  qualifier_strings = []
  for qualifier in possible_qualifiers:
    if qualifier in node.keys():
      if qualifier in ignored_qualifiers:
        continue
      if qualifier in handled_qualifiers:
        qualifier_info = node.pop(qualifier)
        qualifier_strings.append(_dispatch_qualifier(qualifier, qualifier_info))
      else:
        value = node.pop(qualifier)
        print(f'Error: unhandled qualifier: {qualifier}: {value}', file=sys.stderr)
        qualifier_strings.append(f'Error: unhandled qualifier: {qualifier}: {value}')

  return qualifier_strings
