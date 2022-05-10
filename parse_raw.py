#! /usr/local/bin/python3
""" Parse a text file.
"""
import os
import sys
import argparse
import json
from dgw_parser import parse_block

# __main__
# =================================================================================================
if __name__ == '__main__':
  """ Use dummy institution and requirement_id; get text to parse from stdin
  """
  # Command line args
  parser = argparse.ArgumentParser(description='Parse DGW Scribe Blocks')
  parser.add_argument('-j', '--json', action='store_true')
  args = parser.parse_args()

  institution = 'TST01'
  requirement_id = 'RA000000'
  text_to_parse = ''.join(sys.stdin.readlines())
  parse_tree = parse_block(institution, requirement_id, '2000-2022U', '999999', text_to_parse)
  if args.json:
    with open('extracts/TST01_RA000000.json', 'w') as json_file:
      print(json.dumps(parse_tree, indent=2, sort_keys=True), file=json_file)
  try:
    print(parse_tree['error'])
  except KeyError:
    print('OK')
