#! /usr/local/bin/python3
""" This is a development module for recognizing course lists
    MaxTerm and MaxTransfer have to be added to credits processor
"""
from parsers import tokenize, error_report

lines = ['MaxCredits 0 in @ 499, 4991, 4992, 4993, 4994, 4995, 4996, 4997, 4998, 4999',
         'MaxCredits 3 in CSCI 390:399',
         'MaxClass 1 in MATH 223, 224, 232, 245, 247, 248, 317, 337, 609, 613,',
         '619, 621, 623, 624, 625, 626, 633, 634, 635, 636,',
         'PHYS 225, 227, 312']

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

expect_course_list = [in_token, from_token]
expect_num = [int_type, float_type]

parse_tree = dict()
saved_tokens = []
expect = None

for token in tokenize(lines, dict(), 'qns'):
  if expect is not None:
    if token.type in expect:
      pass
    else:
      error_report(f'Expected {expect} got {token}')

  else:
    if token in minmax_tokens:
      saved_tokens = [token]
      expect = expect_num

