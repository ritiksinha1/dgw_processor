""" Utils needed by htmlificization
      dict_to_html
      list_to_html
      to_html
"""

import os
import sys

from format_header_productions import format_header_productions
from format_body_qualifiers import format_body_qualifiers
import format_body_rules

if os.getenv('DEBUG_HTML_UTILS'):
  DEBUG = True
else:
  DEBUG = False

number_names = ['none', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve']


# dict_to_html()
# -------------------------------------------------------------------------------------------------
def dict_to_html(info: dict, section=None) -> str:
  """ A dict is shown as either as a html details element or a paragraph, depending on the number
      and values of the keys, and on whether it is a top-level dict in the header/body list for a
      block. Top-level dicts are indicated by “section” being either header or body; section was set
      by explicitly iterating over these two lists and invoking this function for each dict in those
      lists; from here, section is not set for any recursion that occurs.
  """

  if DEBUG:
    print(f'*** dict_to_html({list(info.keys())}, {section=})', file=sys.stderr)
  assert isinstance(info, dict), f'{type(info)} is not a dict'

  """ Based on all concentrations, majors, and minors with a period_end starting with '9' at CUNY in
      fall 2021, the following keys appeared in the top level of header_list dicts:

          class_credit_head conditional lastres_head maxclass_head maxcredit_head maxpassfail_head
          maxperdisc_head maxterm_head maxtransfer_head minclass_head mincredit_head mingpa_head
          mingrade_head minperdisc_head minres_head optional remark share_head standalone

          This agrees with the grammar, except: conditional_head was converted to conditional by the
          handler; and proxy-advice and under have been ignored by the handlers.

      and the following keys appeared in the top level of body_list dicts:
          block blocktype class_credit_body conditional copy_rules group_requirements noncourse
          remark subset

          This agrees with the grammar, except: conditional_body was converted to conditional by the
          conditional_body handler; group_requirement was converted to group_requirements (a list)
          by the handler; label does not appear (should be removed from the grammar because it makes
          no sense to have a label that isn't connected to a requirement); proxy-advice has been
          ignored by the handlers; rule_complete does not appear (like label, it doesn't make sense
          for this to appear without being connected to a requirement, (at least for Majors,
          Concentrations, and Minors)).

  """

  # Top-level dicts in Header and Body section lists
  # -----------------------------------------------------------------------------------------------
  """ Only certain productions are expected/allowed in the top level of header_list and body_list.
      Furthermore, certain keys have different meanings in the header (where they are rules and thus
      may have labels) and the body (where they act as “qualifiers” for requirements.)

      So this section validates the augmented parse tree in the sense that it makes sure that these
      top-level lists contain only the expected productions, and makes sure that header productions
      are handled differently from body qualifiers if necessary.
  """
  if section == 'header':
    # Format all top-level dicts in the Header
    return '\n'.join([element for element in format_header_productions(info)])
  elif section == 'body':
    body_rules = []
    for key, value in info.items():
      if html_str := format_body_rules.format_body_rule(key, value):
        body_rules.append(html_str)
      else:
        body_rules.append(f'<p class="error">{key} not dispatchable from body_list')
    return '\n'.join(body_rules)

  # All other dicts
  # -----------------------------------------------------------------------------------------------
  """ The top-level dicts may recursively invoke various dicts and lists. The recursive dict
  invocations get handled here.
  """

  return f'<p><em>Recursive dict_to_html(): {list(info.keys())}</em></p>'

  summary = None
  try:
    if label_str := info.pop('label'):
      summary = f'<summary>{label_str}</summary>'
  except KeyError:
    pass
  return_str = ''

  pseudo_msg = ''
  try:
    pseudo = info.pop('is_pseudo')
    if pseudo:
      pseudo_msg = '<p><strong>This is a Pseudo-requirement</strong></p>'
  except KeyError as ke:
    pass

  try:
    remark = info.pop('remark')
    remark = f'<p><strong>{remark}</strong></p>'
  except KeyError as ke:
    remark = ''

  try:
    display = info.pop('display')
    display = f'<p><em>{display}</em></p>'
  except KeyError as ke:
    display = ''

  # Extract any header productions from the dict.
  header_productions = '\n'.join(format_header_productions(info))
  print('keys', list(info.keys()))
  for key, value in info.items():
    print(f'key: {key}')
    if key == 'conditional':  # Special case for conditional dicts
      return conditional_to_details_element(info['conditional'], label)
    elif key == 'subset':
      return subset_to_details_element(info['subset'], label)
    elif key == 'group_requirements':
      return_str = ''
      for group_requirement in info['group_requirements']:
        return_str += group_requirement_to_details_elements(group_requirement, label)
      return return_str
    elif key == 'course_list':
      label_str, course_list = format_course_list(info['course_list'])
      if label:
        if label_str:
          return f"""
          <details>
            <summary>{label}</summary>
            <details>
              <summary>{label_str}</summary>
              {course_list}
            </details>
          </details
          """
        else:
          return f"""
          <details>
            <summary>{label}</summary>
            {course_list}
          </details>
          """
      else:
        label_str = label_str if label_str else '<span class="error">Unnamed requirement</span>'
        return f"""
        <details>
          <summary>{label_str}</summary>
          {course_list}
        </details>
        """
    elif key == 'rule_complete':
      rule_complete_dict = info['rule_complete']
      label_str = rule_complete_dict['label']
      if label is not None:
        label_str = label + label_str
      is_isnot = 'is' if rule_complete_dict['is_complete'] else 'is not'
      return f'<p><strong>{label_str}</strong>: Requirement <em>{is_isnot}</em> satisfied</p>'

    # Class lists and their qualifiers.
    cr_str = format_utils.format_num_class_credit(info)
    if cr_str is None:
      cr_str = ''
    else:
      cr_str = f'<p>{cr_str}</p>'

    qualifier_strings = format_body_qualifiers(info)
    for qualifier_string in qualifier_strings:
      class_attribute = ' class="error"' if 'Error:' in qualifier_string else ''
      cr_str += f'<p{class_attribute}>{qualifier_string}</p>'

    # Other min, max, and num items
    numerics = ''
    if key[0:3].lower() in ['max', 'min', 'num']:
      numerics += f'<p><strong>{key.replace("_", " ").title()}: </strong>{value}</p>'
    if numerics:
      print('xxxx numerics not shown', numerics)

    # course_list part of a multi-key dict
    course_list = ''
    if 'course_list' in info.keys():
      if DEBUG:
        print('    From dict_to_html()')
      label_str, course_list = format_course_list(info['course_list'])
      # If there is a non-empty label, use it as the summary of a complete details element
      if label_str:
        course_list = f'<details><summary>{label_str}</summary>{course_list}</details>'

    # All else
    print(f'xxxx all else: {key} {value}')
    # if isinstance(value, dict):
    #   return f'<details>{summary}{dict_to_html(value)}</details>'
    # elif isinstance(value, list):
    #   return f'<details>{summary}{list_to_html(value)}</details>'
    # else:
    #   return f'<details>{summary}{to_html(value)}</details>'

    # Development aid
    context_path = ''
    if DEBUG:
      try:
        context_path = f"<div>Context: {info['context_path']}</div>"
      except KeyError as ke:
        pass

    return_str = f'{pseudo_msg}{context_path}{remark}{display}{numerics}{course_list}'

    # Key-value pairs not specific to course lists
    # --------------------------------------------
    key_str = f'{key.replace("_", " ").title()}'

    if key == 'group':
      if len(value) > 0:
        suffix = '' if len(value) == 1 else 's'
        return_str += to_html(value, 'Group')
      continue

    if isinstance(value, bool):
      return_str += f'<div>{key_str}: {value}</div>'

    elif isinstance(value, str):
      try:
        # Interpret numeric and range strings
        if ':' in value and 2 == len(value.split(':')):
          # range of values: check if floats or ints
          range_floor, range_ceil = [float(v) for v in value.split(':')]
          if range_floor != int(range_floor) or range_ceil != int(range_ceil):
            return_str += (f'<div>{key_str}: between {range_floor:0.2f} and '
                           f'{range_ceil:0.2f}</div>')
          elif int(range_floor) != int(range_ceil):
            return_str += (f'<div>{key_str}: between {int(range_floor)} and '
                           f'{int(range_ceil)}</div>')
          else:
            # both are ints and are the same
            return_str += f'<div>{key_str}: {int(range_floor)}</div>'
        else:
          # single value
          if int(value) == float(value):
            return_str += f'<div>{key_str}: {int(value)}</div>'
          else:
            return_str += f'<div>{key_str}: {float(value):0.2f}</div>'

      except ValueError as ve:
        # Not a numeric string; just show the text.
        if key != 'context_path':  # This was for development purposes
          return_str += f'<div>{key_str}: {value}</div>'

    else:
      # Fall through
      print(f'xxxx Unhandled {key=} {value=}')

  return f'<details><summary>{label}</summary>{return_str}</details>'


# list_to_html()
# -------------------------------------------------------------------------------------------------
def list_to_html(info: list, section=None, is_area=False) -> str:
  """ If this is a section-level list, return a display element with the name of the sections as
      the summary, and the intepreted dicts in the list as the body.
      If this is a course-area list (square brackets in the Scribed course list), enclose the
      elements in a details element with "Course Area" as the summary.
      Otherwise, go through the list and process according to what is there.
  """
  if DEBUG:
    print(f'*** list_to_html({len(info)} elements, {section=})', file=sys.stderr)

  assert isinstance(info, list), f'{type(info)} is not list'

  # Top-level lists: header_list or body_list
  # -----------------------------------------
  if section is not None:
    summary = f'<summary>{section.title()}</summary>'
    details = ''
    for item in info:
      # These lists contain only dicts.
      assert isinstance(item, dict), f'{type(item)} is not dict'
      details += dict_to_html(item, section)
    return f'<details>{summary}{details}</details>'

  # All other lists
  # ---------------
  list_type = ' Course Area ' if is_area else ' '
  num = len(info)
  if num == 0:
    return '<p class="error">Empty{list_type}List</p>'

  # Simplified handling when the list has only one element
  if num == 1 and not is_area:
    return to_html(info[0])

  # The list has more than one element
  # If any items are dicts with only a remark key, extract them and show them before the details
  # element for the list.
  opening_remarks = ''
  remarkable_items = [item for item in info if isinstance(item, dict) and 'remark' in item.keys()]
  for remarkable_item in remarkable_items:
    if len(remarkable_item.keys()) == 1:
      index = info.index(remarkable_item)
      remark = remarkable_item.pop('remark')
      opening_remarks += f'<p><strong>{remark}</strong></p>'
      info.pop(index)

  num = len(info)
  if num == 0:
    # The list consisted only of remarks
    return f'{opening_remarks}'

  suffix = '' if num == 1 else 's'
  list_type = 'Course Area' if is_area else 'Item'
  if num <= len(number_names):
    num_str = number_names[num].title()
  else:
    num_str = f'{num:,}'

  return_str = (f'{opening_remarks}<details open="open"/>'
                f'<summary>{num_str} {list_type}{suffix}</summary>')
  return_str += '\n'.join([f'{to_html(element)}'for element in info])

  return return_str + '</details>'


# to_html()
# -------------------------------------------------------------------------------------------------
def to_html(info: any) -> str:
  """  Return a nested HTML data structure as described above.
  """
  if DEBUG:
    print(f'*** to_html({type(info)}, {section=})', file=sys.stderr)

  if info is None:
    return ''
  if isinstance(info, bool):
    return 'True' if info else 'False'
  if isinstance(info, list):
    return list_to_html(info)
  if isinstance(info, dict):
    return dict_to_html(info)

  return info
