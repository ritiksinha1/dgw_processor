#! /usr/local/bin/python3
"""
NOT USED: Historical Artifact

maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
maxspread       : MAXSPREAD NUMBER                                      # not a group_list_qualifier
maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
minarea         : MINAREA NUMBER                                        # not a group_list_qualifier
minclass        : MINCLASS (NUMBER|RANGE) course_list tag? display* label?
mincredit       : MINCREDIT (NUMBER|RANGE) course_list tag? display* label?
mingpa          : MINGPA NUMBER (course_list | expression)? display* label?
mingrade        : MINGRADE NUMBER   // Real, 1 decimal place.
minspread       : MINSPREAD NUMBER  // Int                              # not a group_list_qualifier
minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP display*;
ruletag         : RULE_TAG expression
samedisc        : SAME_DISC expression
share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
"""

import sys


# _andor_list()
# -------------------------------------------------------------------------------------------------
def _andor_list(items, conjunction='or'):
  """ Oxford commaizification of a list.
  """
  assert isinstance(items, list), f'{items} is not a list'
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
  valid_qualifiers = ['dont_share', 'maxpassfail', 'maxperdisc', 'maxspread', 'maxtransfer',
                      'minarea', 'minclass', 'mincredit', 'mingpa', 'mingrade', 'minperdisc',
                      'minspread', 'ruletag', 'samedisc', 'share']

  def __init__(self, keyword, number=None, range=None, class_credit=None,
               disciplines=None, course_list=None, expression=None, display=None, label=None):
    """ Constructor args come from analysis of a course_list item's context, done as the parse tree
        is walked. The walker in dgw_processor provides listener methods, which invoke
        dgw_utils.get_course_list_qualifiers()
    """
    self.keyword = keyword.lower()
    if self.keyword not in CourseListQualifier.valid_qualifiers:
      raise ValueError(f'"{keyword}" is not a recognized qualifier type.')

    # Number handling: Assume values are floats, but if the fraction part is zero, treat as int for
    # display purposes (_str for display strings). This heuristic gets overridden for cases where
    # the value really should display as a float, like GPA requirements.
    self.number = number
    if number is not None:
      self.number = float(number)
      self.number_str = f'{self.number:0.1f}'
      if self.number == int(self.number):
        self.number = int(self.number)
        self.number_str = f'self.number'
    if range is None:
      self.min_value, self.max_value = None, None
    else:
      self.min_value, self.max_value = [float(val) for val in range.split(':')]
      # For a range, either both are ints or both are floats, and display as such
      if self.min_value == int(self.min_value) and self.max_value == int(self.max_value):
        self.min_value = int(self.min_value)
        self.max_value = int(self.max_value)
        self.min_value_str = f'{self.min_value}'
        self.max_value_str = f'{self.max_value}'
      else:
        self.min_value_str = f'{self.min_value:0.1f}'
        self.max_value_str = f'{self.max_value:0.1f}'

    self.class_credit = class_credit
    self.disciplines = disciplines
    self.course_list = course_list
    self.expression = expression
    self.display = display
    self.label = label

    # Replace course list tuples with discipline-catalog_number strings
    if self.course_list:
      self.course_list = [f'{c[0]} {c[1]}' for c in self.course_list]

    self.text = self.__str__()

  def __str__(self) -> str:
    """ Printable description.
    """

    # Class/Credit suffix
    self.suffix = 's'
    if self.keyword == 'minclass' or (self.class_credit and self.class_credit == 'class'):
      self.suffix = 'es'
    if self.number and self.number == 1:
      self.suffix = ''

    # ---------------------------------------------------------------------------------------------
    """ The textual representation depends on the keyword. Strings are sentences but not terminated,
        so they can be joined (with '; ') as independent clauses . But that means the terminal mark
        has to be added by the application.
    """

    # maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT)
    if self.keyword == 'maxpassfail':
      return f'No more than {self.number_str} Pass/Fail {self.class_credit}{self.suffix}'

    # maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP
    if self.keyword == 'maxperdisc':
      disciplines = ', '.join([str(d) for d in self.disciplines])
      return (f'A maximum of {self.number_str} {self.class_credit}{self.suffix} in '
              f'{_andor_list(self.disciplines, "or")}')

    # maxspread       : MAXSPREAD NUMBER
    if self.keyword == 'maxspread':
      if self.number == 1:
        return f'All courses must be taken in the same discipline'
      return f'Courses must be taken from no more than {self.number_str} disciplines'

    # maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)?
    if self.keyword == 'maxtransfer':
      if self.number == 0:
        return f'No transfer {self.class_credit}{self.suffix} may be used'
      return f'No more than {self.number_str} transfer {self.class_credit}{self.suffix} may be used'

    # minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP
    if self.keyword == 'minperdisc':
      disciplines = ', '.join([str(d) for d in self.disciplines])
      return f'At least {self.number_str} {self.class_credit}{self.suffix} in {disciplines}'

    # minarea         : MINAREA NUMBER
    if self.keyword == 'minarea':
      return f'Courses must come from at least {self.number_str} area{self.suffix}'

    # mingrade        : MINGRADE NUMBER
    if self.keyword == 'mingrade':
      # Here we force grade to have a decimal place
      return f'Minimum grade of {self.number:0.1f} required'

    # minspread       : MINSPREAD NUMBER
    if self.keyword == 'minspread':
      return f'Courses must come from at least {self.number_str} disciplines'

    # minclass        : MINCLASS (NUMBER|RANGE) course_list
    if self.keyword == 'minclass':
      if self.number:
        return (f' At least {self.number} class{self.suffix} from '
                f'{_andor_list(self.course_list, "or")}')
      return (f'Between {self.min_value_str} and {self.max_value_str} class{self.suffix} from '
              f'{_andor_list(self.course_list, "or")}')

    # mincredit       : MINCREDIT (NUMBER|RANGE) course_list
    if self.keyword == 'mincredit':
      if self.number:
        return (f' At least {self.number} credit{self.suffix} from '
                f'{_andor_list(self.course_list, "or")}')
      return (f'Between {self.min_value_str} and {self.max_value_str} credit{self.suffix} from '
              f'{_andor_list(self.course_list, "or")}')

    # mingpa          : MINGPA NUMBER (course_list | expression)?
    if self.keyword == 'mingpa':
      if self.course_list:
        return f'GPA must be {self.number:0.1f} or above in {_andor_list(self.course_list, "and")}'
      return f'Minimum GPA of {self.number:0.1f} required when {self.expression}'

    # ruletag         : RULE_TAG expression;
    if self.keyword == 'ruletag':
      return f'(Format audit using "{self.expression}")'

    # samedisc        : SAME_DISC expression
    if self.keyword == 'samedisc':
      return f'The following discipline(s) are equivalent: "{self.expression}"'

    # share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression?
    if self.keyword == 'share' or self.keyword == 'dont_share':
      negation = '' if self.keyword == 'share' else 'not '
      scope = 'other courses'
      if self.number:
        scope = f'up to {self.number_str} other {self.class_credit}{self.suffix}'
      if self.expression:
        scope = self.expression.strip(')(')
      return (f'May {negation}overlap with other courses in {scope}')

    raise ValueError(f'{self.keyword} not recognized')
