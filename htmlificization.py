#! /usr/local/bin/python3
"""
    Generate HTML representation of nested lists/dicts.

    Lists and dicts can be nested within one another to any depth.

    Everything is presented as HTML details elements, with the summary element being either the
    label for the dict, the name of the first key in the dict, or the length of the item,
    in that priority order.

"""

import os
import sys

from course_lookup import lookup_course

from dgw_interpreter import dgw_interpreter

DEBUG = os.getenv('DEBUG_HTML')

quarantine_dict = {}
with open('/Users/vickery/Projects/dgw_processor/testing/quarantine_list') as ql_file:
  quarantine_list = ql_file.readlines()
  for line in quarantine_list:
    if line[0] == '#':
      continue
    body, ellucian = line.split('::')
    ellucian = 'y' in ellucian or 'Y' in ellucian
    college, requirement_id, *explanation = body.split(' ')
    explanation = ' '.join(explanation).strip()

    quarantine_dict[(college, requirement_id)] = (explanation.strip('.'), ellucian)


# list_of_courses()
# -------------------------------------------------------------------------------------------------
def list_of_courses(course_tuples: list, title_str: str, highlight=False) -> str:
  """ This is called from course_list_to_details_element to format scribed, missing, active,
      inactive, include, and except course lists into a HTML unordered list element inside the body
      of a details element, where the title_str received is used as the summary element. The title
      string normally specifies how many courses from the list are required.

      Highlight the summary if highlight is True, namely for missing courses.

      There are two flavors of course_tuples:
      - scribed and missing courses have just the discipline and catalog number, and an optional
        with clause, so the length of those tuples is 3
      - active and inactive courses have the course_id, offer_nbr, discipline, catalog_number,
        title, and optional with clause, so the length of those tuples is 6.
  """
  suffix = '' if len(course_tuples) == 1 else 's'
  class_str = ' class="error"' if highlight else ''
  return_str = (f'<details><summary{class_str}>{len(course_tuples)} {title_str}{suffix}</summary>'
                f'<ul>')
  for course_tuple in course_tuples:
    assert len(course_tuple) == 3 or len(course_tuple) == 6, \
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


# course_list_to_details_element()
# -------------------------------------------------------------------------------------------------
def course_list_to_details_element(info: dict, num_required='Unknown Number of') -> str:
  """  The dict for a course_list must have a scribed_courses list, and should have an
       active_courses list. After that, there might be include and except lists, and possibly a
       missing (from CUNYfirst) list. The label becomes the summary for the details element.
       Note: the course_list tag itself was removed by dict_to_html_details before calling this
       method.
  """
  return_str = ''
  # if key in ['attributes', 'qualifiers']:  # Handled by active_courses and scribed_courses
  #   continue

  try:
    label = info.pop('label')
    if label is None:
      label = 'Empty Label'
  except KeyError as ke:
    label = 'Missing Label'
  suffix = '' if num_required == '1' else 's'
  return_str = f'<details><summary>{num_required} Course{suffix} in {label.title()}</summary>'

  try:
    value = info.pop('list_type')
    if value is None:
      pass
    else:
      return_str += f'<p>This is an {value} list.</p>'
  except KeyError as ke:
    pass

  try:
    scribed_courses = info.pop('scribed_courses')
    assert isinstance(scribed_courses, list)
    return_str += list_of_courses(scribed_courses, 'Scribed Course')
  except KeyError as ke:
    return_str = f"""<p class="error">
                       <em>course_list_to_details_element() with no scribed courses!</em></p>
                       <p><strong>Context:</strong> {context_path(info)}</p>
                  """

  try:
    qualifiers = info.pop('qualifiers')
    if qualifiers is not None and len(qualifiers) > 0:
      return_str += to_html(qualifiers)
  except KeyError as ke:
    pass

  try:
    active_courses = info.pop('active_courses')
    assert isinstance(active_courses, list)
    if len(active_courses) == 0:
      return_str += '<div class="error">No Active Courses!</div>'
    else:
      attributes_str = ''
      try:
        attributes = info['attributes']
        if attributes is not None:
          attributes_str = ','.join(attributes)
      except KeyError as ke:
        pass
      return_str += list_of_courses(active_courses, f'Active {attributes_str} Course')
  except KeyError as ke:
    return_str = f"""<p class="error">
                       <em>course_list_to_details_element() with no active_courses tag!</em></p>
                       <p><strong>Context:</strong> {context_path(info)}</p>
                  """

  course_areas = info.pop('course_areas')
  if len(course_areas) > 0:
    return_str += list_to_html_list_element(course_areas, kind='Course Area')

  include_courses = info.pop('include_courses')
  assert isinstance(include_courses, list)
  if len(include_courses) > 0:
    return_str += list_of_courses(include_courses, 'Must-include Course')

  except_courses = info.pop('except_courses')
  assert isinstance(except_courses, list)
  if len(except_courses) > 0:
    return_str += list_of_courses(except_courses, 'Except Course')

  inactive_courses = info.pop('inactive_courses')
  assert isinstance(inactive_courses, list)
  if len(inactive_courses) > 0:
    return_str += list_of_courses(inactive_courses, 'Inactive Course')

  missing_courses = info.pop('missing_courses')
  assert isinstance(missing_courses, list)
  if len(missing_courses) > 0:
    return_str += list_of_courses(missing_courses,
                                  'Not-Found-in-CUNYfirst Course', highlight=True)

  # Any additional information
  for key, value in info.items():
    # if key == 'context_path':
    #   continue
    if isinstance(value, list):
      if len(value) > 0:
        return_str += list_to_html_list_element(value, kind=key.strip('s').title())
    else:
      return_str += f'<p><strong>{key}:</strong> {value}</p>'

  return return_str + '</details>'


