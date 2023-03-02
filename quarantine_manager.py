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
import datetime
import json
import psycopg
import sys

from collections import namedtuple
from pathlib import Path
from pprint import pformat
from psycopg.rows import namedtuple_row

from catalogyears import catalog_years

# Module-level variables
_columns = ['Institution', 'Requirement ID', 'Block Type', 'Catalog', 'Year', 'Explanation']
_fieldnames = [col.lower().replace(' ', '_') for col in _columns[2:]]
_Key = namedtuple('_key', 'institution requirement_id')
_Values = namedtuple('_Values', _fieldnames)


class QuarantineManager(dict):
  """Manage dict of quarantined dap_req_blocks.

  Initialized from the requirement_blocks table, but command line interface available for saving the
  dict to quarantined_blocks.csv and/or for using quarantined_blocks.csv to build a new copy of the
  dict.
  """

  home_dir = Path.home()
  _csv_file = Path(home_dir, 'Projects/dgw_processor/quarantined_blocks.csv')

  # __init__()
  # -----------------------------------------------------------------------------------------------
  def __init__(self):
    """Initialize the dict from the db.

    Can be overwritten from the csv file or written to the csv file.
    """
    self._quarantined_dict = dict()

    # Build the dict from the set of blocks with parse_tree errors.
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("""
        select institution, requirement_id,
               block_type, period_start, period_stop, parse_tree->'error' as explanation
          from requirement_blocks
         where parse_tree->'error' is not null
         order by institution, requirement_id
        """)
        for row in cursor:
          match row.period_start.lower()[-1]:
            case 'u': catalog = 'UGRD'
            case 'g': catalog = 'GRAD'
            case _: catalog = 'Unknown'
          year = 'Current' if row.period_stop.startswith('9') else row.period_stop.strip('UG')
          explanation = row.explanation.replace('Quarantined: ', '')
          key = (row.institution, row.requirement_id)
          values = _Values._make([row.block_type, catalog, year, explanation])
          self._quarantined_dict[key] = values

    # The dict is dirty if it changes without updating the db
    self._dict_dirty = False
    # The file is dirty if the dict has changed and hasn't been written to it. No check is made to
    # see whether the db actually agrees with the file
    self._file_dirty = False

  # is_dict_dirty
  # -----------------------------------------------------------------------------------------------
  @property
  def is_dict_dirty(self):
    """Getter for dict_dirty property."""
    return self._dict_dirty

  # is_file_dirty
  # -----------------------------------------------------------------------------------------------
  @property
  def is_file_dirty(self):
    """Getter for file_dirty property."""
    return self._file_dirty

  # file
  # -----------------------------------------------------------------------------------------------
  @property
  def file(self):
    """Return the contents of the CSV file."""
    with open(self._csv_file) as f:
      return (f.read())

  # list
  # -----------------------------------------------------------------------------------------------
  @property
  def list(self):
    """Return a list of quarantined blocks, with explanations."""
    sk = sorted(self._quarantined_dict.keys(), key=lambda k: [k[0], k[1]])
    return [f'{k[0]} {k[1]}: {self._quarantined_dict[k].explanation}' for k in sk]

  # keys
  # -----------------------------------------------------------------------------------------------
  @property
  def keys(self):
    """Return list of (institution, requirement_id) tuples."""
    return [k for k in self._quarantined_dict.keys()]

  # _read()
  # -----------------------------------------------------------------------------------------------
  def _read(self):
    """Construct dict from CSV file."""
    new_dict = dict()
    with open(QuarantineManager._csv_file, newline='') as csv_file:
      reader = csv.reader(csv_file)
      for line in reader:
        if reader.line_num == 1:
          CSV_Row = namedtuple('CSV_Row', [c.lower().replace(' ', '_') for c in line])
        else:
          row = CSV_Row._make(line)
          value = _Values._make([row.block_type, row.catalog, row.year, row.explanation])
          new_dict[(row.institution, row.requirement_id)] = value
    return new_dict

  # read()
  # -----------------------------------------------------------------------------------------------
  def read(self):
    """Public method for replacing dict using contents of the csv file."""
    old_len = len(self._quarantined_dict)
    new_dict = self._read()
    new_len = len(new_dict)
    are_different = old_len != new_len
    if not are_different:
      for key, explanation in self._quarantined_dict.items():
        if key in new_dict.keys() and new_dict[key] == self._quarantined_dict[key].explanation:
          continue
        are_different = True
        break

    if are_different:
      self._quarantined_dict = new_dict
      self._dict_dirty = True
    else:
      self._dict_dirty = False

    return are_different

  # write()
  # -----------------------------------------------------------------------------------------------
  def write(self):
    """Back up the CSV file, and write the dict to a new one.

    Leaves dirtiness unchanged.
    """
    #   Back up current CSV
    csv_file = QuarantineManager._csv_file
    csv_file.rename(f'./quarantined_blocks_{datetime.date.today()}')

    # Create new CSV
    sk = sorted(self._quarantined_dict.keys(), key=lambda k: [k[0], k[1]])
    with open(csv_file, 'w', newline='') as csv_file:
      writer = csv.writer(csv_file)
      writer.writerow(['Institution', 'Requirement ID', 'Block Type', 'Catalog', 'Year',
                       'Explanation'])
      for key in sk:
        writer.writerow([key[0], key[1]] + list(self._quarantined_dict[key]))
    return len(self._quarantined_dict)

  # update()
  # -----------------------------------------------------------------------------------------------
  def update(self):
    """Replace the parse trees of all quarantined blocks with explanations from current dict."""
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor() as cursor:
        num_updated = num_failed = 0
        for key, value in self._quarantined_dict.items():
          institution, requirement_id = key
          parse_tree = json.dumps({'error': value.explanation,
                                   'header_list': [],
                                   'body_list': []})
          cursor.execute("""
          update requirement_blocks set parse_tree = %s
          where institution ~* %s
          and requirement_id = %s
          """, (parse_tree, institution, requirement_id))
          if cursor.rowcount == 1:
            num_updated += 1
          else:
            num_failed += 1

    self._dict_dirty = False
    return {'num_updated': num_updated,
            'num_failed': num_failed}

  # __setitem__()
  # -----------------------------------------------------------------------------------------------
  def __setitem__(self, k: _Key, explanation: str) -> dict:
    """Implement the add command.

    Given the explanation, fill in the remainder of the quarantined dict entry, insert it into the
    dict, and update the parse_tree in the db. This leaves the file dirty until it gets written to
    the CSV.
    """
    assert len(k) == 2, f'Key should be (institution, requirement_id): {k} received'
    if not isinstance(k, _Key):
      # We can deal with that
      k = _Key._make(k)
    institution, requirement_id = k

    assert isinstance(explanation, str), f'Explanation is not a string'

    # Get block metadata
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

        self._quarantined_dict[k] = [block_type, catalog, year, explanation]

        # Update the parse_tree in the db
        parse_tree = json.dumps({'error': f'{explanation}', 'header_list': [], 'body_list': []})
        cursor.execute("""
        update requirement_blocks set parse_tree = %s
        where institution = %s
          and requirement_id = %s
        """, (parse_tree, institution, requirement_id))
        assert cursor.rowcount == 1, f'Update {institution} {requirement_id} failed'

    self._file_dirty = True

  # __delitem__()
  # -----------------------------------------------------------------------------------------------
  def __delitem__(self, k):
    """Remove k from the dict and CSV file if is quarantined.

    Return a copy of the deleted entry as a dict, or None if the key was not quarantined.
    """
    if k not in self._quarantined_dict.keys():
      raise KeyError(f'Unable to delete {k}: not quaratined.')
    return_dict = {k: self._quarantined_dict[k]}
    del self._quarantined_dict[k]
    self._dict_dirty = True
    self._file_dirty = True

  # __getitem__()
  # -----------------------------------------------------------------------------------------------
  def __getitem__(self, k):
    """Getter for quarantined blocks."""
    return (self._quarantined_dict[k])

  # is_quarantined()
  # -----------------------------------------------------------------------------------------------
  def is_quarantined(self, key):
    """Return presence of block in the quarantined dict."""
    try:
      return self._quarantined_dict[key].explanation
    except KeyError:
      return None

  def __str__(self):
    """Dunder method for printable copy of quarantined dict (not used)."""
    return pformat(self._quarantined_dict)


