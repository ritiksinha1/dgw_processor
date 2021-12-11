#! /usr/local/bin/python3
""" Cache manager for scribed course lookups.
"""

import os
import sys
import json

import psycopg
from psycopg.rows import namedtuple_row

from argparse import ArgumentParser
from collections import namedtuple

from pgconnection import PgConnection

DEBUG = os.getenv('DEBUG_LOOKUP')

CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr discipline catalog_nbr title')


# traverse_dict()
# -------------------------------------------------------------------------------------------------
def traverse_dict(node: dict, target_key: str, return_list: list):
  """ Traverse a dict, accumulating a list of nodes found. You have to start with a dict, but nodes
      can be any type.
  """
  if isinstance(node, dict):
    for key, value in node.items():
      if key == target_key:
        return_list.append({key: value})
      traverse_dict(value, target_key, return_list)
  elif isinstance(node, list):
    for item in node:
      if isinstance(item, dict):
        traverse_dict(item, target_key, return_list)

  return return_list


# get_course_lists()
# -------------------------------------------------------------------------------------------------
def get_course_lists(parse_tree: dict) -> list:
  """ Traverse a oarse tree, and return a list of course_list dicts found.
  """
  return_list = []
  traverse_dict(parse_tree, 'course_list', return_list)

  return return_list


# interpret_course_tuple()
# -------------------------------------------------------------------------------------------------
def interpret_course_tuple(institution: str,
                           scribe_tuple: tuple,
                           except_list: list,
                           key: str) -> dict:
  """
  """
  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      # If there is an except_list, that has to be expanded to a list of matching course_ids Except
      # tuples can have _with_ clauses: log them for later analysis. For now, all courses in the
      # list will be excluded from the returned dict.
      except_courses = []
      for except_tuple in except_list:
        discipline = except_tuple[0].replace('@', '.*')
        catalog_number = except_tuple[1].replace('@', '.*')
        if except_tuple[2]:
          print(f'With clause in except tuple: {except_tuple[2]}')
        cursor.execute("""
        select course_id, offer_nbr
        from cuny_courses
        where institution = %s
          and discipline ~* %s
          and catalog_number ~* %s
          and course_status = 'A'
        """, (institution, discipline, catalog_number))
        for row in cursor:
          except_courses.append((row.course_id, row.offer_nbr))

      if except_courses:
        except_clause = f'and (course_id, offer_nbr not in ({str(except_courses)[1:-1]})'
      else:
        except_clause = ''

      # Handle wildcards
      # ----------------

      # @ @: Empty course_list, alt_text describes the situation

      # Allow embedded wildcard(s) in discipline
      discipline = scribe_tuple[0].replace('@', '.*')

      # Catalog numbers are text, but there are numeric special cases:  \d+@ for levels;
      #                                                                  \d+:\d+
      #                                                                  and range of levels
      # DISCP @
      # DISCP \d+@
      # DISCP
      # Ranges have to be numeric
      # DISCP \d+:\d+
      # DISCP \d+@:\d+@
      return_dict = {'num_courses': 0,
                     'num_bkcr': 0,
                     'num_wric': 0,
                     'course_tuples': [],
                     'alt_text': ''}

  return return_dict


# lookup()
# -------------------------------------------------------------------------------------------------
def lookup(institution: str, scribed_tuple: tuple, except_list: list) -> dict:
  """
  """
  if DEBUG:
    print(f'lookup({institution=}, {scribed_tuple=}, {except_list=})')

  key = f'{institution.lower()[0:3]} {scribed_tuple[0]} {scribed_tuple[1]} {sorted(except_list)}'
  conn = PgConnection()
  cursor = conn.cursor()
  cursor.execute("""
  select dict
    from scribe_lookups
   where key = %s
  """, (key,))
  if cursor.rowcount == 0:
    return_dict = interpret_course_tuple(institution, scribed_tuple, except_list, key)
  else:
    assert cursor.rowcount == 1, (f'{cursor.rowcount} cache values for {key}')
    return_dict = cursor.fetchone().dict

  conn.close()
  return return_dict


if __name__ == '__main__':

 # Command line args
  parser = ArgumentParser(description='Look up courses referenced in Scribe Blocks')
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-np', '--progress', action='store_false')
  parser.add_argument('-ra', '--requirement_id', default=None)
  parser.add_argument('-ti', '--timelimit', type=int, default=30)
  parser.add_argument('--update_db', dest='update_db', action='store_true')
  parser.add_argument('--no_update_db', dest='update_db', action='store_false')
  parser.set_defaults(update_db=True)

  # Parse args
  args = parser.parse_args()

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as cursor:
      if args.institutions[0].lower == 'all':
        cursor.execute('select code from cuny_institutions')
        institutions = [row.code for row in cursor]
      else:
        institutions = [f"{i.strip('01').upper()}01" for i in args.institutions]
      for institution in institutions:
        if args.requirement_id is not None:
          requirement_id = f"RA{int(args.requirement_id.strip('RAra')):06}"
          print(institution, requirement_id, end='')
          cursor.execute("""
          select parse_tree from requirement_blocks
           where institution = %s
             and requirement_id = %s
          """, (institution, requirement_id))
          if cursor.rowcount == 0:
            print(' Not found.')
          else:
            parse_tree = cursor.fetchone().parse_tree
            if not parse_tree:
              print(' Empty parse tree.')
            else:
              course_lists = get_course_lists(parse_tree)
              suffix = '' if len(course_lists) == 1 else 's'
              print(f' Got {len(course_lists)} course_list{suffix}.')
              for course_list in course_lists:
                for scribed_tuples in course_list['course_list']['scribed_courses']:
                  for area in range(len(scribed_tuples)):
                    print(lookup(institution,
                                 tuple(scribed_tuples[area]),  # jsonb cpnverted them to lists
                                 course_list['course_list']['except_courses']))
        else:
          print('please stand by')
