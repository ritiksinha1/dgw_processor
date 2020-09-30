#! /usr/local/bin/python3
"""
    Generate HTML representation of nested lists/dicts.

    Each list will be presented as an unordered list, which will be the contents of a details
    element.

    Each dict will be presented as a definition list, with the keys as definition terms and the
    values as definitions.

    Lists and dicts can be nested within one another to any depth.

    The unordered and definition lists will be contained in details elements.

      If a dict has a "tag" key, it's value will be the summary element of the details element.
      Otherwise the summary will be the word "unnamed."

      The length of each list is appended to the summary element of its containing details element.

"""

import sys


# details()
# -------------------------------------------------------------------------------------------------
def details(info: dict) -> str:
  """
  """
  try:
    tag_val = info.pop('tag')
  except KeyError as ke:
    tag_val = 'unnamed'

  return_str = f'<details><summary>{tag_val}</summary>'

  for key, value in info.items():
    key_name = 'value' if key == 'number' else key

    if value is None:
      continue  # Omit empty fields

    if isinstance(value, bool):
      return_str += f'<div>{key}: {value}</div>'

    elif isinstance(value, str):
      try:
        # Interpret numeric and range strings
        if ':' in value and 2 == len(value.split(' :')):
          # range of values: check if floats or ints
          range_floor, range_ceil = [float(v) for v in value.split(':')]
          if range_floor != int(range_floor) or range_ceil != int(range_ceil):
            return_str += f'<div>{key_name}: between {range_floor:0.1f} and {range_ceil:0.1f}</div>'
          elif int(range_floor) != int(range_ceil):
            return_str += f'<div>{key_name}: between {int(range_floor)} and {int(range_ceil)}</div>'
          else:
            # both are ints and are the same
            return_str += f'<div>{key_name}: {int(range_floor)}</div>'
        else:
          # single value
          if int(value) == float(value):
            return_str += f'<div>{key_name}: {int(value)}</div>'
          else:
            return_str += f'<div>{key_name}: {float(value):0.1f}</div>'

      except ValueError as ve:
        # Not a numeric string
        return_str += f'<div>{key_name}: {value}</div>'

    else:
      return_str += to_html(value)

  return return_str + '</details>'


# unordered_list()
# -------------------------------------------------------------------------------------------------
def unordered_list(info: list) -> str:
  """
  """
  num = len(info)
  suffix = '' if num == 1 else 's'
  if num <= 12:
    num_str = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
               'ten', 'eleven', 'twelve'][num]
  else:
    num_str = f'{num:,}'
  return_str = f'<details><summary>{num_str} item{suffix}</summary>'
  return_str += '\n'.join([f'{to_html(element)}' for element in info])
  return return_str + '</details>'


# to_html()
# -------------------------------------------------------------------------------------------------
def to_html(info: any) -> str:
  """  Return a nested HTML data structure as described above.
  """
  if info is None:
    return 'None'
  if isinstance(info, bool):
    return 'True' if info else 'False'
  if isinstance(info, list):
    return unordered_list(info)
  if isinstance(info, dict):
    return details(info)

  return info
