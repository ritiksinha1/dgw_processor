#! /usr/local/bin/python3
""" Parse a text file.
"""
import os
import sys
from dgw_parser import parse_block

# __main__
# =================================================================================================
if __name__ == '__main__':
  """ Use dummy institution and requirement_id; get text to parse from stdin
  """
  institution = 'TST01'
  requirement_id = 'RA000000'
  text_to_parse = ''.join(sys.stdin.readlines())
  parse_tree = parse_block(institution, requirement_id, '2000-2022U', '999999', text_to_parse)
  try:
    print(parse_tree['error'])
  except KeyError:
    print('OK')
