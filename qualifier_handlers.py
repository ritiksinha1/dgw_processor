#! /usr/local/bin/python3
""" Format strings representing qualifiers.
"""

import os
import sys

import Any

DEBUG = os.getenv('DEBUG_QUALIFIERS')


# Qualifier Handlers
# =================================================================================================

# format_maxperdisc()
# -------------------------------------------------------------------------------------------------
def format_maxperdisc(maxperdisc_dict: dict) -> str:
  """
  """
  limit = float(maxperdisc_dict['number'])
  class_credit = maxperdisc_dict['class_credit']
  disciplines = maxperdisc_dict['disciplines']
  discipline_str = ', '.join(disciplines)
  if len(disciplines) == 1:
    suffix = ''
    anyof = ''
  else:
    suffix = 's'
    anyof = ' any of '

  if class_credit == 'class':
    class_str = 'class' if limit == 1 else 'classes'
    return (f'No more than {int(limit)} {class_str} in {anyof}the following discipline{suffix}: '
            f'{discipline_str}')
  elif class_credit == 'credit':
    credit_str = 'credit' if limit == 1 else 'credits'
    return (f'No more than {limit:0.1f} {credit_str} in {anyof}the following discipline{suffix}: '
            f'{discipline_str}')

  return '<span class="error">Error: invalid MaxPerDisc</span>'


# format_minclass()
# -------------------------------------------------------------------------------------------------
def format_minclass(minclass_dict: dict) -> str:
  """
  """
  pprint(minclass_dict, stream=sys.stderr)
  try:
    number = int(minclass_dict['number'])
    if number < 1:
      raise ValueError('Minclass with minimum less than 1.')
    suffix = '' if number == 1 else 'es'
    rule_str = f'<p>At least {number} class{suffix} required.</p>'
    label_str, course_list = course_list_details(minclass_dict.pop('course_list'))
    return f'<details><summary>{label_str}</summary>{rule_str}{course_list}</dict>'
  except ValueError as ve:
    return f'<p class="error">Invalid MinClass {ve} {minclass_dict=}</>'
  except KeyError as ke:
    return f'<p class="error">Invalid MinClass {ke} {minclass_dict=}</>'


