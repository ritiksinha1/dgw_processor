#! /usr/local/bin/python3

""" Using ../quarantined_blocks.csv as the backing store for a list of quarantined requirement
    blocks, make the list available to other modules as a dict indexed by (institution,
    requirement_id) tuples, while keeping the CSV file in sync with updates to the dict. The dict is
    shared by reference across instances of the QuarantineManager class. Module-level variables are
    used rather than static class variables simply to make references to them easier to type.
    Because of the limited scope of this application, no superclass methods are supported, and only
    the methods needed for this app are implemented here.
"""

import csv
import json
import psycopg
import sys

from collections import namedtuple
from pprint import pprint, pformat
from psycopg.rows import namedtuple_row

from catalogyears import catalog_years

# Module-level variables
_quarantined_dict = None
_columns = ['Institution', 'Requirement ID', 'Block Type', 'Catalog', 'Year', 'Explanation',
            'Can Ellucian']
_explanation_index = _columns.index('Explanation') - 2
_fieldnames = [col.lower().replace(' ', '_') for col in _columns]
_Row = namedtuple('_Row', _fieldnames)
_Key = namedtuple('_Key', 'institution requirement_id')
_csv_file = '/Users/vickery/Projects/dgw_processor/quarantined_blocks.csv'


class QuarantineManager(dict):
  """
  """

  def __init__(self):
    global _quarantined_dict
    if _quarantined_dict is None:
      _quarantined_dict = dict()
      with open(_csv_file) as csv_file:
        csv_reader = csv.reader(csv_file)
        for line in csv_reader:
          if csv_reader.line_num == 1:
            _columns = line
          else:
            row = _Row._make(line)
            key = _Key._make([row.institution, row.requirement_id])
            _quarantined_dict[key] = list(row._asdict().values())[2:]

  def __update_file__(self):
    """ Write the dict to the file. Column names are capitalized; keys are not.
    """
    with open(_csv_file, 'w', newline='') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(_columns)
      keys = sorted(_quarantined_dict.keys())
      for key in keys:
        writer.writerow([key[0], key[1]] + _quarantined_dict[key])

  def __setitem__(self, k: _Key, v: list) -> dict:
    """ Given the explanation and can_ellucian strings, fill in the remainder of the quarantined
        dict entry, insert it into the dict; update the CSV file, update the parse_tree in the db,
        and return the inserted entry as a dict.
    """
    assert len(k) == 2, f'Key should be (institution, requirement_id): {k} received'
    if not isinstance(k, _Key):
      # We can deal with that
      k = _Key._make(k)
    institution, requirement_id = k

    assert len(v) == 2, f'Two strings (explanation, can_ellucian) expected; {len(v)} received.'
    explanation, can_ellucian = v

    global _quarantined_dict
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute(f"""
        select block_type, period_start, period_stop
          from requirement_blocks
         where institution = '{institution}'
           and requirement_id = '{requirement_id}'
        """)
        assert cursor.rowcount == 1, f'{institution} {requirement_id} not in requirement_blocks.'
        row = cursor.fetchone()

    block_type = row.block_type.upper()
    catalog_info = catalog_years(row.period_start, row.period_stop)
    catalog = ('UGRD' if catalog_info.catalog_type == 'Undergraduate' else
               'GRAD' if catalog_info.catalog_type == 'Graduate'else
               'Unknown')
    year = 'Current' if catalog_info.last_year == 'Now' else catalog_years.last_year

    _quarantined_dict[k] = [block_type, catalog, year] + v

    # Update the CSV file
    self.__update_file__()

    # Update the parse_tree in the db
    parse_tree = json.dumps({'error': f'Quarantined: {explanation}'})
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("""
        update requirement_blocks set parse_tree = %s
        where institution = %s
          and requirement_id = %s
        """, (parse_tree, institution, requirement_id))
        assert cursor.rowcount == 1, f'Update {institution} {requirement_id} failed'

  def __delitem__(self, k):
    """ If k is quarantined, remove it from the dict and CSV file. Return a copy of the deleted
        entry as a dict, or None if the key was not quarantined.
    """
    if k not in _quarantined_dict.keys():
      raise KeyError(f'Unable to delete {k}: not quaratined.')
    return_dict = {k: _quarantined_dict[k]}
    del _quarantined_dict[k]
    self.__update_file__()

  def __getitem__(self, k):
    return(_quarantined_dict[k])

  def is_quarantined(self, k):
    return k in _quarantined_dict.keys()

  def keys(self):
    return sorted(_quarantined_dict.keys())

  def items(self):
    return sorted(_quarantined_dict.items())

  def explanation(self, key):
    try:
      return _quarantined_dict[key][_explanation_index]
    except KeyError as ke:
      return f'{ke}: Not quarantined'

  def __str__(self):
    return pformat(_quarantined_dict)


