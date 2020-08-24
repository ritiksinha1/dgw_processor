#! /usr/local/bin/python3
"""
maxpassfail     : MAXPASSFAIL NUMBER (CLASS | CREDIT) tag?;
maxperdisc      : MAXPERDISC NUMBER (CLASS | CREDIT) LP SYMBOL (list_or SYMBOL)* RP tag?;
maxspread       : MAXSPREAD NUMBER tag?;
maxtransfer     : MAXTRANSFER NUMBER (CLASS | CREDIT) (LP SYMBOL (list_or SYMBOL)* RP)? tag?;
minarea         : MINAREA NUMBER tag?;
minclass        : MINCLASS (NUMBER|RANGE) course_list tag? display* label?;
mincredit       : MINCREDIT (NUMBER|RANGE) course_list tag? display* label?;
mingpa          : MINGPA NUMBER (course_list | expression)? tag? display* label?;
mingrade        : MINGRADE NUMBER;
minspread       : MINSPREAD NUMBER tag?;
minperdisc      : MINPERDISC NUMBER (CLASS | CREDIT)  LP SYMBOL (list_or SYMBOL)* RP tag? display*;
ruletag         : RULE_TAG expression;
samedisc        : SAME_DISC expression tag?;
share           : (SHARE | DONT_SHARE) (NUMBER (CLASS | CREDIT))? expression? tag?;
"""


class CourseListQualifier:
  """ Structure for any of the qualifiers that may be attached to a course list. Room for anything
      that might be needed.
  """
  def __init__(keyword, number=None, min_value=None, max_value=None, class_credit=None,
               disciplines=None, course_list=None, expression=None, display=None, label=None):
    self.keyword = keyword.lower()
    self.number = number
    self.min_value = min_value
    self.max_value = max_value
    self.class_credit = class_credit
    self.disciplines = disciplines
    self.course_list = course_list
    self.expression = expression
    self.display = display
    self.label = label

