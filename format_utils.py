#! /usr/local/python3

""" Utilities shared by htmlificization, format_header_productions, and format body_qualifiers.
      class_credit_to_str
      format_class_credit_clause
      format_course_list
      list_of_courses
"""

import os
import sys

import html_utils

if os.getenv('DEBUG_FORMAT_UTILS'):
  DEBUG = True
else:
  DEBUG = False


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


# format_class_credit_clause()
# -------------------------------------------------------------------------------------------------
def format_class_credit_clause(cc_dict: dict):
  """ Convert the elements of a class/credit requirement info into a string.
      Use min_classes, max_classes, min_credits, max_credits, conjunction
      Ignore allow_credits and allow_classes because they are auditor directives, not requirements.
  """
  assert isinstance(cc_dict, dict), f'{type(cc_dict)} is not dict'

  try:
    num_classes_str = None
    if cc_dict['min_classes'] is not None:
      min_classes = int(cc_dict['min_classes'])
      max_classes = int(cc_dict['max_classes'])
      if min_classes == max_classes:
        if min_classes != 0:
          suffix = '' if min_classes == 1 else 'es'
          num_classes_str = f'{min_classes} class{suffix}'
      else:
        num_classes_str = f'Between {min_classes} and {maxclasses} classes'

    num_credits_str = None
    if cc_dict['min_credits'] is not None:
      min_credits = float(cc_dict['min_credits'])
      max_credits = float(cc_dict['max_credits'])
      if abs(max_credits - min_credits) < 0.01:
        if min_credits > 0.0:
          suffix = '' if abs(min_credits - 1.0) < 0.01 else 's'
          num_credits_str = f'{min_credits:.2f} credit{suffix}'
      else:
        num_credits_str = f'Between {min_credits:0.2f} and {max_credits:.2f} credits'

    if num_classes_str and num_credits_str:
      conjunction_str = ' ' + cc_dict['conjunction'].lower() + ' '
      num_credits_str = num_credits_str.lower()
    else:
      conjunction_str = ''
    return f'{num_classes_str}{conjunction_str}{num_credits_str}'

  except (KeyError, ValueError) as err:
    return f'<p class="error">{cc_dict} is not a valid class_credit dict: {err}</p>'


# format_course_list()
# -------------------------------------------------------------------------------------------------
def format_course_list(info: dict) -> str:
  """ The dict for a course_list must have a scribed_courses list, and should have an
      active_courses list. After that, there might be include and except lists, and possibly a
      missing (from CUNYfirst) list.

      Returns a string representing the course list, suitable for use as the body of a HTML details
      element. If a non-empty label is found, a complete details element is returned with the label
      as the element’s summary.
  """
  if DEBUG:
    print(f'*** format_course_list({info.keys()})', file=sys.stderr)
  assert isinstance(info, dict), f'{type(info)} is not dict'

  details_str = ''

  try:
    label_str = info['label']
  except KeyError as ke:
    label_str = None

  list_type = info['list_type']

  try:
    scribed_courses = info['scribed_courses']
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
                       <em>format_course_list() with no scribed courses!</em></p>
                       <p><strong>Keys:</strong> {course_list.keys()}</p>
                  """

  try:
    qualifiers = info['qualifiers']
    if qualifiers is not None and len(qualifiers) > 0:
      details_str += to_html(qualifiers)
  except KeyError as ke:
    pass

  try:
    active_courses = info['active_courses']
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

    course_areas = info['course_areas']
    if len(course_areas) > 0:
      details_str += html_utils.list_to_html(course_areas, kind='Course Area')

    include_courses = info['include_courses']
    assert isinstance(include_courses, list)
    if len(include_courses) > 0:
      details_str += list_of_courses(include_courses, 'Must-include Course')

    except_courses = info['except_courses']
    assert isinstance(except_courses, list)
    if len(except_courses) > 0:
      details_str += list_of_courses(except_courses, 'Except Course')

    inactive_courses = info['inactive_courses']
    assert isinstance(inactive_courses, list)
    if len(inactive_courses) > 0:
      details_str += list_of_courses(inactive_courses, 'Inactive Course')

    missing_courses = info['missing_courses']
    assert isinstance(missing_courses, list)
    if len(missing_courses) > 0:
      details_str += list_of_courses(missing_courses, 'Not-Found-in-CUNYfirst Course',
                                     highlight=True)
  except KeyError as ke:
    print(f'Invalid Course List: missing key is {ke}', file=sys.stderr)
    pprint(info, stream=sys.stderr)

  # Class/Credit info, if present
  if 'conjunction' in info.keys():
    conjunction = info['conjunction']
  else:
    conjunction = None
  if 'min_classes' in info.keys():
    min_classes = info['min_classes']
    max_classes = info['max_classes']
  else:
    min_classes = max_classes = None
  if 'min_credits' in info.keys():
    min_credits = info['min_credits']
    max_credits = info['max_credits']
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
        details_str += html_utils.list_to_html(value, kind=key.strip('s').title())
    else:
      details_str += f'<p>{key}: {value}</p>'

  # if DEBUG:
  #   print(f'    returning [{label_str=} {details_str=}]', file=sys.stderr)

  return (label_str, details_str)


# list_of_courses()
# -------------------------------------------------------------------------------------------------
def list_of_courses(course_tuples: list, title_str: str, highlight=False) -> str:
  """ This is called from format_course_list to format scribed, missing, active, inactive, include,
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
    print(f'*** list_of_courses({len(course_tuples)} course tuples, {title_str} {highlight=})',
          file=sys.stderr)

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


