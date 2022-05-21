#! /usr/local/bin/python3
""" What are the overlap patterns between course limits in the header and course requirements in the
    body?
"""

import csv
import os
import sys
import psycopg
from psycopg.rows import namedtuple_row

if __name__ == '__main__':

  with open('./analysis.txt') as infile:
    for line in infile.readlines():
      ident, course_dict = line.split(';')
      institution, requirement_id, block_type, limit_type, number = ident.split()
      course_dict = eval(course_dict)
      print(list(course_dict.keys()))