# format_maxpassfail()
# -------------------------------------------------------------------------------------------------
def format_maxpassfail(maxpassfail_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_maxpassfail({maxpassfail_info}', file=sys.stderr)

  number = float(maxpassfail_info['number'])
  class_credit = maxpassfail_info['class_credit']
  if class_credit == 'credit':
    if number == 0:
      return 'No credits may be taken pass/fail'
    suffix = '' if number == 1 else 's'
    return f'A maximum of {number:0.1f} credit{suffix} may be taken pass/fail'
  else:
    if number == 0:
      return 'No courses may be taken pass/fail'
    suffix = '' if number == 1 else 'es'
    return f'A maximum of {number:0} class{suffix} may be taken pass/fail'
  return f'maxpassfail: not implemented yet'


# format_maxperdisc()
# -------------------------------------------------------------------------------------------------
def format_maxperdisc(mpd_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** format_maxperdisc({mpd_dict=})', file=sys.stderr)
  class_credit = mpd_dict['class_credit'].lower()
  if class_credit == 'class':
    number = int(mpd_dict['number'])
    suffix = '' if number == 1 else 's'
  elif class_credit == 'credit':
    number = float(mpd_dict['number'])
    suffix = '' if number == 1.0 else 'es'
  else:
    number = float('NaN')
    suffix = 'x'
  disciplines = sorted(mpd_dict['disciplines'])
  return f'No more than {number} {class_credit}{suffix} in ({", ".join(disciplines)})'


# format_maxspread()
# -------------------------------------------------------------------------------------------------
def format_maxspread(maxspread_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** format_maxspread({maxspread_info})', file=sys.stderr)

  number = int(maxspread_info)

  return f'maxspread: not implemented yet {number=}'


# format_maxtransfer()
# -------------------------------------------------------------------------------------------------
def format_maxtransfer(transfer_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_maxtransfer({transfer_info}', file=sys.stderr)

  return f'maxtransfer: not implemented yet'


# format_minarea()
# -------------------------------------------------------------------------------------------------
def format_minarea(minarea_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_minarea({minarea_info}', file=sys.stderr)

  return f'minarea: not implemented yet'


# format_minclass()
# -------------------------------------------------------------------------------------------------
def format_minclass(mcl_dict: dict) -> str:
  """ dict_keys(['number', 'course_list'])
  """
  if DEBUG:
    print(f'*** format_minclass({mcl_dict=})', file=sys.stderr)
  number = int(mcl_dict['number'])
  suffix = '' if number == 1 else 'es'
  scribed_courses_list = mcl_dict['course_list']['scribed_courses']
  scribed_courses = []
  for scribed_course in scribed_courses_list:
    if scribed_course[2]:
      # There is a with clause
      scribed_courses.append(f'{scribed_course[0]} {scribed_course[1]} {scribed_course[2]}')
    else:
      scribed_courses.append(f'{scribed_course[0]} {scribed_course[1]}')
  scribed_courses_str = ', '.join(scribed_courses)

  return f'At least  {number} class{suffix} in ({scribed_courses_str})'


# format_mincredit()
# -------------------------------------------------------------------------------------------------
def format_mincredit(mincredit_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_mincredit({mincredit_info}', file=sys.stderr)

  number = float(mincredit_info.pop('number'))
  course_list = mincredit_info.pop('course_list')
  return f'mincredit: not implemented yet {number=} {course_list=}'


# format_mingpa()
# -------------------------------------------------------------------------------------------------
def format_mingpa(mgp_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** format_mingpa({mgp_dict=})', file=sys.stderr)
  number = float(mgp_dict['number'])
  return f'Minimum GPA of {number:0.1f} {mgp_dict.keys()=}'


# format_mingrade()
# -------------------------------------------------------------------------------------------------
def format_mingrade(min_grade: str) -> str:
  """
  """
  if DEBUG:
    print(f'*** format_mingrade({min_grade=})', file=sys.stderr)

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

  number = float(min_grade)
  if number < 1.0:
    number = 0.7
  # Lots of values greater than 4.0 have been used to mean "no upper limit."
  if number > 4.0:
    number = 4.0
  letter = letters[int(round(number * 3))]
  return f'Minimum grade of {letter} required'


# format_minperdisc()
# -------------------------------------------------------------------------------------------------
def format_minperdisc(minperdisc_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_minperdisc({minperdisc_info}', file=sys.stderr)

  return f'minperdisc: not implemented yet'


# format_minspread()
# -------------------------------------------------------------------------------------------------
def format_minspread(minspread_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_minspread({minspread_info}', file=sys.stderr)

  return f'minspread: not implemented yet'


# format_samedisc()
# -------------------------------------------------------------------------------------------------
def format_samedisc(samedisc_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'format_samedisc({samedisc_info}', file=sys.stderr)

  return f'samedisc: not implemented yet'


# dispatch()
# -------------------------------------------------------------------------------------------------
dispatch_table = {'maxpassfail': format_maxpassfail,
                  'maxperdisc': format_maxperdisc,
                  'maxspread': format_maxspread,
                  'maxtransfer': format_maxtransfer,
                  'minarea': format_minarea,
                  'minclass': format_minclass,
                  'mincredit': format_mincredit,
                  'mingpa': format_mingpa,
                  'mingrade': format_mingrade,
                  'minperdisc': format_minperdisc,
                  'minspread': format_minspread,
                  'samedisc': format_samedisc
                  }


# dispatch_qualifier()
# -------------------------------------------------------------------------------------------------
def dispatch_qualifier(qualifier: str, qualifier_info: Any) -> str:
  """ Dispatch a dict key:value pair, where the key is the name of a qualifier, use the matching
      format_xxx function to format the value into an English string.
  """
  if DEBUG:
    print(f'*** dispatch({qualifier}, {qualifier_info=})', file=sys.stderr)

  return dispatch_table[qualifier](qualifier_info)


# format_qualifiers()
# -------------------------------------------------------------------------------------------------
def format_qualifiers(node: dict) -> list:
  """ Given a dict that may or may not have keys for known qualifiers remove all qualifiers from the
      node, and return a list of formatted strings representing the qualifiers found.
  """
  # The following qualifieres are legal, but we ignore ones that we don’t need.
  possible_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                         'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                         'proxy_advice', 'rule_tag', 'samedisc', 'share']
  ignored_qualifiers = ['proxy_advice', 'rule_tag', 'share']
  handled_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                        'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                        'samedisc']
  qualifier_strings = []
  for qualifier in possible_qualifiers:
    if qualifier in node.keys():
      if qualifier in ignored_qualifiers:
        continue
      if qualifier in handled_qualifiers:
        qualifier_info = node.pop(qualifier)
        qualifier_strings.append(dispatch_qualifier(qualifier, qualifier_info))
      else:
        value = item.pop(qualifier)
        print(f'Error: unhandled qualifier: {qualifier}: {value}', file=sys.stderr)
        qualifier_strings.append(f'Error: unhandled qualifier: {qualifier}: {value}')
    return qualifier_strings
