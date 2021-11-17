#! /usr/local/bin/python3
""" Format header productions. Return a formatted string for each type of rule that can appear
    in the header section of a block.

    Header productions may, optionally, include a label. Header-only productions are marked with an
    asterisk, and are completely formatted here. The others use helper functions from
    format_body_productions to handle their non-label parts.

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
      _dispatch_production
      format_header_productions
"""

import os
import sys

import Any

import format_body_qualifiers

import format_utils

DEBUG = os.getenv('DEBUG_HEADER')


# Header Qualifier Handlers
# =================================================================================================

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
  number_str, is_unity = format_utils.format_number(maxclass_dict['number'], is_int=True)
  suffix = '' if is_unity else 'es'
  if number_str == '0':
    maxclass_str = 'Zero classes allowed'
  else:
    maxclass_str = f'No more than {number_str} class{suffix} allowed'
  if course_list := format_utils.format_course_list(maxclass_dict['course_list']):
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
  number_str, is_unity = format_utils.format_number(maxcredit_dict['number'], is_int=False)
  suffix = '' if is_unity else 's'
  if number_str == '0.00':
    maxcredit_str = 'No credits allowed'
  else:
    maxcredit_str = f'No more than {number_str} credit{suffix} allowed'

  if course_list_str := format_utils.format_course_list(maxcredit_dict['course_list']):
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
  maxpassfail_info = format_body_qualifiers.format_maxpassfail(maxpassfail_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxpassfail_info}<details>'
  else:
    return f'<p>{maxpassfail_info}</p>'


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
  maxperdisc_info = format_body_qualifiers.format_maxperdisc(maxperdisc_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxperdisc_info}<details>'
  else:
    return f'<p>{maxperdisc_info}</p>'


# _format_maxtransfer()
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
  maxtransfer_info = format_body_qualifiers.format_maxtransfer(maxtransfer_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{maxtransfer_info}<details>'
  else:
    return f'<p>{maxtransfer_info}</p>'


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
  minclass_info = format_body_qualifiers.format_minclass(minclass_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{minclass_info}<details>'
  else:
    return f'<p>{minclass_info}</p>'


# _format_mincredit_head()
# -------------------------------------------------------------------------------------------------
def _format_mincredit_head(mincredit_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_mincredit_head({mincredit_head_dict}', file=sys.stderr)

  try:
    label_str = mincredit_head_dict['label']
  except KeyError:
    label_str = None

  mincredit_dict = mincredit_head_dict['mincredit']
  mincredit_info = format_body_qualifiers.format_mincredit(mincredit_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{mincredit_info}<details>'
  else:
    return f'<p>{mincredit_info}<.p>'


# _format_mingpa_head()
# -------------------------------------------------------------------------------------------------
def _format_mingpa_head(mingpa_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** _format_mingpa_head({mingpa_head_dict})', file=sys.stderr)

  try:
    label_str = mingpa_head_dict['label']
  except KeyError:
    label_str = None

  mingpa_dict = mingpa_head_dict['mingpa']
  mingpa_info = format_body_qualifiers.format_mingpa(mingpa_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{mingpa_info}<details>'
  else:
    return f'<p>{mingpa_info}</p>'


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
  mingrade_info = format_body_qualifiers.format_mingrade(mingrade_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{mingrade_info}<details>'
  else:
    return f'<p>{mingrade_info}</p>'


# _format_minperdisc_head()
# -------------------------------------------------------------------------------------------------
def _format_minperdisc_head(minperdisc_head_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'_format_minperdisc_head({minperdisc_head_dict}', file=sys.stderr)

  try:
    label_str = minperdisc_head_dict['label']
  except KeyError:
    label_str = None

  minperdisc_dict = minperdisc_head_dict['minperdisc']
  minperdisc_info = format_body_qualifiers.format_minperdisc(minperdisc_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{minperdisc_info}<details>'
  else:
    return f'<p>{minperdisc_info}</p>'


# _format_minres_head()
# -------------------------------------------------------------------------------------------------
def _format_minres_head(minres_head_dict: dict) -> str:
  """
      minres_head : minres label?;
      minres.     : MINRES (num_classes | num_credits) display* tag?;
  """
  if DEBUG:
    print(f'_format_minres_head({minres_head_dict}', file=sys.stderr)

  try:
    label_str = minres_head_dict['label']
  except KeyError:
    label_str = None

  minres_dict = minres_head_dict['minres']
  try:
    if display_str := minres_dict['display']:
      display_str = f'<p>{display_str}</p>'
  except KeyError:
    display_str = ''
  class_credit_str = format_utils.format_num_class_credit(minres_dict)
  minres_info = f'<p>{class_credit_str} must be completed in residence.</p>'

  if label_str:
    return f'<details>{display_str}<summary>{label_str}</summary>{minres_info}<details>'
  else:
    return f'{display_str}{minres_info}'


# _format_share_head()
# -------------------------------------------------------------------------------------------------
def _format_share_head(share_head_dict: dict) -> str:
  """ share_header : share label?;
  """
  if DEBUG:
    print(f'_format_share_head({share_head_dict})', file=sys.stderr)

  try:
    label_str = share_head_dict['label']
  except KeyError:
    label_str = None

  share_dict = share_head_dict['share']
  share_info = format_body_qualifiers.format_share(share_dict)

  if label_str:
    return f'<details><summary>{label_str}</summary>{share_info}<details>'
  else:
    return f'<p>{share_info}</p>'


# dispatch_table {}
# -------------------------------------------------------------------------------------------------
dispatch_table = {'maxclass_head': _format_maxclass_head,
                  'maxcredit_head': _format_maxcredit_head,
                  'maxpassfail_head': _format_maxpassfail_head,
                  'maxperdisc_head': _format_maxperdisc_head,
                  'maxtransfer_head': _format_maxtransfer_head,
                  'mingpa_head': _format_mingpa_head,
                  'mingrade_head': _format_mingrade_head,
                  'minclass_head': _format_minclass_head,
                  'mincredit_head': _format_mincredit_head,
                  'minperdisc_head': _format_minperdisc_head,
                  'minres_head': _format_minres_head,
                  'share_head': _format_share_head
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


# dispatch_header_productions()
# -------------------------------------------------------------------------------------------------
def dispatch_header_productions(node: dict) -> list:
  """ Given a dict that may or may not have keys for known productions remove all known productions
      from the dict, and return a list of formatted strings representing them.
  """
  if DEBUG:
    print(f'*** dispatch_header_productions(keys: {list(node.keys())}', file=sys.stderr)

  production_strings = []
  for production in dispatch_table.keys():
    if production in node.keys():
      production_info = _dispatch_production(production, node.pop(production))
      if production_info is not None:
        production_strings.append(production_info)

  return production_strings
