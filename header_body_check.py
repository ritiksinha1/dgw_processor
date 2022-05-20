#! /usr/local/bin/python3
""" What are the overlap patterns between course limits in the header and course requirements in the
    body?
"""

import os
import sys
import psycopg
from psycopg.rows import namedtuple_row

if __name__ == '__main__':
  with open('./analysis.txt') as infile:
    for line in infile.readlines():
      institution, requirement_id, block_type, limit_type = line[0:31].split()
      number, scribe_list, include_list, exclude_list = line[31:].split(';')
      print(number, scribe_list.strip(), include_list.strip(), exclude_list.strip())
