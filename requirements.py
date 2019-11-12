from enum import Enum
import json
from json import JSONEncoder
import re

import psycopg2
from psycopg2.extras import NamedTupleCursor
from collections import namedtuple
from datetime import datetime

from reserved_words import reserved_words, canonical

conn = psycopg2.connect('dbname=cuny_courses')
cursor = conn.cursor(cursor_factory=NamedTupleCursor)
cursor.execute("""select institution, discipline, discipline_name
                    from cuny_disciplines
                   where status ='A'""")
disciplines = dict()
discipline_names = dict()
for row in cursor.fetchall():
  institution = row.institution.lower().strip('0123456789')
  if institution not in disciplines.keys():
    disciplines[institution] = []
  disciplines[institution].append(row.discipline.lower())
  discipline_names[f'{institution}:{row.discipline.lower()}'] = row.discipline_name

quant_re = r'(\d+\.?\d*)(:\d+\.?\d*)?'
punctuations = ['_LBRACE_',
                '_RBRACE_',
                '_LPAREN_',
                '_RPAREN_',
                '_SEMI_',
                '_COLON_',
                '_AND_',
                '_OR_',
                '_DOT_',
                '_EQ_',
                '_NE_',
                '_GT_',
                '_LT_',
                '_LE_',
                '_GE_',
                ]


# tokenize()
# ------------------------------------------------------------------------------------------
def tokenize(lines, strings, institution):
  # NOTE: some discipline names have embedded spaces; these will have to be re-joined when a
  # sequence of two 'unknown' tokens are found in a course list.
  for line in lines:
    # Convert punctuation to tokens
    line = line.replace(',', ' _OR_ ')
    line = line.replace('+', ' _AND_ ')
    line = line.replace('{', ' _LBRACE_ ')
    line = line.replace('}', ' _RBRACE_ ')
    line = line.replace('(', ' _LPAREN_ ')
    line = line.replace(')', ' _RPAREN_ ')
    line = line.replace(';', ' _SEMI_ ')
    line = line.replace(':', ' _COLON_ ')
    line = line.replace('.', ' _DOT_ ')
    line = line.replace('=', ' _EQ_ ')
    line = line.replace('<>', ' _NE_ ')
    line = line.replace('>', ' _GT_ ')
    line = line.replace('<', ' _LT_ ')
    line = line.replace('<=', ' _LE_ ')
    line = line.replace('>=', ' _GE_ ')
    line = line.replace('< =', ' _LE_ ')
    line = line.replace('> =', ' _GE_ ')

    tokens = line.split()
    held = None
    index = 0
    for token in tokens:
      index += 1
      split_token = re.match(r'([a-z]+)(\d+)', token, re.I)
      if split_token:
        token = split_token.group(1)
        tokens.insert(index, split_token.group(2))
      if re.match(r'_str_\d{5}', token):
        token_type = 'string'
        try:
          value = strings[token]
        except KeyError as ke:
          print(f'TOKENIZER ERROR: {line}\n  KeyError: "{ke}"')
          for key in strings.keys():
            print(f'{key}: "{strings[key]}"')
          exit(1)
      elif '@' in token:
        # could be a discipline or catalog number
        token_type = 'wildcard'
        value = token
      elif token in punctuations:
        token_type = 'punctuation'
        value = token
      elif token.lower() in ['and', 'or']:
        token_type = 'punctuation'
        value = f'_{token.upper()}_'
      elif token.lower() in disciplines[institution]:
        token_type = 'discipline'
        value = token.lower()
      else:
        # Quantifier can be:
        #   int (int_value)
        #   int:int (int_range)
        #   float (float_value)
        #   float:float, int:float, float:int (float_range)
        nums = re.match(quant_re, token)
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
              upper_val = int(nums.group(2)[1:])
            except ValueError as ve:
              upper_val = float(nums.group(2)[1:])
              token_type = 'float_range'
            value = {'from': value, 'to': upper_val}
        else:
          # At this point, we would like everything to be a reserved word.
          # So we try all the reservered word regexs and count how many of each is found.
          # Create a list of unknowns for each college.
          reserved_word = canonical(token)
          if reserved_word is not None:
            token_type = 'reserved'
            value = reserved_word
          else:
            token_type = 'unknown'
            value = token
      yield {'token_type': token_type, 'value': value}


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

    # Preprocess block to make tokenization easier
    for line in self.lines:
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
    tokens = tokenize(self.header_lines, strings, institution)
    for token in tokens:
      if token['token_type'].endswith('_range'):
        value_str = f'between {token["value"]["from"]} and {token["value"]["to"]}'
      else:
        value_str = token['value']
      print(f'{institution}\t{token["token_type"]}\t|{value_str}|')

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