# Testing/Managing
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  """ Accept commands for viewing/adding blocks to the quarantine list.
  """
  qm = QuarantineManager()

  # Accept initial command from command line
  if len(sys.argv) > 1:
    choice = ' '.join(sys.argv[1:])
  else:
    # ... or not
    choice = '-'  # starter-upper

  # CLI until empty line, quit, or exit
  while selection := choice.lower():
    # Allow command name to overlap with institution names that start with q or e
    if selection in ['q', 'e', 'quit', 'exit']:
      break

    match selection[0]:

      case '?' | 'h':
        # CRUD operations
        print('Add {institution requirement_id reason} to dict, CSV file, and db')
        print('Change explanation')
        print('File: show CSV file')
        print('List: list blocks')
        print('Read CSV to dict')
        print('Write dict to CSV')
        print('Update db from dict')
        # Query
        print('<institution> <requirement_id> Is Quarantined?')

      case 'a':
        # Add institution requirement_id reason to dict, CSV, and db
        try:
          # add institution requirement_id explanation
          cmd, institution, requirement_id, *explanation = choice.split()
          institution = institution[0:3].upper() + '01'
          requirement_id = f"RA{int(requirement_id.lower().strip('ra')):06}"
          explanation = ' '.join(explanation)
          key = (institution, requirement_id)
          if qm.is_quarantined(key):
            print(f'{institution} {requirement_id} is already quarantined')
          else:
            qm[key] = explanation
            print(f'Quarantined {institution} {requirement_id}')
        except Exception as err:
          print(f'Add failed: {err}')

      case 'c':
        # Change an explanation
        try:
          cmd, institution, requirement_id, *explanation = choice.split()
          institution = institution[0:3].upper() + '01'
          requirement_id = f"RA{int(requirement_id.lower().strip('ra')):06}"
          explanation = ' '.join(explanation)
          key = (institution, requirement_id)
          if old_text := qm.is_quarantined(key):
            qm[key] = explanation
            print(f'Changed “{old_text}” ==> “{explanation}”')
          else:
            print(f'{institution} {requirement_id} is not quarantined')
        except Exception as err:
          print(f'Change failed: {err}')

      case 'f':
        # Show the CSV file
        print(qm.file)

      case 'l':
        # Show the dict
        for line in qm.list:
          print(line)

      case 'r':
        # Read csv file into dict
        if qm.read():
          print('Dict changed')
          assert qm.is_dict_dirty
        else:
          print('No difference')
          assert not qm.is_dict_dirty

      case 'w':
        # Write the dict to the CSV
        num_rows = qm.write()
        print(f'Saved {num_rows} blocks')

      case 'u':
        # Update the db from the dict
        result = qm.update()
        for k, v in result.items():
          print(k, v)

      case 'e':
        # Exit
        break

      case '-':
        # The starter-upper dummy command
        pass

      case _:
        # Not a command, possibly a block check
        try:
          institution, requirement_id = choice.split()
          institution = institution.strip('01').upper() + '01'
          requirement_id = f'RA{requirement_id.strip("RA"):>06}'
          explanation = qm.is_quarantined((institution, requirement_id))
          if explanation:
            print(f'{institution} {requirement_id}: {explanation}')
          else:
            print(f'{institution} {requirement_id} is not quarantined')
        except Exception as err:
          print(f'Command deficiency detected: {err}', file=sys.stderr)

    choice = input('help | add | file | list | read | write | update : ')

  # Exit
  # -----------------------------------------------------------------------------------------------
  """ Allow exit without committing pending changes to the CSV and/or database.
  """
  if qm.is_dict_dirty:
    reply = input('Update db before exiting? [Yn]? ')
    if reply.lower().startswith('n'):
      print('Not Updated')
    else:
      result = qm.update()
      for k, v in result.items():
        print(k, v)

  if qm.is_file_dirty:
    reply = input('Save CSV before exiting? [Yn]? ')
    if reply.lower().startswith('n'):
      exit('Dirty exit')
    else:
      num_blocks = qm.write()
      exit(f'Saved {num_blocks} blocks')
  else:
    exit()
