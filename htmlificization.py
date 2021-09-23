#! /usr/local/bin/python3
"""
    Convert a scribe block and it (json-encoded) parsed representation into a web page.

    The json-encoded lists and dicts produced by the dgw_interpreter can be nested within one
    another to any depth.

    Everything is presented as HTML details elements, with the label of a dict being the
    summary element. Subsets, Groups, Conditionals, and course lists are handles specially.

"""

import os
import sys
import csv
import argparse

from pprint import pprint
from collections import namedtuple

from course_lookup import lookup_course

from body_qualifiers import format_body_qualifiers, \
    _format_share as format_share, \
    _format_maxperdisc as format_maxperdisc
from quarantine_manager import QuarantineManager
from dgw_parser import dgw_parser, catalog_years
from pgconnection import PgConnection

DEBUG = os.getenv('DEBUG_HTML')

# Module Initialization
# =================================================================================================

# Dict of CUNY college names
conn = PgConnection()
cursor = conn.cursor()
cursor.execute('select code, name from cuny_institutions')
college_names = {row.code: row.name for row in cursor.fetchall()}
conn.close()

# Dict of quarantined requirement_blocks
quarantined_dict = QuarantineManager()

number_names = ['none', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve']


# list_of_courses()
# -------------------------------------------------------------------------------------------------
def list_of_courses(course_tuples: list, title_str: str, highlight=False) -> str:
  """ This is called from course_list_details to format scribed, missing, active, inactive, include,
      and except course lists into a HTML unordered list element inside the body of a details
      element, where the title_str received is used as the summary element. The title string
      normally specifies how many courses from the list are required.

      Highlight the summary if highlight is True, namely for missing courses.

      There are two flavors of course_tuples:
      - scribed and missing courses have just the discipline and catalog number, and an optional
        with clause, so the length of those tuples is 3
      - active and inactive courses have the course_id, offer_nbr, discipline, catalog_number,
        title, credits, and optional with clause, so the length of those tuples is 7.
  """
  if DEBUG:
    print(f'*** list_of_courses({len(course_tuples)} course tuples, {title_str} {highlight=})', file=sys.stderr)

  suffix = '' if len(course_tuples) == 1 else 's'
  class_str = ' class="error"' if highlight else ''
  return_str = (f'<details><summary{class_str}>{len(course_tuples)} {title_str}{suffix}</summary>'
                f'<ul>')
  for course_tuple in course_tuples:
    assert len(course_tuple) == 3 or len(course_tuple) == 7, \
        f'{len(course_tuple)} is not three or six'
    if len(course_tuple) < 4:  # Scribed is 3 (possible 'with'); except and including are 2
      return_str += f'<li>{course_tuple[0]} {course_tuple[1]}'
      if course_tuple[2] is not None:
        return_str += f' with {course_tuple[2]}'
      return_str += '</li>\n'
    else:
      return_str += (f'<li>{course_tuple[2]} {course_tuple[3]}: <em>{course_tuple[4]}</em>')
      if course_tuple[-1] is not None:
         return_str += f' <strong>with {course_tuple[-1]}</strong>'
      return_str += '</li>'
  return_str += '</ul>\n</details>'
  return return_str


# class_credit_to_str()
# -------------------------------------------------------------------------------------------------
def class_credit_to_str(min_classes: int, max_classes: int,
                        min_credits: float, max_credits: float, conjunction: str) -> str:
  """ Tell how many classes and/or credits are required.
  """
  if DEBUG:
    print(f'*** class_credit_to_str({min_classes=}, {max_classes=}, {min_credits=}, '
          f'{max_credits=}, {conjunction=})', file=sys.stderr)

  if min_classes:
    if min_classes == max_classes:
      suffix = '' if min_classes == 1 else 'es'
      num_classes = f'{min_classes} class{suffix}'
    else:
      num_classes = f'between {min_classes} and {max_classes} classes'
  else:
    num_classes = ''
  if min_credits:
    if min_credits == max_credits:
      suffix = '' if min_credits == 1.0 else 's'
      num_credits = f'{min_credits} credit{suffix}'
    else:
      num_credits = f'between {min_credits} and {max_credits} credits'
  else:
    num_credits = ''

  if num_credits and num_classes:
    class_credit_str = f'{num_classes} {conjunction.lower()} {num_credits}'
  else:
    # Possibly empty string
    class_credit_str = f'{num_classes}{num_credits}'

  if DEBUG:
    print(f'    returning “{class_credit_str}”', file=sys.stderr)

  return class_credit_str


# course_list_details()
# -------------------------------------------------------------------------------------------------
def course_list_details(info: dict) -> str:
  """ The dict for a course_list must have a scribed_courses list, and should have an
      active_courses list. After that, there might be include and except lists, and possibly a
      missing (from CUNYfirst) list.

      Returns a string representing the course list, suitable for use as the body of a HTML details
      element. If a non-empty label is found, a complete details element is returned with the label
      as the element’s summary.
  """
  if DEBUG:
    print(f'*** course_list_details({info.keys()})', file=sys.stderr)

  details_str = ''

  try:
    label = info.pop('label')
    if label is None:
      raise KeyError
    label_str = label
  except KeyError as ke:
    label_str = ''

  list_type = info.pop('list_type')

  try:
    scribed_courses = info.pop('scribed_courses')
    assert isinstance(scribed_courses, list)
    scribed_text = ''.join([str(sc) for sc in scribed_courses])
    if len(scribed_courses) > 1 or ':' in scribed_text or '@' in scribed_text:
      if list_type == 'OR':
        if len(scribed_courses) == 2:
          details_str += f'<p>Either of these courses</p>'
        else:
          details_str += f'<p>Any of these courses</p>'
      else:
        details_str += f'<p>All of these courses</p>'

    details_str += list_of_courses(scribed_courses, 'Scribed Course')
  except KeyError as ke:
    details_str = f"""<p class="error">
                       <em>course_list_details() with no scribed courses!</em></p>
                       <p><strong>Keys:</strong> {course_list.keys()}</p>
                  """

  try:
    qualifiers = info.pop('qualifiers')
    if qualifiers is not None and len(qualifiers) > 0:
      details_str += to_html(qualifiers)
  except KeyError as ke:
    pass

  try:
    active_courses = info.pop('active_courses')
    assert isinstance(active_courses, list)
    if len(active_courses) == 0:
      details_str += '<div class="error">No Active Courses!</div>'
    else:
      attributes_str = ''
      try:
        attributes = info['attributes ']
        if attributes is not None:
          attributes_str = ','.join(attributes)
      except KeyError as ke:
        pass
      details_str += list_of_courses(active_courses, f'Active {attributes_str}Course')

    course_areas = info.pop('course_areas')
    if len(course_areas) > 0:
      details_str += list_to_html_list_element(course_areas, kind='Course Area')

    include_courses = info.pop('include_courses')
    assert isinstance(include_courses, list)
    if len(include_courses) > 0:
      details_str += list_of_courses(include_courses, 'Must-include Course')

    except_courses = info.pop('except_courses')
    assert isinstance(except_courses, list)
    if len(except_courses) > 0:
      details_str += list_of_courses(except_courses, 'Except Course')

    inactive_courses = info.pop('inactive_courses')
    assert isinstance(inactive_courses, list)
    if len(inactive_courses) > 0:
      details_str += list_of_courses(inactive_courses, 'Inactive Course')

    missing_courses = info.pop('missing_courses')
    assert isinstance(missing_courses, list)
    if len(missing_courses) > 0:
      details_str += list_of_courses(missing_courses, 'Not-Found-in-CUNYfirst Course',
                                     highlight=True)
  except KeyError as ke:
    print(f'Invalid Course List: missing key is {ke}', file=sys.stderr)
    pprint(info, stream=sys.stderr)

  # Class/Credit info, if present
  if 'conjunction' in info.keys():
    conjunction = info.pop('conjunction')
  else:
    conjunction = None
  if 'min_classes' in info.keys():
    min_classes = info.pop('min_classes')
    max_classes = info.pop('max_classes')
  else:
    min_classes = max_classes = None
  if 'min_credits' in info.keys():
    min_credits = info.pop('min_credits')
    max_credits = info.pop('max_credits')
  else:
    min_credits = max_credits = None

  requirements_str = class_credit_to_str(min_classes, max_classes,
                                         min_credits, max_credits, conjunction)
  if label_str and requirements_str:
    label_str = f'{requirements_str} in {label_str}'
  else:
    # Could be one, the other, or neither
    label_str = f'{requirements_str}{label_str}'

  # Any additional information
  for key, value in info.items():
    if isinstance(value, list):
      if len(value) > 0:
        details_str += list_to_html_list_element(value, kind=key.strip('s').title())
    else:
      details_str += f'<p>{key}: {value}</p>'

  # if DEBUG:
  #   print(f'    returning [{label_str=} {details_str=}]', file=sys.stderr)

  return (label_str, details_str)


# requirement_to_details_element()
# -------------------------------------------------------------------------------------------------
def requirement_to_details_element(requirement: dict) -> str:
  """ This starts as class_credit_body in the grammar; dgw_parser has turned it into a list of
      dicts. This method interprets one element of that list.
      If there is a label, return a full details element with the label as the summary. Otherwise,
      just return the HTML that will make up the body of an enclosing details element.
      Keys: allow_classes, allow_credits, conjunction, course_list, is_pseudo, label, num_classes,
            num_credits.
      Ignoring allow_classes and allow_credits: they are audit controls.
  """
  if DEBUG:
    print(f'*** requirement_to_details_element({list(requirement.keys())})', file=sys.stderr)
  try:
    label = requirement.pop('label')
    if not label:
      raise KeyError
    outer_label_str = label
  except KeyError as ke:
    outer_label_str = ''

  requirement_list = []
  if 'is_pseudo' in requirement.keys() and requirement['is_pseudo']:
    requirement_list.append('<p>This requirement does not have a strict credit limit.</p>')

  if 'min_classes' in requirement.keys():
    min_classes = requirement.pop('min_classes')
    max_classes = requirement.pop('max_classes')
  else:
    min_classes = max_classes = None
  if 'min_credits' in requirement.keys():
    min_credits = requirement.pop('min_credits')
    max_credits = requirement.pop('max_credits')
  else:
    min_credits = max_credits = None

  assert min_credits or min_classes

  conjunction = requirement.pop('conjunction')
  if conjunction is None:
    conjunction = '?'

  requirements_str = class_credit_to_str(min_classes, max_classes,
                                         min_credits, max_credits, conjunction)

  # If nothing else, expect a list of courses for the requirement
  try:
    if DEBUG:
      print('    From requirement_to_details_element()', file=sys.stderr)
    inner_label_str, course_str = course_list_details(requirement.pop('course_list'))
  except KeyError as ke:
    inner_label_str = course_str = ''

  # Not expecting both inner and outer labels; combine if present
  # if DEBUG:
  #   print(f'    returning <details><summary>{requirements_str} in '
  #         f'{inner_label_str}{outer_label_str}</summary>'
  #         f'[{course_str}]</details>', file=sys.stderr)
  return (f'<details><summary>{requirements_str} in {inner_label_str}{outer_label_str}</summary>'
          f'{course_str}</details>')


# subset_to_details_element()
# -------------------------------------------------------------------------------------------------
def subset_to_details_element(info: dict, outer_label) -> str:
  """  The dict for a subset:
        subset    : BEGINSUB
                  ( conditional_body
                    | block
                    | blocktype
                    | class_credit_body
                    | copy_rules
                    | course_list
                    | group
                    | noncourse
                    | rule_complete
                  )+
                  ENDSUB qualifier* (remark | label)*;

      If there is a remark, it goes right after the summary (inner label)
      Then any qualifiers.
      Then all the other items. Note that dgw_parser() has renamed class_credit_body as
      'requirements', which gets listed last as “courses.”

       There are four possibilities for labels: outer, inner, both, or neither (really?). If both,
       return the inner part nested inside a details element with the outer label as its summary
  """
  if DEBUG:
    print(f'*** subset_to_details_element({list(info.keys())}, {outer_label=})', file=sys.stderr)

  try:
    inner_label = info.pop('label')
  except KeyError as ke:
    inner_label = None

  if outer_label is None and inner_label is None:
    print(f'*** Subset with no label\n{info}', file=sys.stderr)

  try:
    remark = info.pop('remark')
    remark_str = f'<p>{remark}</p>'
  except KeyError as ke:
    remark_str = ''

  qualifier_strings = format_body_qualifiers(info)
  qualifiers_str = ''
  for qualifier_string in qualifier_strings:
    class_attribute = ' class="error"' if 'Error:' in qualifier_string else ''
    qualifiers_str += f'<p{class_attribute}>{qualifier_string}</p>'

  # Is there a list of course requirements?
  if 'requirements' in info.keys():
    course_requirements = info.pop('requirements')
    num_requirements = len(course_requirements)
    # Remarks aren’t requirements, but we show them anyway to provide context.
    for requirement in course_requirements:
      if 'remark' in requirement.keys():
        num_requirements -= 1
    suffix = '' if len(course_requirements) == 1 else 's'
    course_requirements_summary = (f'<summary>{len(course_requirements)} '
                                   f'Requirement{suffix}</summary>')
    course_requirements_body = ''.join([requirement_to_details_element(course_requirement)
                                        for course_requirement in course_requirements])
    course_requirements_element = (f'<details>{course_requirements_summary}'
                                   f'{course_requirements_body}</details>')
  else:
    course_requirements_element = ''

  # Are there any group requirements?
  if 'group_requirements' in info.keys():
    for group_requirement in info['group_requirements']:
      course_requirements_element += group_requirement_to_details_elements(group_requirement)

  # Remaining keys are info to appear before the course/group requirements

  if DEBUG and len(info.keys()):
    print(f'    Keys being passed to to_html() in subset_to_details_element: {list(info.keys())}',
          file=sys.stderr)

  details_str = ''.join([to_html(info[key]) for key in info.keys()])

  requirements_str = f'{remark_str}{qualifiers_str}{details_str}{course_requirements_element}'
  if len(requirements_str) == 0:
    requirements_str += '<p class="error">Error: No Requirements! 324</p>'

  # Here we deal with the four inner/outer label possibilities
  if outer_label and inner_label:
    summary = f'<summary>{outer_label}</summary'
    body = f'<details><summary>{inner_label}</summary>{requirements_str}</details>'
  elif outer_label and not inner_label:
    summary = f'<summary>{outer_label}</summary>'
    body = requirements_str
  elif not outer_label and inner_label:
    summary = f'<summary>{inner_label}</summary>'
    body = requirements_str
  else:
    summary = 'Unnamed Requirement'
    body = requirements_str

  return f'<details>{summary}{body}</details>'


# group_requirement_to_details_elements()
# -------------------------------------------------------------------------------------------------
def group_requirement_to_details_elements(info: dict, outer_label=None) -> str:
  """
      Returns a details element for each dict in the info list.
      The summary for each group is the label; the body starts with a paragraph that tells how many
      group items are required, and how many group items there are, followed by the html for each
      group item.
  """
  if DEBUG:
    print(f'*** group_requirement_to_details_elements({list(info.keys())}, '
          f'{outer_label=})', file=sys.stderr)
  assert isinstance(info, dict), f'{info} is not a dict'

  group_requirement = info.pop('group_requirement')
  return_str = ''
  num_required = int(group_requirement['number'])
  if num_required < len(number_names):
    num_required = number_names[num_required]
  group_list = group_requirement['group_list']
  assert isinstance(group_list, dict)
  num_groups = len(group_list['groups'])
  num_groups_suffix = '' if num_groups == 1 else 's'
  if num_groups < len(number_names):
    num_groups = number_names[num_groups]
  if num_required == 'one':
    if num_groups == 'one':
      requirement_str = '<p>The following group'
    elif num_groups == 'two':
      requirement_str = '<p>Either of the following two groups'
    else:
      requirement_str = f'<p>One of the following {num_groups} groups'
  else:
    requirement_str = f'<p>Any {num_required} of the following {num_groups} groups'
  label_str = group_requirement['label'].title()

  try:
    qualifiers = ''.join(f'<p>{q}</p>' for q in group_requirement['qualifiers'])
  except KeyError as ke:
    qualifiers = ''

  summary = f'<summary>{label_str}</summary>'
  body = requirement_str + qualifiers

  # Each group gets its own details element telling which group it is
  group_number = 0
  for group_item in group_list['groups']:
    group_number += 1
    if isinstance(group_item, list):
      group_body = list_to_html_list_element(group_item)
    elif isinstance(group_item, dict):
      group_body = dict_to_html_details_element(group_item)
    else:
      group_body = f'<div class="error">Error: {group_item} is neither a list nor a dict</div>'
    index = number_names[group_number] if group_number < len(number_names) else group_number
    body += f"""
    <details>
      <summary>Group {index} of {num_groups} group{num_groups_suffix}</summary>
      {group_body}
    </details>
    """
  return_str += f'<details open="open">{summary}{body}</details>'
  return return_str


# conditional_to_details_element()
# -------------------------------------------------------------------------------------------------
def conditional_to_details_element(info: dict, outer_label: str) -> str:
  """  The dict for a conditional construct must have a condition, which becomes the summary of the
       html details element. The optional label goes next, followed by nested details elements for
       the true and the optional false branches.

       There are four possibilities for labels: outer, inner, both, or neither (really?). If both,
       return the parts nested inside a details element with the outer summary
  """
  if DEBUG:
    print(f'*** conditional_to_details_element({list(info.keys())}, {outer_label=})',
          file=sys.stderr)

  try:
    condition = info.pop('condition')
  except KeyError as ke:
    condition = '(Missing Condition)'

  try:
    inner_label = info.pop('label')
  except KeyError as ke:
    inner_label = None

  try:
    true_value = to_html(info['if_true'])
    if_true_part = (f'<details open="open"><summary>if ({condition}) is true</summary>'
                    f'{true_value}</details>')
  except KeyError as ke:
    if_true_part = '<p class="error">Empty If-then rule!</p>'

  try:
    false_value = to_html(info['if_false'])
    if_false_part = (f'<details open="open"><summary>if ({condition}) is not true</summary>'
                     f'{false_value}</details>')
  except KeyError as ke:
    if_false_part = ''  # Else is optional

  if inner_label:
    inner_details = (f'<details><summary open="open">{inner_label.title()}</summary'
                     f'{if_true_part}{if_false_part}</details>')

    # Return one of the four possibilities
    if outer_label is None:
      return inner_details
    else:
      return (f'<details><summary open="open"><summary{outer_label.title()}</summary>'
              f'<details>{inner_details}</details>')
  else:
    inner_details = f'{if_true_part}{if_false_part}'
    if outer_label is None:
      return inner_details
    else:
      return (f'<details><summary open="open"><summary{outer_label.title()}</summary>'
              f'{inner_details}</details>')


# dict_to_html_details_element()
# -------------------------------------------------------------------------------------------------
def dict_to_html_details_element(info: dict) -> str:
  """ Convert a Python dict to a HTML <details> element. The <summary> element is based on the
      tag/label fields of the dict. During development, the context path goes next. Then, if there
      are remark or display fields, they go after that. If the tag starts with "num_", that
      value comes next. Then everything else.

      There are two scenarios: a single key with a dict as its value, or multiple keys (with any
      type of value, including dicts).
        Case 1: If there is a single key, that’s the summary element.
        Case 2: If there are multiple keys, use the label as the summary element. But if there is no
        label, this isn’t a details-worthy item, and just return the fields for use in the body
        of the parent.
  """

  if DEBUG:
      print(f'*** dict_to_html_details_element({list(info.keys())})', file=sys.stderr)

  # Indicator for not returning a nest-able display element
  label = None
  try:
    label = info.pop('label')
  except KeyError as ke:
    pass

  keys = info.keys()

  if len(keys) == 1:
    # If there is a single key, see if it is group, subset, conditional, or naked course list,
    # and special-case if so
    key = list(info)[0]
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
      label_str, course_list = course_list_details(info.pop('course_list'))
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

    # Also special-casing qualifiers to be consistent between header rules and body qualifiers.
    elif key == 'share':
      return f'<p>{format_share(info[key])}</p>'
    elif key == 'maxperdisc':
      return f'<p>{format_maxperdisc(info[key])}</p>'

    # Not special-case, but just a single key
    if label is None:
      summary = f'<summary>{key.replace("_", " ").title()}</summary>'
    else:
      summary = f'<summary>{label.title()}</summary>'
    value = info[key]
    if isinstance(value, dict):
      return f'<details>{summary}{dict_to_html_details_element(value)}</details>'
    elif isinstance(value, list):
      return f'<details>{summary}{list_to_html_list_element(value)}</details>'
    else:
      return f'<details>{summary}{to_html(value)}</details>'

  else:
    # Multple keys
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

    try:
      rule_complete_dict = info.pop('rule_complete')
      rule_complete_value = 'complete' if rule_complete_dict['is_complete'] else 'not complete'
      if 'label' in rule_complete_dict.keys():
        label_str = rule_complete['label']
      else:
        label_str = ''
      rule_complete = f'<p>{label_str}: Rule is {rule_complete_value}</p>'

      display = f'<p><em>{display}</em></p>'
    except KeyError as ke:
      rule_complete = ''

    # Class lists and their qualifiers.
    try:
      # Determing number of classes and/or credits required
      min_classes = info.pop('min_classes')
      max_classes = info.pop('max_classes')
      min_credits = info.pop('min_credits')
      max_credits = info.pop('max_credits')
      conjunction = info.pop('conjunction')
      cr_str = class_credit_to_str(min_classes, max_classes, min_credits, max_credits, conjunction)
      if cr_str:
        cr_str = f'<p>{cr_str}</p>'
    except KeyError as ke:
      cr_str = ''

    qualifier_strings = format_body_qualifiers(info)
    for qualifier_string in qualifier_strings:
      class_attribute = ' class="error"' if 'Error:' in qualifier_string else ''
      cr_str += f'<p{class_attribute}>{qualifier_string}</p>'

    # Other min, max, and num items
    numerics = cr_str
    keys = list(info.keys())
    for key in keys:
      if key[0:3].lower() in ['max', 'min', 'num']:
        value = info.pop(key)
        if value is not None:
          numerics += f'<p><strong>{key.replace("_", " ").title()}: </strong>{value}</p>'

    # course_list part of a multi-key dict
    course_list = ''
    if 'course_list' in info.keys():
      if DEBUG:
        print('    From dict_to_html_details_element()')
      label_str, course_list = course_list_details(info.pop('course_list'))
      # If there is a non-empty label, use it as the summary of a complete details element
      if label_str:
        course_list = f'<details><summary>{label_str}</summary>{course_list}</details>'

    # Development aid
    context_path = ''
    if DEBUG:
      try:
        context_path = f'<div>Context: {info.pop("context_path")}</div>'
      except KeyError as ke:
        pass

    return_str = (f'{pseudo_msg}{context_path}{remark}{display}{numerics}{course_list}'
                  f'{rule_complete}')

    # Key-value pairs not specific to course lists
    # --------------------------------------------
    for key, value in info.items():
      if value is None:
        continue  # Omit empty fields

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
              return_str += (f'<div>{key_str}: between {range_floor:0.1f} and '
                             f'{range_ceil:0.1f}</div>')
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
              return_str += f'<div>{key_str}: {float(value):0.1f}</div>'

        except ValueError as ve:
          # Not a numeric string; just show the text.
          if key != 'context_path':  # This was for development purposes
            return_str += f'<div>{key_str}: {value}</div>'

      else:
        # Fall through
        return_str += to_html(value)

    if label is None:
      return return_str
    else:
      return f'<details><summary>{label}</summary>{return_str}</details>'


# list_to_html_list_element()
# -------------------------------------------------------------------------------------------------
def list_to_html_list_element(info: list, kind='Item') -> str:
  """
  """
  if DEBUG:
    print(f'*** list_to_html_list_element({len(info)} elements, {kind=})', file=sys.stderr)

  num = len(info)
  if num == 0:
    return '<p class="error">Empty List</p>'
  if num == 1:
    return to_html(info[0], kind)

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

  # for unremarkable_item in info:
  if num <= len(number_names):
    num_str = number_names[num].title()
  else:
    num_str = f'{num:,}'
  # Pluralization awkwardness
  if kind == 'Property':
    kind = 'Properties'
  else:
    kind = kind + 's'
  return_str = f'{opening_remarks}<details open="open"/><summary>{num_str} {kind}</summary>'
  return_str += '\n'.join([f'{to_html(element)}'for element in info])
  return return_str + '</details>'


# to_html()
# -------------------------------------------------------------------------------------------------
def to_html(info: any, kind='Item') -> str:
  """  Return a nested HTML data structure as described above.
  """
  if DEBUG:
    print(f'*** to_html({type(info)}, {kind=})', file=sys.stderr)

  if info is None:
    return ''
  if isinstance(info, bool):
    return 'True' if info else 'False'
  if isinstance(info, list):
    return list_to_html_list_element(info, kind)
  if isinstance(info, dict):
    return dict_to_html_details_element(info)

  return info


# scribe_block_to_html()
# -------------------------------------------------------------------------------------------------
def scribe_block_to_html(row: tuple, period_range='current') -> str:
  """ Generate html for the scribe block and interpreted head and body lists objects, unless the
      block has been quarantined.
  """
  if DEBUG:
    print(f'*** scribe_block_to_html({row}, {period_range=})', file=sys.stderr)

  if row.requirement_html == 'Not Available':
    return ('<h1 class="error">This scribe block is not available.</h1>'
            '<p><em>Should not occur.</em></p>')

  catalog_type, first_year, last_year, catalog_years_text = catalog_years(row.period_start,
                                                                          row.period_stop)
  college_name = college_names[row.institution]
  disclaimer = """
  <div class="disclaimer">
    <p class="warning">
      This is project is in the “beta” stage. That means that the display below
      <em>should</em> be an an accurate representation of the requirements for this block,
      omitting elements that would depend an individual student’s academic record, such as Proxy
      Advice. But there may be errors and omissions. If you see such anomalies, I would
      appreciate hearing about them. (<em>Click on my name for an email link.</em>)
    </p>
    <p>
      <em>Thanks</em>,<br>
      <a href="mailto:cvickery@qc.cuny.edu?subject=DGW Report"
         class="signature">Christopher Vickery</a>
    </p>
  </div>
  """
  # Interpret the block if it hasn’t been done yet.
  if row.parse_tree == {}:
    parse_tree = dgw_parser(row.institution,
                            row.block_type,
                            row.block_value,
                            period_range=period_range)
  else:
    parse_tree = row.parse_tree

  if 'error' in parse_tree.keys():
    err_msg = parse_tree['error']
    parse_results = f'<section><h2 class="error">Parsing failed</h2><p>{err_msg}</p></section'
  else:
    header_list, body_list = parse_tree['header_list'], parse_tree['body_list']
    parse_results = f"""
  <section>
  <details><summary>Header</summary>
    {to_html(header_list)}
  </details>
  <details><summary>Body</summary>
    {to_html(body_list, kind='Requirement')}
  </details
</section>
    """

  return disclaimer + f"""
  <h1>{college_name} {row.requirement_id}: <em>{row.title}</em></h1>
  <p>Requirements for {catalog_type} Catalog Years {catalog_years_text}</p>
  <section>{row.requirement_html}</section>
  {parse_results}
  """


# __main__
# =================================================================================================
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-np', '--progress', action='store_false')
  parser.add_argument('-p', '--period', choices=['all', 'current', 'latest'], default='current')
  parser.add_argument('-q', '--do_quarantined', action='store_true')
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-ti', '--timelimit', type=int, default=30)
  parser.add_argument('-u', '--update_db', action='store_true')

  # Parse args
  args = parser.parse_args()
  if args.requirement_id:
    institution = args.institutions[0].strip('10').upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')
    requirement_id = f'RA{int(requirement_id):06}'

    if args.progress:
      print(f'{institution} {requirement_id} {args.period}', end='')
      sys.stdout.flush()
    parse_tree = dgw_parser(institution,
                            'block_type',   # Not used with requirement_id
                            'block_value',  # Not used with requirement_id
                            period_range=args.period,
                            progress=args.progress,
                            update_db=args.update_db,
                            requirement_id=requirement_id,
                            do_quarantined=args.do_quarantined,
                            timelimit=args.timelimit)
    # When not updating the db (i.e., during debugging), display the result as a web page.
    if not args.update_db:
      if 'error' in parse_tree.keys():
        err_msg = parse_tree['error']
        html = f'<h1 class="error">Error: {err_msg}</h1>'
      else:
        html = ''
      if DEBUG:
        print('HEADER', file=sys.stderr)
      html += to_html(parse_tree['header_list'])
      if DEBUG:
          print('BODY', file=sys.stderr)
      html += to_html(parse_tree['body_list'])
      print(html)

    exit()
  else:
    exit('Only RA option supported.')
