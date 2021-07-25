#! /usr/local/bin/python3
""" Format qualifier info into a string
"""

import os
import sys

import Any

DEBUG = os.getenv('DEBUG_QULIFIERS')


# Qualifier Handlers
# =================================================================================================

# process_maxpassfail()
# -------------------------------------------------------------------------------------------------
def process_maxpassfail(maxpassfail_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_maxpassfail({maxpassfail_info}', file=sys.stderr)

  return f'maxpassfail: not implemented yet'


# process_maxperdisc()
# -------------------------------------------------------------------------------------------------
def process_maxperdisc(mpd_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** process_maxperdisc({mpd_dict=}, {calling_context=})', file=sys.stderr)
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


# process_maxspread()
# -------------------------------------------------------------------------------------------------
def process_maxspread(maxspread_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_maxspread({maxspread_info}', file=sys.stderr)

  return f'maxspread: not implemented yet'


# process_maxtransfer()
# -------------------------------------------------------------------------------------------------
def process_maxtransfer(transfer_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_maxtransfer({transfer_info}', file=sys.stderr)

  return f'maxtransfer: not implemented yet'


# process_minarea()
# -------------------------------------------------------------------------------------------------
def process_minarea(minarea_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_minarea({minarea_info}', file=sys.stderr)

  return f'minarea: not implemented yet'


# process_minclass()
# -------------------------------------------------------------------------------------------------
def process_minclass(mcl_dict: dict) -> str:
  """ dict_keys(['number', 'course_list'])
  """
  if DEBUG:
    print(f'*** process_minclass({mcl_dict=}, {calling_context=})', file=sys.stderr)
  local_context = calling_context + []
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


# process_mincredit()
# -------------------------------------------------------------------------------------------------
def process_mincredit(mincredit_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_mincredit({mincredit_info}', file=sys.stderr)

  print(mincredit_info.keys())
  return f'mincredit: not implemented yet'


# process_mingpa()
# -------------------------------------------------------------------------------------------------
def process_mingpa(mgp_dict: dict) -> str:
  """
  """
  if DEBUG:
    print(f'*** process_mingpa({mgp_dict=}, {calling_context=})', file=sys.stderr)
  local_context = calling_context + []
  number = float(mgp_dict['number'])
  return f'Minimum GPA of {number:0.1f} {mgp_dict.keys()=}'


# process_mingrade()
# -------------------------------------------------------------------------------------------------
def process_mingrade(min_grade: str) -> str:
  """
  """
  if DEBUG:
    print(f'*** process_mingrade({min_grade=}, {calling_context=})', file=sys.stderr)
  local_context = calling_context + []

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


# process_minperdisc()
# -------------------------------------------------------------------------------------------------
def process_minperdisc(minperdisc_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_minperdisc({minperdisc_info}', file=sys.stderr)

  return f'minperdisc: not implemented yet'


# process_minspread()
# -------------------------------------------------------------------------------------------------
def process_minspread(minspread_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_minspread({minspread_info}', file=sys.stderr)

  return f'minspread: not implemented yet'


# process_samedisc()
# -------------------------------------------------------------------------------------------------
def process_samedisc(samedisc_info: dict) -> str:
  """
  """
  if DEBUG:
    print(f'process_samedisc({samedisc_info}', file=sys.stderr)

  return f'samedisc: not implemented yet'


# dispatch()
# -------------------------------------------------------------------------------------------------
dispatch_table = {'maxpassfail': process_maxpassfail,
                  'maxperdisc': process_maxperdisc,
                  'maxspread': process_maxspread,
                  'maxtransfer': process_maxtransfer,
                  'minarea': process_minarea,
                  'minclass': process_minclass,
                  'mincredit': process_mincredit,
                  'mingpa': process_mingpa,
                  'mingrade': process_mingrade,
                  'minperdisc': process_minperdisc,
                  'minspread': process_minspread,
                  'samedisc': process_samedisc
                  }


def dispatch(qualifier: str, qualifier_info: Any) -> str:
  """
  """
  if DEBUG:
    print(f'*** dispatch({qualifier}, {qualifier_info=}', file=sys.stderr)

  return dispatch_table[qualifier](qualifier_info)
