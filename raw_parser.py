#! /usr/local/bin/python3
""" Augmented parse tree from text file. Use for debugging.
"""
import os
import sys
import argparse

from contextlib import contextmanager
from collections import namedtuple
from pprint import pprint

from ReqBlockLexer import ReqBlockLexer
from ReqBlockParser import ReqBlockParser
from ReqBlockVisitor import ReqBlockVisitor

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

from quarantine_manager import QuarantineManager
from dgw_filter import dgw_filter
from dgw_handlers import dispatch
from catalogyears import catalog_years

DEBUG = os.getenv('DEBUG_RAW_PARSER')

sys.setrecursionlimit(10**6)

quarantined_dict = QuarantineManager()


# raw_parser()
# =================================================================================================
def raw_parser(requirement_text: str) -> dict:
  """ For each matching Scribe Block, parse the block and generate lists of JSON objects from it.

       The period_range argument can be 'all', 'current', or 'latest', with the latter two being
       picked out of the result set for 'all'. If there is more than one block in the selected
       range, all will be updated in the db, but only the oldest one’s header and body lists will be
       returned.
  """
  augmented_tree = {'header_list': [], 'body_list': []}

  text_to_parse = dgw_filter(requirement_text)
  # Generate the parse tree from the Antlr4 parser generator.
  input_stream = InputStream(text_to_parse)
  lexer = ReqBlockLexer(input_stream)
  token_stream = CommonTokenStream(lexer)
  parser = ReqBlockParser(token_stream)
  # parser.removeErrorListeners()
  # parser.addErrorListener(DGW_ErrorListener())
  parse_tree = parser.req_block()

  # Walk the header and body parts of the parse tree, interpreting the parts to be saved.
  header_list = []

  head_ctx = parse_tree.header()
  if head_ctx:
    for child in head_ctx.getChildren():
      obj = dispatch(child, institution, 'RA000000')
      if obj != {}:
        header_list.append(obj)

  body_list = []
  body_ctx = parse_tree.body()
  if body_ctx:
    for child in body_ctx.getChildren():
      obj = dispatch(child, institution, 'RA000000')
      if obj != {}:
        body_list.append(obj)

  augmented_tree['header_list'] = header_list
  augmented_tree['body_list'] = body_list

  return augmented_tree


# __main__
# =================================================================================================
# Select Scribe Blocks for parsing
if __name__ == '__main__':
  """ You can select blocks by institutions, block_types, block_values, and period from here.
      By default, the requirement_blocks table's head_objects and body_objects fields are updated
      for each block parsed.
  """
  # Command line args
  parser = argparse.ArgumentParser(description='Raw DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institution', default='QNS01')
  parser.add_argument('scribe_block_file')
  # Parse args
  args = parser.parse_args()
  institution = args.institution[0:2].upper() + '01'
  with open(args.scribe_block_file) as scribe_text:
    requirement_text = scribe_text.read()
  pprint(raw_parser(requirement_text))
