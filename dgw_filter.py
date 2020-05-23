#! /usr/local/bin/python3
""" Function to filter out cruft at the end of requirement blocks.
    Can be used from the command line as a filter.
"""

import re
import sys


# filter()
# -------------------------------------------------------------------------------------------------
def filter(src, remove_comments=False):
  """ Remove all text following "END." as well as {hide } from src.
  """
  return_str = re.sub(r'[Ee][Nn][Dd]\.(.|\n)*', 'END.\n', src)
  return_str = re.sub(r'[Hh][Ii][Dd][Ee]-?(([Ff][Rr][Oo][Mm]-?[Aa][Dd][Vv][Ii][Cc][Ee])|'
                      r'([Rr][Uu][Ll][Ee]))?',
                      '', return_str.replace('{', '').replace('}', ''))

  if remove_comments:
    return_str = re.sub(f'#.*\n', '', return_str)

  return return_str


if __name__ == "__main__":
  print(filter(sys.stdin.read()))
