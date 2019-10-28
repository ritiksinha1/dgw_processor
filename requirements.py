from enum import Enum
import json
from json import JSONEncoder
import re

from datetime import datetime


class State(Enum):
  """ Parsing states.
  """
  BEFORE = 1
  HEAD = 2
  BODY = 3
  AFTER = 4

  def next(self):
    if self.value < 4:
      return State(self.value + 1)
    else:
      return self


class Requirements():
  """ Representation of the requirements for a degree, major, minor, or concentration for one range
      of Catalog Years.

      The constructor takes a text description in Degreeworks Scribe format, which is stored as the
      "scribe_text" member. The parsed information is available in the "json" and "html" members.
      The _str_() method returns a plain text version.

      Fields:
        scribe_text     Raw requirements text in scribe format
        header_lines:   Scribe text between BEGIN and first semicolon, with comment lines dropped
        body_lines:     Scribe text between first semicolon and END., with comment lines dropped
        anomalies:      Parsing anomalies
  """

  def __init__(self, requirement_text):
    self.scribe_text = requirement_text
    self.header_lines = []
    self.body_lines = []
    self.ignored_lines = []
    self.anomalies = []
    self.lines = requirement_text.split('\n')
    state = State.BEFORE
    for line in self.lines:
      line = line.replace('(CLOB)', '').strip()
      if len(line) == 0:
        continue
      if line.startswith('#') or \
         line.startswith('!') or \
         line.lower().startswith('log'):
        self.ignored_lines.append(line)
      else:
        # FSM for separating block's lines into header and body parts
        if state == State.BEFORE:
          # Observation: BEGIN is always alone on a separate line
          if line == 'BEGIN':
            state = state.next()
          else:
            self.ignored_lines.append(line)
          continue
        if state == State.HEAD:
          # Observation: the first semicolon may be embedded in the middle of a line, or not
          parts = line.split(';')
          if parts[0] != '':
            self.header_lines.append(parts[0])
          if len(parts) > 1:
            state = state.next()
            if parts[1] != '':
              self.body_lines.append(parts[1])
          continue
        if state == State.BODY:
          # Observation: END. may be embedded in the middle of a line, or not. It never appears in
          # label or remark strings.
          matches = re.match(r'(.*)END\.(.*)', line)
          if matches is None:
            self.body_lines.append(line)
          else:
            if matches.group(1) != '':
              self.body_lines.append(matches.group(0))
            if matches.group(2) != '':
              self.ignored_lines.append(matches.group(2))
            state = state.next()
          continue
        if state == State.AFTER:
          self.ignored_lines.append(line)

    if state != State.AFTER:
      self.anomalies.append(f'Incomplete requirement block in state {state.name}.')

  def __str__(self):
    return '\n'.join(['HEADER LINES']
                     + self.header_lines
                     + ['BODY LINES']
                     + self.body_lines
                     + ['ANOMALIES']
                     + self.anomalies
                     + ['IGNORED']
                     + self.ignored_lines)

  def json(self):
    return json.dumps(self.__dict__, default=lambda x: x.__dict__)

  def html(self):
    for line in self.header_lines + self.body_lines + self.anomalies:
      returnVal += f'<p>{line}</p>'
    return returnVal


class AcademicYear:
  """ This is a helper class for representing one academic year as a string.
      Academic years run from September through the following August.
      The sting will be either CCYY-YY or CCYY-CCYYY or Now
  """
  def __init__(self, century_1=None, year_1=None, century_2=None, year_2=None):
    """ Academic_Year constructor. Second year must be one greater than the first.
        if no args, the year is “Now”
    """
    if century_1 is None:
      self.is_now = True
      now = datetime.now()
      # The current academic year began last year if it is now Jan-Aug.
      if now.month < 9:
        self.year = now.year - 1
      else:
        self.year = now.year
    else:
      self.is_now = False
      self.century_1 = int(century_1)
      self.year_1 = int(year_1)
      self.century_2 = int(century_2)
      self.year_2 = int(year_2)
      self.year = 100 * self.century_1 + self.year_1
      if (100 * self.century_1 + self.year_1 + 1) != (100 * self.century_2 + self.year_2):
        raise ValueError(f'{100 * self.century_1 + self.year_1}, '
                         f'{100 * self.century_2 + self.year_2} is not a valid pair of years')

  def __str__(self):
    if self.is_now:
      return 'Now'
    else:
      if self.century_1 != self.century_2:
        return f'{self.century_1}{self.year_1:02}-{self.century_2}{self.year_2:02}'
      else:
        return f'{self.century_1}{self.year_1:02}-{self.year_2:02}'


class Catalogs():
  def __init__(self, period_start, period_stop):
    """ Represents a range of catalog years and which catalogs (graduate, undergraduate, both, or
        unspecified) are involved. When a student starts a program, the catalog year tells what the
        requirements are at that time.

    """
    self.which_catalogs = []  # Serializable
    which_catalogs = set()  # Not serializable
    self.first_academic_year = None
    self.last_academic_year = None

    m_start = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_start)
    if m_start is not None:
      century_1, year_1, century_2, year_2, catalog = m_start.groups()
      try:
        self.first_academic_year = AcademicYear(century_1, year_1, century_2, year_2)
      except ValueError as e:
        self.first_academic_year = f'Unknown: {e}.'
      self.first_year = (century_1 * 100) + year_1
      if catalog == 'U':
        which_catalogs.add('Undergraduate')
      if catalog == 'G':
        which_catalogs.add('Graduate')

    if re.search(r'9999+', period_stop):
      self.last_academic_year = AcademicYear()
    else:
      m_stop = re.search(r'(19|20)(\d\d)-?(19|20)(\d\d)([UG]?)', period_stop)
      if m_stop is not None:
        century_1, year_1, century_2, year_2, catalog = m_stop.groups()
        try:
          self.last_academic_year = AcademicYear(century_1, year_1, century_2, year_2)
        except ValueError as e:
          self.last_academic_year = f'Unknown: {e}.'
        self.last_year = (century_1 * 100) + year_1
        if catalog == 'U':
          which_catalogs.add('Undergraduate')
        if catalog == 'G':
          which_catalogs.add('Graduate')
    self.which_catalogs = sorted(list(which_catalogs), reverse=True)

  def __str__(self):
    if self.first_academic_year != self.last_academic_year:
      return f'{self.first_academic_year} through {self.last_academic_year}'
    else:
      return f'{self.first_academic_year}'
