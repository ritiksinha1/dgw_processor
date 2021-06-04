#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?
"""

from argparse import ArgumentParser
from collections import namedtuple
from pgconnection import PgConnection
from dgw_interpreter import dgw_interpreter

from pprint import pprint

Course = namedtuple('Course',
                    'course_id offer_nbr discipline catalog_number title credits restriction')


# search_for_courses()
# -------------------------------------------------------------------------------------------------
def search_for(where: any, current_path: list, found_list: list) -> None:
  """ Depth-first recursive search of nested lists/dicts for course_list keys.
      For each course_list, tell how many are required, and list the active ones found.
  """
  global depth
  # print(f'{depth}enter', ':'.join(current_path), found_list)
  depth += '..'
  if isinstance(where, list):
    # print(f'{depth}is list with {len(where)} elements')
    for index in range(len(where)):
      if isinstance(where[index], dict):
        # current_path.append(f'{index}')
        search_for(where[index], current_path, found_list)
        # current_path.pop()
  elif isinstance(where, dict):
    # print(f'{depth}is dict with {len(where)} entries')
    for key, value in where.items():
      # print(f'{depth}{key} {isinstance(value, dict)}')
      if key == 'course_list':
        # Bingo!
        # Now to extract the number of classes and/or credits required and:
        #   for each active course: its course_id:offer_nbr, discipline-catalog_number, title, and
        #                           min credits
        #   for each missing course: its discipline-catalog_number
        requirement_str = []
        # Suffix handling: value might be missing, float or int, unity, or a range.
        if (num_classes := where['num_classes']) is not None:
          try:
            suffix = '' if float(num_classes) == 1 else 'es'
          except ValueError as ve:
            suffix = 'es'
          requirement_str.append(f'{num_classes} class{suffix}')
        if (num_credits := where['num_credits']) is not None:
          try:
            suffix = '' if float(num_credits) == 1 else 's'
          except ValueError as ve:
            suffix = 's'
          requirement_str.append(f'{num_credits} credit{suffix}')
        if 'label' in value.keys() and (label := value['label']) is not None:
          label = value['label']
          in_clause = f' in {label}'
        else:
          label = ''
          in_clause = ''
        requirement_str = ' or '.join(requirement_str) + in_clause
        # Active courses
        active_courses = [Course._make(c) for c in value['active_courses']]
        # Missing courses
        missing_courses = [f'{c[0]} {c[1]}' for c in value['missing_courses']]
        missing_msg = '' if len(missing_courses) == 0 else (f'Missing from CUNYfirst: '
                                                            f'{" and ".join(missing_courses)}')

        found_list.append(''.join(f'[{p}]' for p in current_path) + f' {requirement_str}' + ' from '
                          + ' or '.join([f'{c.course_id:06}:{c.offer_nbr}'
                                         for c in active_courses]) + missing_msg)
        college, requirement_type, requirement_value, *context_path = current_path
        print(college, requirement_type, requirement_value, context_path)
      else:
        if 'label' in where.keys():
          current_path.append(where['label'])
        else:
          current_path.append(key)
        search_for(value, current_path, found_list)
        current_path.pop()
  else:
    # Ignore things that aren't dicts or lists
    # print(f'{depth}{where}: not list or dict')
    pass
  depth = depth[0:-2]


# __main__()
# =================================================================================================
if __name__ == '__main__':
  parser = ArgumentParser('Look up course list contexts')
  parser.add_argument('-i', '--institutions', nargs='*', default=['qns'])
  parser.add_argument('-t', '--block_types', nargs='*', default=['major'])
  parser.add_argument('-v', '--block_values', nargs='*', default=['current'])
  parser.add_argument('-f', '--force', action='store_true')
  parser.add_argument('-p', '--period', default='current')
  args = parser.parse_args()
  period = args.period.lower()

  # Allowable values for period
  assert period in ['all', 'current']

  with open('./debug', 'w') as debug:
    conn = PgConnection()
    cursor = conn.cursor()
    institutions = [inst.upper().strip('01') for inst in args.institutions]
    for institution in institutions:
      institution = institution + '01'
      block_types = [arg.upper() for arg in args.block_types]
      for block_type in block_types:
        assert block_type in ['MAJOR', 'CONC', 'MINOR']
        block_values = [value.upper() for value in args.block_values]
        if 'ALL' in block_values:
          cursor.execute(f"""
        select block_value
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
    """)
          block_values = [row.block_value.upper() for row in cursor.fetchall()
                          if not row.block_value.isdigit()
                          and '?' not in row.block_value]
        for block_value in block_values:
          cursor.execute(f"""
        select period_stop, requirement_text, header_list, body_list
          from requirement_blocks
         where institution = '{institution}'
           and block_type = '{block_type}'
           and block_value ~* '^{block_value}$'
    """)
          for row in cursor.fetchall():
            if period == 'current' and row.period_stop != '99999999':
              continue
            print(f'{institution} {block_type} {block_value} {period}')
            header_list, body_list = (row.header_list, row.body_list)
            if len(header_list) == 0 or len(body_list) == 0 or args.force:
              header_list, body_list = dgw_interpreter(institution, block_type, block_value,
                                                       period_range=period)

            pprint(body_list, stream=debug)
            # Find course lists in the body
            depth = ''
            current_path = [institution[0:3], block_type, block_value]
            contexts = []
            search_for(body_list, current_path, contexts)
            for context in contexts:
              print(context)

