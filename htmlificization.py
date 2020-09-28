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


# details()
# -------------------------------------------------------------------------------------------------
def details(struct: dict) -> str:
  """
  """
  try:
    tag = struct.pop('tag')
  except KeyError as ke:
    tag = 'unnamed'
  return_str = f'<details><summary>{tag}</summary>'
  return_str += '\n'.join([to_html(struct[element]) for elemeent in struct])
  return return_str + '</details>'


# unordered_list()
# -------------------------------------------------------------------------------------------------
def unordered_list(struct: list) -> str:
  """
  """
  return_str = '<ul>'
  return_str = '\n'.join([f'<li>{to_html(struct[element])}</li>' for element in struct])
  return return_str + '</ul>'


# to_html()
# -------------------------------------------------------------------------------------------------
def to_html(struct) -> str:
  """  Return a nested HTML data structure as described above.
  """
  if isinstance(struct, list):
    return unordered_list(struct)
  if isinstance(struct, dict):
    return details(struct)

  return struct
