#! /usr/local/bin/python3
""" This is a development module for recognizing course lists
    MaxTerm and MaxTransfer have to be added to credits processor
"""

import psycopg2
from psycopg2.extras import NamedTupleCursor
from enum import Enum, auto

from parsers import tokenize, error_report

test_1 = ['@ 499, 4991, 4992, 4993, 4994, 4995, 4996, 4997, 4998, 4999']
test_2 = ['CSCI 390:399']
test_3 = ['MATH 223, 224, 232, 245, 247, 248, 317, 337, 609, 613,',
          '619, 621, 623, 624, 625, 626, 633, 634, 635, 636,',
          'PHYS 225, 227, 312']
test_4 = ['@ (With DWAge>10 and DWDiscipline   <>ANTH),'
          '@ (With DWAge>10 and DWCourseNumber <>145)']

maxcredits_token = ('reserved', 'maxcredits')
maxclasses_token = ('reserved', 'maxclasses')
maxpassfail_token = ('reserved', 'maxpassfail')
minmax_tokens = [maxcredits_token, maxclasses_token, maxpassfail_token]
and_token = ('punctuation', '_AND_')
in_token = ('reserved', 'in')
from_token = ('reserved', 'from')
or_token = ('punctuation', '_OR_')
lp_token = ('punctuation', '_LPAREN_')
rp_token = ('punctuation', '_RPAREN_')
int_type = 'int_value'
float_type = 'float_value'

expect_num = [int_type, float_type]

conn = psycopg2.connect('dbname=cuny_courses')
cursor = conn.cursor(cursor_factor=NameTupleCursor)


class CourseList():
  """ A list of courses. Each one has the course_id, offer_nbr, discipline, catalog number from
      cuny_courses.
  """
  def __init__(str: institution):
    self.institution = institution


class ParseState(Enum):
  """ First, look for a discipline, then look for a catalog number, then look for either, but
      each discipline has to be followed by at least one catalog number.
  """
  S_0 = auto()
  S_1 = auto()
  S_2 = auto()
  S_3 = auto()
  S_4 = auto()
  def next_state(state):
    yield ParseState.__members__.items().keys().index(state) + 1


for test in (test_1, test_2, test_3, test_4):
  for token in tokenize(test, dict(), 'qns'):
