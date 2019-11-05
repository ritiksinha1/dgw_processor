from enum import Enum
import json
from json import JSONEncoder
import re

from collections import namedtuple
from datetime import datetime

quant = r'(\d+\.?\d*)(:\d+\.?\d*)?'
quantifier = namedtuple('Quantifier', 'lower upper')


def tokenize(lines, strings):
  # NOTE: some discipline names have embedded spaces; these will have to be re-joined when a
  # sequence of two 'keyword' tokens are found in a course list.
  tokens = ' '.join(lines).split()
  for token in tokens:
    if re.match(r'_str_\d{5}', token):
      token_type = 'string'
      value = strings[token]
    elif '@' in token:
      token_type = 'wildcard'
      value = token
    elif token in ['lparen', 'rparen', 'semi', 'colon', 'and', 'or']:
      token_type = 'punctuation'
      value = token
    else:
      # Quantifier can be:
      #   int (int_value)
      #   int:int (int_range)
      #   float (float_value)
      #   float:float, int:float, float:int (float_range)
      nums = re.match(quant, token)
      if nums is not None:
        try:
          value = int(nums.group(1))
          token_type = 'int_value'
        except ValueError as ve:
          value = float(nums.group(1))
          token_type = 'float_value'
        if nums.group(2) is not None:
          token_type = token_type.replace('_value', '_range')
          try:
            upper_val = int(nums.group(2))
          except ValueError as ve:
            upper_val = float(nums.group(2))
            token_type = 'float_range'
          value = {'from': value, 'to': upper_val}
      else:
        token_type = 'keyword'
        value = token
    yield {'token_type': token_type, 'value': value}


class State(Enum):
  """ Parsing states.
  """
  # Block States
  BEFORE = 1
  HEADER = 2
  RULES = 3
  AFTER = 4

  def next_section(self):
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
        rule_lines:     Scribe text between first semicolon and END., with comment lines dropped
        anomalies:      Parsing anomalies
  """

  def __init__(self, requirement_text):
    self.scribe_text = requirement_text
    self.requirements = {'precis': {}, 'details': {}}
    self.header_lines = []
    self.rule_lines = []
    self.anomalies = []
    self.comment_lines = []
    self.ignored_lines = []
    self.lines = requirement_text.split('\n')

    strings = dict()
    string_count = 0
    block_state = State.BEFORE
    line_count = 0

    for line in self.lines:
      # '(CLOB)' (Character large object) is an Oracle artifact
      line = line.replace('(CLOB)', '').strip()

      # Comment lines start with # or !
      if line.startswith('#') or \
         line.startswith('!') or \
         line.lower().startswith('log'):
        self.comment_lines.append(line)
        continue

      # Known to-ignore lines
      if re.match('proxy(-)?advice', line, re.I):
        self.ignored_lines.append(line)
        continue

      # tokenize strings
      if '"' in line:
        match = re.search('".*"', line)
        if not match:
          self.anomalies.append(f'{line}\nLine {line_count}: Unterminated string.')
          self.ignored_lines.append(line)
          continue
        else:
          string_count += 1
          string_id = f'_str_{string_count:05}'
          strings[string_id] = match.group(0).strip('"').strip()
          line = line.replace(match.group(0), string_id)
      if len(line) == 0:
        continue

      # tokenize punctuation
      line = line.replace(',', ' or ')
      line = line.replace('+', ' and ')
      line = line.replace('(', ' lparen ')
      line = line.replace(')', ' rparen ')
      line = line.replace(';', ' semi ')
      line = line.replace(':', ' colon ')

      # FSM for separating block's lines into header and body parts
      if block_state == State.BEFORE:
        # Observation: BEGIN is always alone on a separate line
        if line == 'BEGIN':
          block_state = block_state.next_section()
        else:
          self.comment_lines.append(line)
        continue

      if block_state == State.HEADER:
        # Observation: the first semicolon may be embedded in the middle of a line, or not
        parts = line.split(';')
        if parts[0] != '':
          self.header_lines.append(parts[0])
        if len(parts) > 1:
          block_state = block_state.next_section()
          if parts[1] != '':
            self.rule_lines.append(parts[1])
        continue

      if block_state == State.RULES:
        # Observation: END. may be embedded in the middle of a line, or not. It never appears in
        # label or remark strings.
        matches = re.match(r'(.*)END\.(.*)', line)
        if matches is None:
          self.rule_lines.append(line)
        else:
          if matches.group(1) != '':
            self.rule_lines.append(matches.group(0))
          if matches.group(2) != '':
            self.ignored_lines.append(matches.group(2))
          block_state = block_state.next_section()
        continue

        if block_state == State.AFTER:
          self.ignored_lines.append(line)

    if block_state != State.AFTER:
      self.anomalies.append(f'Incomplete requirement block in {block_state.name}.')

    # Process header (precis) lines
    tokens = tokenize(self.header_lines, strings)
    for token in tokens:
      if token['token_type'].endswith('_range'):
        value_str = f'between {token["value"].lower} and {token["value"].upper}'
      else:
        value_str = token['value']
      print(f'{token["token_type"]}\t{value_str}')

    # Process body (details) lines
    for line in self.rule_lines:
      pass

  def __str__(self):
    return self.requirements

  def debug(self):
    return '\n'.join(['*** HEADER LINES ***']
                     + self.header_lines
                     + ['*** RULE LINES ***']
                     + self.rule_lines
                     + ['*** ANOMALY LINES ***']
                     + self.anomalies
                     + ['*** COMMENT LINES ***']
                     + self.comment_lines
                     + ['*** IGNORED LINES ***']
                     + self.ignored_lines)

  def json(self):
    return json.dumps(self.__dict__, default=lambda x: x.__dict__)

  def html(self):
    for line in self.header_lines + self.rule_lines + self.anomalies:
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
