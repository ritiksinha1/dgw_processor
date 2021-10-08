#! /usr/local/bin/python3
""" Format header productions. Return a formatted string for each type of rule that can appear
    in the header section of a block.

    Note that each production gets only a one-line string value here, suitable for adding to the
    program_requirements table.

    The productions that end in _head may, optionally, include a label.

head        :
            ( class_credit_head
            | conditional_head
            | lastres_head
            | maxclass_head
            | maxcredit_head
            | maxpassfail_head
            | maxperdisc_head
            | maxterm_head
            | maxtransfer_head
            | mingpa_head
            | mingrade_head
            | minclass_head
            | mincredit_head
            | minperdisc_head
            | minres_head
            | optional
            | proxy_advice
            | remark
            | share_head
            | standalone
            | under
            )*
            ;

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

import format_body_qualifiers

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

  if 'label' in maxpassfail_dict.keys():
    label_str = maxpassfail_dict['label']
    print(f'Unhandled label for maxpassfail: {label_str}', file=sys.stderr)

  try:
    number = float(maxpassfail_dict.pop('number'))
    class_credit = maxpassfail_dict.pop('class_or_credit')

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
  """ {'number': production_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'*** _format_maxperdisc({maxperdisc_dict=})', file=sys.stderr)

  if 'label' in maxperdisc_dict.keys():
    label_str = maxperdisc_dict['label']
    print(f'Unhandled label for maxperdisc: {label_str}', file=sys.stderr)

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
    return f'No more than {number} {class_credit}{suffix} in ({", ".join(disciplines)})'
  except KeyError as ke:
    return f'Error: invalid MaxPerDisc {ke} {maxperdisc_dict}'
  except ValueError as ve:
    return f'Error: invalid MaxPerDisc {ve} {maxperdisc_dict}'


# _format_maxtransfer()
# -------------------------------------------------------------------------------------------------
def _format_maxtransfer(maxtransfer_dict: dict) -> str:
  """ {'number': production_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'_format_maxtransfer({maxtransfer_dict}', file=sys.stderr)

  if 'label' in maxtransfer_dict.keys():
    label_str = maxtransfer_dict['label']
    print(f'Unhandled label for maxtransfer: {label_str}', file=sys.stderr)

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

  if 'label' in minclass_dict.keys():
    label_str = minclass_dict['label']
    print(f'Unhandled label for minclass: {label_str}', file=sys.stderr)

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

  if 'label' in mincredit_dict.keys():
    label_str = mincredit_dict['label']
    print(f'Unhandled label for mincredit: {label_str}', file=sys.stderr)

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
  return f'Minimum GPA of {number:0.2f}{expression}required'


# _format_minperdisc()
# -------------------------------------------------------------------------------------------------
def _format_minperdisc(minperdisc_dict: dict) -> str:
  """ {'number': production_ctx.NUMBER().getText(),
       'class_credit': class_credit,
       'disciplines': disciplines}
  """
  if DEBUG:
    print(f'_format_minperdisc({minperdisc_dict}', file=sys.stderr)

  if 'label' in minperdisc_dict.keys():
    label_str = minperdisc_dict['label']
    print(f'Unhandled label for minperdisc: {label_str}', file=sys.stderr)

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


# _format_share()
# -------------------------------------------------------------------------------------------------
def _format_share(share_dict: dict) -> str:
  """ share_header : share label?;
      Template: “[{label}: ]{num class_credit(s)} {Mm}ay {not} be shared {with expression requirements}”
  """
  if DEBUG:
    print(f'_format_share({share_dict})', file=sys.stderr)

  label_str = ''
  if 'label' in share_dict.keys():
    label_text = share_dict.pop('label')
    if label_text:
      label_str = f'{label_text}: '

  return f'{label_str}{format_body_qualifiers._format_share(share_dict)}'


# dispatch()
# -------------------------------------------------------------------------------------------------
dispatch_table = {'maxclass': _format_maxclass,
                  'maxcredit': _format_maxcredit,
                  'maxpassfail_head': _format_maxpassfail,
                  'maxperdisc_head': _format_maxperdisc,
                  'maxtransfer_head': _format_maxtransfer,
                  'mingpa_head': _format_mingpa,
                  'mingrade_head': format_body_qualifiers._format_mingrade,
                  'minclass_head': _format_minclass,
                  'mincredit_head': _format_mincredit,
                  'minperdisc_head': _format_minperdisc,
                  'minres_head': _format_minres,
                  'share_head': _format_share
                  }


# _dispatch_production()
# -------------------------------------------------------------------------------------------------
def _dispatch_production(production: str, production_info: Any) -> str:
  """ Dispatch a dict key:value pair, where the key is the name of a production, use the matching
      _format_xxx function to format the value into an English string.
  """
  if DEBUG:
    print(f'*** _dispatch_production({production}, {production_info=})',
          file=sys.stderr)
  return dispatch_table[production](production_info)


# format_header_productions()
# -------------------------------------------------------------------------------------------------
def format_header_productions(node: dict) -> list:
  """ Given a dict that may or may not have keys for known productions remove all known productions
      from the dict, and return a list of formatted strings representing them.
  """
  if DEBUG:
    print(f'*** format_header_productions(keys: {list(node.keys())}', file=sys.stderr)

  production_strings = []
  for production in dispatch_table.keys():
    production_info = _dispatch_production(production, node.pop(production))
    if production_info is not None:
      production_strings.append(production_info)

  return production_strings
