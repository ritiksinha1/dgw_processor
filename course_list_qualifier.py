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


#  _format_number()
# -------------------------------------------------------------------------------------------------
def _format_number(n, class_credit) -> str:
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


#  _format_range()
# -------------------------------------------------------------------------------------------------
def _format_range(min_value, max_value):
  """
  """
  pass


# _andor_list()
# -------------------------------------------------------------------------------------------------
def _andor_list(items, conjunction='or'):
  """ Oxford commaizification of a list.
  """
  assert isinstance(items, list)
  assert conjunction.lower() in ['and', 'or']

  if len(items) == 0:
    return ''
  if len(items) == 1:
    return f'{items[0]}'
  if len(items) == 2:
    return f'{items[0]} {conjunction} {items[1]}'
  return ', '.join([str(item) for item in items[0:-1]]) + f', {conjunction} {items[-1]}'


# class CourseListQualifier
# -------------------------------------------------------------------------------------------------
class CourseListQualifier(object):
  """ Structure for any of the qualifiers that may be attached to a course list. Room for anything
      that might be needed.
  """
  valid_qualifiers = ['maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer', 'minarea',
                      'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc', 'minspread',
                      'ruletag', 'samedisc', 'share']

  def __init__(self, keyword, number=None, range=None, class_credit=None,
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
    if range is not None:
      self.min_value, self.max_value = range.split(':')
    self.class_credit = class_credit
    self.disciplines = disciplines
    self.course_list = course_list
    self.expression = expression
    self.display = display
    self.label = label

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

    # ---------------------------------------------------------------------------------------------
    """ The textual representation depends on the keyword. Strings are sentences, but not terminated
        so they can be joined (with '; ') as independent clauses . But that means the terminal mark
        has to be added by the application.
    """

    # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
    if self.keyword == 'maxpassfail':
      number = _format_number(self.number, self.class_credit)
      return f'No more than {number} Pass/Fail {self.class_credit}{suffix}'

    # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
    if self.keyword == 'maxperdisc':
      disciplines = ', '.join([str(d) for d in self.disciplines])
      number = _format_number(self.number, self.class_credit)
      suffix = '' if number == '1' else 's'
      suffix = 'es' if self.class_credit == 'class' and suffix == 's' else suffix
      return (f'A maximum of {number} {self.class_credit}{suffix} in '
              f'{_andor_list(self.disciplines, "or")}')

    # maxspread       : MAXSPREAD NUMBER
    if self.keyword == 'maxspread':
      if self.number == 1:
        return f'All courses must be taken in the same discipline'
      return f'Courses must be taken from no more than {self.number} disciplines'

    # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
    if self.keyword == 'maxtransfer':
      number = _format_number(self.number, self.class_credit)
      if number == '0':
        return f'No transfer {self.class_credit}{suffix} may be used.'
      return f'No more than {number} transfer {self.class_credit}{suffix} may be used'

    # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
    if self.keyword == 'minperdisc':
      disciplines = ', '.join([str(d) for d in self.disciplines])
      number = _format_number(self.number, self.class_credit)
      return f'At least {number} {self.class_credit}{suffix} in {disciplines}'

    # minarea         : MINAREA NUMBER
    if self.keyword == 'minarea':
      suffix = '' if self.number == 1 else 's'
      return f'Courses must come from at least {self.number} area{suffix}'

    # mingrade        : MINGRADE NUMBER
    if self.keyword == 'mingrade':
      return f'Minimum grade of {self.number:0.1f} required'

    # minspread       : MINSPREAD NUMBER
    if self.keyword == 'minspread':
      return f'Courses must come from at least {self.number} disciplines'

    # minclass        : MINCLASS (NUMBER|RANGE) course_list
    if self.keyword == 'minclass':
      print('*** minclass:', self.__dict__, file=sys.stderr)
      return 'minclass'

    # mincredit       : MINCREDIT (NUMBER|RANGE) course_list
    if self.keyword == 'mincredit':
      print('*** mincredit:', self.__dict__, file=sys.stderr)
      return 'mincredit'

    # mingpa          : MINGPA NUMBER (course_list | expression)?
    if self.keyword == 'mingpa':
      if self.course_list is not None or self.expression is not None:
        print('*** mingpa with course_list or expression:', self.__dict__, file=sys.stderr)
      return f'Minimum GPA of {self.number:0.1f} required'

    # ruletag         : RULE_TAG expression;
    if self.keyword == 'ruletag':
      return f'(Format audit using "{self.expression}")'

    # samedisc        : SAME_DISC expression
    if self.keyword == 'samedisc':
      return f'The following discipline(s) are equivalent: "{self.expression}"'

    # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
    if self.keyword == 'share':
      print('*** share:', self.__dict__, file=sys.stderr)
      return 'share'

    raise ValueError(f'{self.keyword} not recognized')