# conditional_to_details_element()
# -------------------------------------------------------------------------------------------------
def conditional_to_details_element(info: dict) -> str:
  """  The dict for a conditional construct must have a condition, which becomes the summary of the
       html details element. The optional label goes next, followed by nested details elements for
       the true and the optional false branches.
       Note: the conditional tag itself was removed by dict_to_html_details before calling this
       method.
  """

  try:
    condition = info['condition']
  except KeyError as ke:
    condition = '(Missing Condition)'

  try:
    label = f"""“{info['label'].strip('"')}”"""
  except KeyError as ke:
    label = None

  try:
    true_value = to_html(info['if_true'], kind='If-true Item')
    if_true_part = (f"<details><summary>if {condition} is true</summary>"
                    f"{true_value}</details>")
  except KeyError as ke:
    if_true_part = '<p class="error">Empty If-then rule!</p>'

  try:
    false_value = to_html(info['if_false'], kind='if-false Item')
    if_false_part = (f"<details><summary>if {condition} is not true</summary>"
                     f"{false_value}</details>")
  except KeyError as ke:
    if_false_part = ''  # Else is optional

  if label:
    # Produce a details element to hold the two legs
    return f'<details><summary>{label}</summary{if_true_part}{if_false_part}</details>'
  else:
    return f'{if_true_part}{if_false_part}'


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
        Case 2: If there are multiple keys, use the label as the summary element, or 'No Label' if
        there is none.
  """

  keys = info.keys()
  if len(keys) == 1:
    # Case 1
    key = list(info)[0]
    if key == 'conditional':  # Special case for conditional dicts
      return(conditional_to_details_element(info))

    # Not if-then
    summary = f'<summary>{key.replace("_", " ").title()}</summary>'
    value = info[key]
    if isinstance(value, dict):
      return f'<details>{summary}{dict_to_html_details_element(value)}</details>'
    elif isinstance(value, list):
      return f'<details>{summary}{list_to_html_list_element(value)}</details>'
    else:
      return f'<details>{summary}{to_html(value)}</details>'

  else:
    # Case 2
    try:
      label = info.pop('label')
      if label is not None:
        summary = f'<summary>{label}</summary>'
    except KeyError as ke:
        summary = f'<summary>No Label</summary>'

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

    # min, max, and num items
    numerics = ''
    keys = [key for key in info.keys()]
    for key in keys:
      if key[0:3].lower() in ['max', 'min', 'num']:
        value = info.pop(key)
        if value is not None:
          numerics += f'<p><strong>{key.replace("_", " ").title()}: </strong>{value}</p>'

    # courses?
    course_list = ''
    if 'course_list' in info.keys():
      num_required = 'Unknown'
      if 'num_courses_required' in info.keys():
        num_required = info.pop('num_courses_required')
      course_list = course_list_to_details_element(info.pop('course_list'), num_required=f'{num_required}')

    # Development aid
    context_path = ''
    if DEBUG:
      try:
        context_path = f'<div><strong>Context:</strong>{info.pop("context_path")}</div>'
      except KeyError as ke:
        pass

    return_str = (f'<details>{summary}{pseudo_msg}{context_path}{remark}{display}{numerics}'
                  f'{course_list}')

    for key, value in info.items():
      key_str = f'<strong>{key.replace("_", " ").title()}</strong>'

      # Key-value pairs not specific to course lists
      # --------------------------------------------
      if value is None:
        continue  # Omit empty fields

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
        # Fallthrough
        return_str += to_html(value)

    return return_str + '</details>'


# list_to_html_list_element()
# -------------------------------------------------------------------------------------------------
def list_to_html_list_element(info: list, kind='Requirement') -> str:
  """
  """
  num = len(info)
  if num == 0:
    return '<p class="error">Empty List</p>'
  elif num == 1:
    return to_html(info[0])
  else:
    if num <= 12:
      num_str = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
                 'Ten', 'Eleven', 'Twelve'][num]
    else:
      num_str = f'{num:,}'
    return_str = f'<details><summary>{num_str} {kind}s</summary>'
    return_str += '\n'.join([f'{to_html(element)}' for element in info])
    return return_str + '</details>'


# to_html()
# -------------------------------------------------------------------------------------------------
def to_html(info: any, kind='Requirement') -> str:
  """  Return a nested HTML data structure as described above.
  """
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
def scribe_block_to_html(row: tuple, period='all') -> str:
  """ Generate html for the scribe block and interpreted head and body lists objects, unless the
      block has been quarantined.
  """
  if row.requirement_html == 'Not Available':
    return '<h1>This scribe block is not available.</h1><p><em>Should not occur.</em></p>'

  if (row.institution, row.requirement_id) in quarantine_dict.keys():
    header_list, body_list = None, None
    explanation, ellucian = quarantine_dict[(row.institution, row.requirement_id)]
    if ellucian:
      qualifier = 'Although the Ellucian parser does not report an error,'
    else:
      qualifier = 'Neither the Ellucian parser nor'
    disclaimer = f"""
    <p class="disclaimer">
      <span class="error">
        {qualifier} this parser was unable to process this Scribe Block, with the following
        explanation:
      </span>
        “{explanation}.”
    </p>
    """
    return row.requirement_html + disclaimer

  else:
    disclaimer = """
    <div class="disclaimer">
      <p class="warning">
        This is project is now in the “beta” stage. That means that the display below
        <em>should</em> be an an accurate representation of the requirements for this block,
        omitting elements that would depend an individual student’s academic record, such as Proxy
        Advice. But there are undoubtedly errors and omissions. If you see such anomalies, I would
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
    if len(row.header_list) == 0 and len(row.body_list) == 0:
      header_list, body_list = dgw_interpreter(row.institution,
                                               row.block_type,
                                               row.block_value,
                                               period=period)
    else:
      header_list, body_list = row.header_list, row.body_list

    return row.requirement_html + disclaimer + f"""
    <section>
      <details><summary>Header</summary>
        {to_html(header_list)}
      </details>
      <details><summary>Body</summary>
        {to_html(body_list)}
      </details
    </section>
    """
