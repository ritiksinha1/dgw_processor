
import sys
import re
from enum import Enum
import json
from json import JSONEncoder
from collections import namedtuple
from datetime import datetime

from parsers import parse_header, parse_rules

RequirementDict = namedtuple('RequirementDict', 'header rules')


# Class State
# =================================================================================================
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


# Class Requirements
# =================================================================================================
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

  # init()
  # -----------------------------------------------------------------------------------------------
  def __init__(self, requirement_text, institution):
    self.scribe_text = requirement_text
    self.requirements = RequirementDict({}, {})
    self.header_lines = []
    self.rule_lines = []
    self.anomalies = []
    self.comment_lines = []
    self.ignored_lines = []

    lines = requirement_text.split('\n')
    strings = dict()
    string_count = 0
    block_state = State.BEFORE
    line_count = 0

    # Preprocess block to make tokenization easier
    for line in lines:
      # '(CLOB)' (Character large object) is an Oracle artifact
      line = line.replace('(CLOB)', '').strip()

      # Convert strings to tokens
      string_failure = False
      while '"' in line:
        match = re.search('"(.*?)"', line)
        if not match:
          self.anomalies.append(f'{line}\nLine {line_count}: Unterminated string.')
          self.ignored_lines.append(line)
          string_failure = True
          break
        else:
          string_count += 1
          string_id = f'_str_{string_count:05}'
          strings[string_id] = match.group(1).strip()
          line = line.replace(f'"{match.group(1)}"', f' {string_id} ')
      if string_failure:
        continue

      # Comments lines start with # or ! in the docs; but also with // in practice
      match = re.match(r'(.*?)(#|!|//)(.*$)', line)
      if match:
        self.comment_lines.append(match.group(2) + match.group(3))
        line = match.group(1)

      # Filter out lines with rows of 3 or more asterisks, dashes, backslashes, or equal signs
      match = re.search(r'(\\{3,}|\*{3,}|\-{3,}|={3,})', line)
      if match:
        self.ignored_lines.append(line)
        continue

      # Known to-ignore keyword lines
      # if re.match('log|proxy(-)?advice', line, re.I):
      #   self.ignored_lines.append(line)
      #   continue

      # Ignore empty lines
      if len(line.strip()) == 0:
        continue

      # FSM for separating block's lines into header and body parts
      if block_state == State.BEFORE:
        # Observation: BEGIN is always alone on a separate line
        if line == 'BEGIN':
          block_state = block_state.next_section()
        else:
          self.ignored_lines.append(line)
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
        # label or remark strings. Whatever is before it is a rule line; whatever follows it gets
        # ignored.
        matches = re.match(r'(.*)END\.(.*)', line, re.I)
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

    # Process header lines
    # tokens = tokenize(self.header_lines, strings, institution)
    # for token in tokens:
    #   if token['token_type'].endswith('_range'):
    #     value_str = f'between {token["value"]["from"]} and {token["value"]["to"]}'
    #   else:
    #     value_str = token['value']
    #   if token['token_type'] == 'unknown':
    #     if institution not in unknown_tokens_by_institution.keys():
    #       unknown_tokens_by_institution[institution] = dict()
    #     if token['value'] not in unknown_tokens_by_institution[institution].keys():
    #       unknown_tokens_by_institution[institution][token['value']] = 0
    #     unknown_tokens_by_institution[institution][token['value']] += 1
    #   else:
    #     if (institution, token['token_type']) not in token_types_by_institution.keys():
    #       token_types_by_institution[(institution, token['token_type'])] = 0
    #     token_types_by_institution[(institution, token['token_type'])] += 1
    self.header = parse_header(self.header_lines, strings, institution)
    # Process body (details) lines
    for line in self.rule_lines:
      pass

  # __str__()
  # -----------------------------------------------------------------------------------------------
  def __str__(self):
    return self.requirements

  # debug()
  # -----------------------------------------------------------------------------------------------
  def debug(self):
    # print(f'=================================\n{self.scribe_text}\n------------------------------',
    #       file=sys.stderr)
    print('\n'.join(self.header_lines), '\n---------------------------------', file=sys.stderr)
    print(self.header, file=sys.stderr)
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

  # json()
  # -----------------------------------------------------------------------------------------------
  def json(self):
    return json.dumps(self.__dict__, default=lambda x: x.__dict__)

  # html()
  # -----------------------------------------------------------------------------------------------
  def html(self):
    for line in self.header_lines + self.rule_lines + self.anomalies:
      returnVal += f'<p>{line}</p>'
    return returnVal


# Class AcademicYear
# =================================================================================================
class AcademicYear:
  """ This is a helper class for representing one academic year as a string.
      Academic years run from September through the following August.
      The sting will be either CCYY-YY or CCYY-CCYYY or Now
  """
  # __init__()
  # -----------------------------------------------------------------------------------------------
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

  # __str__()
  # -----------------------------------------------------------------------------------------------
  def __str__(self):
    if self.is_now:
      return 'Now'
    else:
      if self.century_1 != self.century_2:
        return f'{self.century_1}{self.year_1:02}-{self.century_2}{self.year_2:02}'
      else:
        return f'{self.century_1}{self.year_1:02}-{self.year_2:02}'


# Class Catalogs
# =================================================================================================
class Catalogs():
  """ Represents a range of catalog years and which catalogs (graduate, undergraduate, both, or
      unspecified) are involved. When a student starts a program, the catalog year tells what the
      requirements are at that time.
  """
  # __init__()
  # -----------------------------------------------------------------------------------------------
  def __init__(self, period_start, period_stop):
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

  # __str__()
  # -----------------------------------------------------------------------------------------------
  def __str__(self):
    if self.first_academic_year != self.last_academic_year:
      return f'{self.first_academic_year} through {self.last_academic_year}'
    else:
      return f'{self.first_academic_year}'
