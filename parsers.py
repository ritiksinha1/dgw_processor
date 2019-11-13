"""
"""
import re
import sys

import psycopg2
from psycopg2.extras import NamedTupleCursor
from collections import namedtuple

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
    disciplines[institution] = ['any']
    discipline_names[f'{institution}:any'] = 'Any Discipline'
  disciplines[institution].append(row.discipline.lower())
  discipline_names[f'{institution}:{row.discipline.lower()}'] = row.discipline_name

Token = namedtuple('Token', 'type value')

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
#    line = line.replace(':', ' _COLON_ ')
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
    index = 0
    for token in tokens:
      index += 1

      # Check for splittable token: <letters><digits>
      split_token = re.match(r'([a-z]+)(\d+)', token, re.I)
      if split_token:
        token = split_token.group(1)
        tokens.insert(index, split_token.group(2))

      # Extract stings to string_table
      if re.match(r'_str_\d{5}', token):
        token_type = 'string'
        try:
          value = strings[token]
        except KeyError as key_error:
          print(f'TOKENIZER ERROR: {line}\n  KeyError: "{key_error}"')
          for key in strings.keys():
            print(f'{key}: "{strings[key]}"')
          exit(1)

      # Check if quantifier token
        # Quantifier can be:
        #   int (int_value)
        #   int:int (int_range)
        #   float (float_value)
        #   float:float, int:float, float:int (float_range; promote ints)
      nums = re.match(r'(\d+\.?\d*)(:\d+\.?\d*)?', token)
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
            value = float(value)
            token_type = 'float_range'
          value = {'min': value, 'max': upper_val}

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
        # At this point, we would like everything to be a reserved word.
        # So we try all the reservered word regexes.
        reserved_word = canonical(token)
        if reserved_word is not None:
          token_type = 'reserved'
          value = reserved_word
        else:
          # Alas, it’s not a reserved word either. We’ll call it a terminal symbol.
          token_type = 'terminal'
          value = token
      yield Token(token_type, value)


def error_report(str, saved_tokens=[]):
  """ Print the error string, and dump/purge the list of saved tokens.
  """
  print(str, file=sys.stderr)
  while len(saved_tokens) > 0:
    print(f'  {saved_tokens.pop()}', file=sys.stderr)


def parse_header(lines, strings, institution):
  """
  """
  saved_tokens = []
  expect = None
  parse_tree = dict()
  for token in tokenize(lines, strings, institution):
    if expect is not None:
      if token.type in expect:
        parse_tree[saved_tokens.pop().value] = token.value
      else:
        error_report(f'Expected {expect}, got {token}')
      expect = None

    elif token in [('reserved', 'mingrade'),
                   ('reserved', 'mingpa')]:
      saved_tokens.append(token)
      expect = ['float_value']

    elif token == ('reserved', 'credits'):
      num_credits = saved_tokens.pop()
      if num_credits.type == 'int_value':
        num_credits = num_credits.value
        credit_type = 'total_credits'
      else:
        error_report(f'Expected number of credits, got {num_credits}')
        for item in saved_tokens:
          print(item, file=sys.stderr)
      if len(saved_tokens) > 0:
        credit_type = saved_tokens.pop()
        if credit_type in [('reserved', 'maxpassfail'),
                           ('reserved', 'minres')]:
          credit_type = credit_type.value
        else:
          credit_type = 'total_credits'

      parse_tree[credit_type] = num_credits
    else:
      saved_tokens.append(token)
  return parse_tree


def parse_rules(lines):
  """
  """
  parse_tree = dict()
  for token in tokenize(lines):
    pass
  return parse_tree