# Testing/Managing
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  """ Accept commands for viewing/adding blocks to the quarantine list.
  """
  quarantined_dict = QuarantineManager()

  # Accept initial command from command line
  if len(sys.argv) > 1:
    choice = ' '.join(sys.argv[1:])
  else:
    # ... or not
    choice = '-'  # starter-upper

  try:
    while choice.lower()[0] in ['-', '?', 'h', 'a', 'd', 'f', 'w']:
      selection = choice.lower()[0]
      if selection == '-':
        pass

      elif selection in ['?', 'h']:
        print('Add {institution requirement_id reason} to CSV file and db')
        print('Dict: show dict')
        print('File show CSV file')
        print('Write all CSV rows to db')

      elif selection == 'f':
        # Display the CSV file
        print('File:')
        with open(_csv_file) as f:
          print(f.read())

      elif selection == 'd':
        # Display the dict
        print('Dict:')
        for key, value in quarantined_dict.items():
          print(f'{key.institution}, {key.requirement_id}: '
                f'{quarantined_dict.explanation((key.institution, key.requirement_id))}')

      elif selection == 'w':
        # Update the parse_tree of all quarantined blocks in the requirement_blocks table.
        # Use this when the repo has an updated csv from another machine
        with psycopg.connect('dbname=cuny_curriculum') as conn:
          with conn.cursor(row_factory=namedtuple_row) as cursor:
            for key, value in quarantined_dict.items():
              parse_tree = json.dumps({'error': f'Quarantined: {value[3]}'})
              institution, requirement_id = key
              cursor.execute(f"""
              update requirement_blocks
                 set parse_tree = '{parse_tree}'
               where institution = %s
                 and requirement_id = %s
              """, key)
              if cursor.rowcount != 1:
                print(f'{institution} {requirement_id} update failed with {cursor.rowcount = }')
                continue
        print(f'Requirement Block parse_trees updated from CSV file')

      elif selection == 'a':
        # Add institution requirement_id reason to quarantine
        try:
          # add institution requirement_id reason...
          cmd, institution, requirement_id, *reason = choice.split()
          institution = institution[0:3].upper() + '01'
          requirement_id = int(requirement_id.lower().strip('ra'))
          requirement_id = f'RA{requirement_id:06}'
          reason = ' '.join(reason)
          key = (institution, requirement_id)
          print(institution, requirement_id, f'“{reason}”')
          if quarantined_dict.is_quarantined(key):
            print(f'\n{institution} {requirement_id} is already quarantined')
          else:
            quarantined_dict[key] = [reason, 'unknown']
            print(f'Quarantined {institution} {requirement_id}')
        except Exception as err:
          print(f'Add failed: {err}')

      else:
        try:
          institution, requirement_id = choice.split()
          institution = institution.strip('01').upper() + '01'
          requirement_id = f'RA{requirement_id.strip("RA"):06}'
          whether = '' if quarantined_dict.is_quarantined((institution, requirement_id)) else ' not'
          print(f'{institution} {requirement_id} is{whether} quarantined')
        except Exception as err:
          print(f'Command deficiency detected: {err}')

      choice = input('help | add | dict | file | write: ')

  except IndexError as ie:
    exit()
