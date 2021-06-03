#! /usr/local/bin/python3
""" Look at course lists and their Scribe contexts.
    How to categorize courses as required, possible, forbidden?
"""

from argparse import ArgumentParser
from pgconnection import PgConnection
from dgw_interpreter import dgw_interpreter

from pprint import pprint


# search_for()
# -------------------------------------------------------------------------------------------------
def search_for(target: str, where: any, path: str, found_list: list) -> None:
  """ Depth-first recursive search of nested lists/dicts for dict keys matching target.
      Append the context_path to the found list.
  """
  if isinstance(where, list):
    for index in range(len(where)):
      if isinstance(where[index], dict):
        path += f' => [{index}/{len(where)}]'
        search_for(target, where[index], path, found_list)
  elif isinstance(where, dict):
    for key, value in where.items():
      path += f' => {key}'
      if key == target:
        found_list.append(f'{target} @ {path}')
  else:
    # Ignore things that aren't dicts or lists
    pass


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
            path = 'body'
            contexts = []
            search_for('course_list', body_list, path, contexts)
            pprint(contexts)
