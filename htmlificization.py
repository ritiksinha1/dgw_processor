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

import os
import sys

from course_lookup import lookup_course

from dgw_interpreter import dgw_parser

DEBUG = os.getenv('DEBUG_HTML')

quarantine_dict = {}
with open('/Users/vickery/dgw_processor/testing/quarantine_list') as ql_file:
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
def list_of_courses(course_tuples, title_str, highlight=False):
  """ There are two flavors of course_tuples: scribed courses have just the discipline and catalog
      number, with an optional with clause, so the length of those tuples is 3. Otherwise, the
      tuple consists of the course_id, offer_nbr, discipline, catalog_number, and optional with
      clause.
  """
  suffix = '' if len(course_tuples) == 1 else 's'
  class_str = ' class="error"' if highlight else ''
  return_str = (f'<details><summary{class_str}>{len(course_tuples)} {title_str}{suffix}</summary>')
  for course_tuple in course_tuples:
    if len(course_tuple) == 3:
      return_str += f'<div>{course_tuple[0]} {course_tuple[1]}'
      if course_tuple[2] is not None:
        return_str += f' with {course_tuple[2]}'
      return_str += '</div>\n'
    else:
      return_str += (f'<details><summary>{course_tuple[2]} {course_tuple[3]}: '
                     f'<em>{course_tuple[4]}</em>')
      if course_tuple[5] is not None:
        return_str += f' with {course_tuple[5]}'
      return_str += '</summary>'
      return_str += f'{lookup_course(course_tuple[0], offer_nbr=course_tuple[1])[1]}</details>'
  return_str += '</details>\n'
  return return_str


# details()
# -------------------------------------------------------------------------------------------------
def details(info: dict) -> str:
  """
  """
  try:
    tag_name = info.pop('tag')
  except KeyError as ke:
    tag_name = 'unnamed'

  return_str = f'<details><summary>{tag_name}</summary>'

  if tag_name == 'course_list':
    # Hoo-boy, this is fun: we are going to do everything nice here: how many courses in each
    # of the three lists, and links to catalog descriptions for active courses, usw.
    try:

      label = info.pop('label')
      if label is not None:
        return_str += f'<h2>{label}</h2>'

      list_type = info.pop('list_type')
      if list_type != 'None':
        return_str += f'<p>This is an {list_type} list.</p>'

      scribed_courses = info.pop('scribed_courses')
      assert isinstance(scribed_courses, list)
      return_str += list_of_courses(scribed_courses, 'Scribed Course')

      attributes_str = ''
      attributes = info.pop('attributes')
      if attributes is not None:
        attributes_str = ','.join(attributes)

      active_courses = info.pop('active_courses')
      assert isinstance(active_courses, list)
      if len(active_courses) == 0:
        return_str += '<div class="error">No Active Courses!</div>'
      else:
        return_str += list_of_courses(active_courses, f'Active {attributes_str} Course')

      inactive_courses = info.pop('inactive_courses')
      assert isinstance(inactive_courses, list)
      if len(inactive_courses) > 0:
        return_str += list_of_courses(inactive_courses, 'Inactive Course')

      include_courses = info.pop('include_courses')
      assert isinstance(include_courses, list)
      if len(include_courses) > 0:
        return_str += list_of_courses(include_courses, 'Include Course')

      except_courses = info.pop('except_courses')
      assert isinstance(except_courses, list)
      if len(except_courses) > 0:
        return_str += list_of_courses(except_courses, 'Except Course')

      missing_courses = info.pop('missing_courses')
      if len(missing_courses) > 0:
        return_str += list_of_courses(missing_courses,
                                      'Not-Found-in-CUNYfirst Course', highlight=True)

      qualifiers = info.pop('qualifiers')
      if len(qualifiers) > 0:
        if DEBUG:
          print(f'{qualifiers=}', file=sys.stderr)
        return_str += '<details><summary>Qualifiers</summary>'
        return_str += '\n'.join([to_html(qualifier) for qualifier in qualifiers])
        return_str += '</details>'
      else:
        if DEBUG:
          print(f'No qualifiers: {info}', file=sys.stderr)

    except KeyError as ke:
      print(f'Missing course_list element in', info['context_path'])

    # There should be no keys left except for the context_path
    context_path = info.pop('context_path')
    if DEBUG:
      return_str += f'<strong>Context:</strong> {context_path}'

    for key, value in info.items():
      return_str += f'<dir>{key}: {info.keys()} <span class="error"> Not Interpreted.</span></dir>'

  else:
    for key, value in info.items():
      key_name = 'value' if key == 'number' else key

      if value is None:
        continue  # Omit empty fields

      if isinstance(value, bool):
        # Show booleans only if true
        if value:
          return_str += f'<div>{key_name}: {value}</div>'

      elif isinstance(value, str):
        try:
          # Interpret numeric and range strings
          if ':' in value and 2 == len(value.split(':')):
            # range of values: check if floats or ints
            range_floor, range_ceil = [float(v) for v in value.split(':')]
            if range_floor != int(range_floor) or range_ceil != int(range_ceil):
              return_str += (f'<div>{key_name}: between {range_floor:0.1f} and '
                             f'{range_ceil:0.1f}</div>')
            elif int(range_floor) != int(range_ceil):
              return_str += (f'<div>{key_name}: between {int(range_floor)} and '
                             f'{int(range_ceil)}</div>')
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
          # Not a numeric string; just show the text.
          return_str += f'<div>{value}</div>'

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
    num_str = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
               'Ten', 'Eleven', 'Twelve'][num]
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


# scribe_block_to_html()
# -------------------------------------------------------------------------------------------------
def scribe_block_to_html(row: tuple, period='all') -> str:
  """ Generate html for the scribe block and interpreted head and body lists objects.
  """
  if row.requirement_html == 'Not Available':
    return '<h1>This scribe block is not available.</h1><p><em>Should not occur.</em></p>'

  if (row.institution, row.requirement_id) in quarantine_dict.keys():
    explanation, ellucian = quarantine_dict[(row.institution, row.requirement_id)]
    print(f'{explanation=} {ellucian=}', file=sys.stderr)
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
  else:
   disclaimer = """
   <p class="disclaimer error">
     The following is an <strong>incomplete interpretation</strong> of the above scribe block. The
     interpreter that produces this view is under development.
   </p>
"""

  if len(row.head_objects) == 0 and len(row.body_objects) == 0:
    head_list, body_list = dgw_parser(row.institution,
                                      row.block_type,
                                      row.block_value,
                                      period=period)
  else:
    head_list, body_list = row.head_objects, row.body_objects

  return row.requirement_html + disclaimer + f"""
<section>
  <h1>Head</h1>
  {to_html(head_list)}
  <h1>Body</h1>
  {to_html(body_list)}
</section>
"""
