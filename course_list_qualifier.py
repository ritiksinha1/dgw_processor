#! /usr/local/bin/python3
"""
maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
maxspread       : MAXSPREAD NUMBER
maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
minarea         : MINAREA NUMBER
minclass        : MINCLASS (NUMBER|RANGE) course_list tag? display* label?
mincredit       : MINCREDIT (NUMBER|RANGE) course_list tag? display* label?
mingpa          : MINGPA NUMBER (course_list | expression)? display* label?
mingrade        : MINGRADE NUMBER   // Real, 1 decimal place.
minspread       : MINSPREAD NUMBER  // Int
minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP display*;
ruletag         : RULE_TAG expression
samedisc        : SAME_DISC expression
share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
"""

import sys


# _fix_number()
# -------------------------------------------------------------------------------------------------
def _fix_number(n, class_credit) -> str:
  """ Format int or float string, as appropriate.
      Number of classes has to be an int, but number of credits can be a float, which gets displayed
      as an int if the fraction part is 0.
  """
  if class_credit == 'class':
    number = f'{int(n)}'
  else:
    number = float(n)
    if int(number) == number:
      number = f'{int(number)}'
    else:
      number = f'{number:.1}'
  return number


# class CourseListQualifier
# -------------------------------------------------------------------------------------------------
class CourseListQualifier(object):
  """ Structure for any of the qualifiers that may be attached to a course list. Room for anything
      that might be needed.
  """
  valid_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                      'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                      'ruletag', 'samedisc', 'share']

  def __init__(self, keyword, number=None, min_value=None, max_value=None, class_credit=None,
               disciplines=None, course_list=None, expression=None, display=None, label=None):
    """ Constructor args come from analysis of a course_list item's context, done as the parse tree
        is walked. The walker in dgw_processor provides listener methods, which invoke
        dgw_utils.get_course_list_qualifiers()
    """
    self.keyword = keyword.lower()
    if self.keyword not in CourseListQualifier.valid_qualifiers:
      raise ValueError(f'"{keyword}" is not a recognized qualifier type.')
    self.number = number
    if number is not None:
      self.number = float(number)
      if self.number == int(self.number):
        self.number = int(self.number)
    self.min_value = min_value
    self.max_value = max_value
    self.class_credit = class_credit
    self.disciplines = disciplines
    self.course_list = course_list
    self.expression = expression
    self.display = display
    self.label = label
    if self.min_value and self.max_value and self.min_value == self.max_value:
      self.number = self.min_value
      self.min_value = None
      self.max_value = None
    self.text = self.__str__()

  def __str__(self) -> str:
    """ Printable description.
    """
    # Class/Credit suffix
    suffix = 's'
    if self.class_credit and self.class_credit == 'class':
      suffix = 'es'
    if self.number and self.number == 1:
      suffix = ''

    # The textual representation depends on the keyword
    # ---------------------------------------------------------------------------------------------

    # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
    if self.keyword == 'maxpassfail':
      number = _fix_number(self.number, self.class_credit)
      return f'No more than {number} Pass/Fail {self.class_credit}{suffix}.'

    # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
    if self.keyword == 'maxperdisc':
      number = _fix_number(self.number, self.class_credit)
      disciplines = ', '.join([str(d) for d in self.disciplines])
      return f'No more than {number} {self.class_credit}{suffix} in {disciplines}.'

    if self.keyword == 'maxspread':
      number = int(self.number)
      if number == 1:
        return f'All courses must be taken in the same discipline.'
      return f'Courses must be taken from no more than {self.number} disciplines.'

    # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
    if self.keyword == 'maxtransfer':
      number = _fix_number(self.number, self.class_credit)
      if number == 0:
        return f'No transfer {self.class_credit}{suffix} may be used.'
      return f'No more than {self.number} transfer {self.class_credit}{suffix} may be used.'

    # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
    # maxspread       : MAXSPREAD NUMBER
    # minarea         : MINAREA NUMBER
    # mingrade        : MINGRADE NUMBER
    # minspread       : MINSPREAD NUMBER
    # minclass        : MINCLASS (NUMBER|RANGE) course_list
    # mincredit       : MINCREDIT (NUMBER|RANGE) course_list
    # mingpa          : MINGPA NUMBER (course_list | expression)?
    # ruletag         : RULE_TAG expression;
    # samedisc        : SAME_DISC expression
    # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?

    return self.keyword
