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
import sys

from collections import namedtuple
from pprint import pprint, pformat

from catalogyears import catalog_years
from pgconnection import PgConnection

# Module-level variables
_quarantined_dict = None
_columns = ['Institution', 'Requirement ID', 'Block Type', 'Catalog', 'Year', 'Explanation',
            'Can Ellucian']
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
            value = [row.block_type, row.catalog, row.year, row.explanation, row.can_ellucian]
            _quarantined_dict[key] = value

  def __update_file__(self):
    """ Write the dict to the file. Column names are capitalized; keys are not.
    """
    with open(_csv_file, 'w', newline='') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(_columns)
      keys = sorted(_quarantined_dict.keys())
      for key in keys:
        writer.writerow([key.institution, key.requirement_id] + _quarantined_dict[key])

  def __setitem__(self, k: _Key, v: list) -> dict:
    """ Given the explanation and can_ellucian strings, fill in the remainder of the quarantined
        dict entry, insert it into the dict; update the CSV file, and return the inserted entry as
        a dict.
    """
    assert len(v) == 2, f'Two strings (explanation, can_ellucian) expected; {len(v)} received.'
    global _quarantined_dict
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f"""
    select block_type, period_start, period_stop
      from requirement_blocks
     where institution = '{k[0]}'
       and requirement_id = '{k[1]}'
    """)
    assert cursor.rowcount == 1
    row = cursor.fetchone()
    conn.close()

    block_type = row.block_type.upper()
    catalog_info = catalog_years(row.period_start, row.period_stop)
    catalog = ('UGRD' if catalog_info.catalog_type == 'Undergraduate' else
               'GRAD' if catalog_info.catalog_type == 'Graduate'else
               'Unknown')
    year = 'Current' if catalog_info.last_year == 'Now' else catalog_years.last_year

    _quarantined_dict[k] = [block_type, catalog, year] + v
    self.__update_file__()

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

  def __str__(self):
    return pformat(_quarantined_dict)


# Testing
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  quarantined_dict = QuarantineManager()
  # (BAR01, RA000185) is used for testing.
  test_key = _Key._make(('BAR01', 'RA000185'))
  do_continue = True
  while do_continue:
    if quarantined_dict.is_quarantined(test_key):
      print(f'({test_key.institution}, {test_key.requirement_id}) IS quarantined')
    else:
      print(f'({test_key.institution}, {test_key.requirement_id}) is NOT quarantined')
    print('toggle, dump, Exit: ', end='')
    choice = input()

    if choice.lower().startswith('t'):
      if quarantined_dict.is_quarantined(test_key):
        del quarantined_dict[test_key]
      else:
        quarantined_dict[test_key] = ['Because I said so', 'Unknown']
        print(f'({test_key.institution}, {test_key.requirement_id}) is now ',
              quarantined_dict[test_key])

    elif choice.lower().startswith('d'):
      with open(_csv_file) as f:
        print(f.read())
      for key, value in quarantined_dict.items():
        print(f'({key.institution}, {key.requirement_id}): ', value)

    else:
      do_continue = False
