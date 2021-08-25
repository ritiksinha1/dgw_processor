#! /usr/local/bin/python3
""" Format block_level qualifiers. Return a formatted string for each type of rule that can appear
    in the header section of a block.

    Note that each qualifier gets only a one-line string value here, suitable for adding to the
    program_requirements table.

head : ( class_credit_head',
       | conditional_head   ? See if this is used for major, minor, conc; might be degree-only
       | lastres            ?
       | maxclass',
       | maxcredit',
       | maxpassfail',
       | maxperdisc',
       | maxterm
       | maxtransfer',
       | mingrade',
       | minclass',
       | mincredit',
       | mingpa',
       | minperdisc',
       | minres',
       | optional           ?
       | proxy_advice
       | remark',
       | share              ?
       | standalone         ?
       | under
       )*

  These are the ones currently handled: others may need to be added in the future
        maxclass
        maxcredit
        maxpassfail
        maxperdisc
        maxtransfer
        minclass
        mincredit
        mingrade
        mingpa
        minperdisc
        minres
        remark
"""

import os
import sys

import Any

DEBUG = os.getenv('DEBUG_HEADER')


# Header Qualifier Handlers
# =================================================================================================

# _format_maxclass()
# -------------------------------------------------------------------------------------------------
def _format_maxclass(maxclass_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_maxclass({maxpassfail_dict}', file=sys.stderr)

  num_class = int(maxclass_dict.pop('number'))
  class_suffix = '' if num_class == 1 else 'es'
  course_list = maxclass_dict.pop('course_list')
  num_active = len(course_list['active_courses'])
  active_suffix = '' if num_active == 1 else 's'
  return (f'No more than {num_class} credit{class_suffix} from a set of {num_active} '
          f'active course{active_suffix} allowed')


# _format_maxcredit()
# -------------------------------------------------------------------------------------------------
def _format_maxcredit(maxcredit_dict: dict) -> str:
  """ When the number is zero, it means "none of" the courses in the list, but when > zero, it
      really is a maximum. In either case the course list can be very long. We list the number of
      active courses here.
  """
  if DEBUG:
    print(f'_format_maxcredit({maxcredit_dict}', file=sys.stderr)

  num_credit = float(maxcredit_dict.pop('number'))
  credit_suffix = '' if num_credit == 1.0 else 's'
  course_list = maxcredit_dict.pop('course_list')
  num_active = len(course_list['active_courses'])
  active_suffix = '' if num_active == 1 else 's'
  return (f'No more than {num_credit:0.1f} credit{credit_suffix} from a set of {num_active} '
          f'active course{active_suffix} allowed')


# _format_maxpassfail()
# -------------------------------------------------------------------------------------------------
def _format_maxpassfail(maxpassfail_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_maxpassfail({maxpassfail_dict}', file=sys.stderr)

  try:
    number = float(maxpassfail_dict.pop('number'))
    class_credit = maxpassfail_dict.pop('class_or_credit')
    print(number, class_credit)
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
    return f'Error: invalid MaxPassFail {ke} {maxpassfail_dict}'
  except ValueError as ve:
    return f'Error: invalid MaxPassFail {ve} {maxpassfail_dict}'


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
  letter = letters[int(round(3 * number))]
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


# _format_minres()
# -------------------------------------------------------------------------------------------------
def _format_minres(minres_dict: dict) -> str:
  """  {'minres': {'allow_classes': None,
                   'allow_credits': None,
                   'conjunction': None,
                   'label': None,
                   'max_classes': None,
                   'max_credits': 41.0,
                   'min_classes': None,
                   'min_credits': 41.0}},
  """
  if DEBUG:
    print(f'_format_minres({minres_dict}', file=sys.stderr)

  conjunction = minres_dict.pop('conjunction')
  label = minres_dict.pop('label')
  if label is not None:
    label_str = f'{label}: '
  else:
    label_str = ''
  min_classes = minres_dict.pop('min_classes')
  max_classes = minres_dict.pop('max_classes')
  min_credits = minres_dict.pop('min_credits')
  max_credits = minres_dict.pop('max_credits')

  if min_classes is not None:
    if min_classes == max_classes:
      num_classes = min_classes
    else:
      num_classes = f'between {min_classes} and {max_classes}'
  else:
    num_classes = None
  if min_credits is not None:
    if min_credits == max_credits:
      num_credits = min_credits
    else:
      num_credits = f'between {min_credits} and {max_credits}'
  else:
    num_credits = None

  if num_classes is not None and num_credits is not None:
    return (f'{label_str}At least {num_classes} classes {conjunction} {num_credits} must be '
            f'taken in residence')
  if num_classes:
    return f'{label_str}At least {num_classes} classes must be taken in residence'
  if num_credits:
    return f'{label_str}At least {num_credits} credits must be taken in residence'
  return 'Error: MinRes with neither classes nor credits specified.'


# _format_remark()
# -------------------------------------------------------------------------------------------------
def _format_remark(remark_str: str) -> str:
  """ The value of a remark key is just the string.
  """
  if DEBUG:
    print(f'_format_remark({remark_str}', file=sys.stderr)

  return f'Message: {remark_str}'


# dispatch()
# -------------------------------------------------------------------------------------------------
dispatch_table = {'maxclass': _format_maxclass,
                  'maxcredit': _format_maxcredit,
                  'maxpassfail': _format_maxpassfail,
                  'maxperdisc': _format_maxperdisc,
                  'maxtransfer': _format_maxtransfer,
                  'mingrade': _format_mingrade,
                  'minclass': _format_minclass,
                  'mincredit': _format_mincredit,
                  'mingpa': _format_mingpa,
                  'minperdisc': _format_minperdisc,
                  'minres': _format_minres,
                  'remark': _format_remark
                  }


# _dispatch_qualifier()
# -------------------------------------------------------------------------------------------------
def _dispatch_qualifier(qualifier: str, qualifier_info: Any) -> str:
  """ Dispatch a dict key:value pair, where the key is the name of a qualifier, use the matching
      _format_xxx function to format the value into an English string.
  """
  if DEBUG:
    print(f'*** _dispatch_qualifier({qualifier}, {qualifier_info=})',
          file=sys.stderr)
  return dispatch_table[qualifier](qualifier_info)


# format_header_qualifiers()
# -------------------------------------------------------------------------------------------------
def format_header_qualifiers(node: dict) -> list:
  """ Given a dict that may or may not have keys for known qualifiers remove all qualifiers from the
      node, and return a list of formatted strings representing the qualifiers found.
  """
  # The following qualifieres are legal, but we ignore ones that we don’t need.
  if DEBUG:
    print(f'*** format_header_qualifiers({node.keys()=}', file=sys.stderr)
  handled_qualifiers = ['maxclass', 'maxcredit', 'maxpassfail', 'maxperdisc', 'maxtransfer',
                        'mingrade', 'minclass', 'mincredit', 'mingpa', 'minperdisc', 'minres',
                        'remark']
  qualifier_strings = []
  for qualifier in handled_qualifiers:
    try:
      qualifier_info = node.pop(qualifier)
      qualifier_strings.append(_dispatch_qualifier(qualifier, qualifier_info))
    except KeyError as ke:
      # Ignore anything not in the dispatch table.
      pass

  return qualifier_strings
