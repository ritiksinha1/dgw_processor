#! /usr/local/python3

""" Utilities shared by htmlificization, format_header_productions, and format body_qualifiers.
      and_list
      format_num_class_credit
      format_course_list
      format_number
      list_of_courses
"""

import os
import sys

from traceback import print_stack

import format_body_qualifiers
import html_utils

if os.getenv('DEBUG_FORMAT_UTILS'):
  DEBUG = True
else:
  DEBUG = False

number_names = ['none', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve']


# and_list()
# -------------------------------------------------------------------------------------------------
def and_list(args: list) -> str:
  """ Given a list of strings, format them into an oxford-comma's and list
      Does not deal with commas embedded in arg strings.
  """
  return_str = ', '.join(args)
  match return_str.count(','):
    case 0:
      pass
    case 1:
      return_str = return_str.replace(',', ' and')
    case _:
      point = return_str.rindex(',') + 1
      return_str = return_str[0:point] + ' and' + return_str[point:]

  return return_str


# format_num_class_credit()
# -------------------------------------------------------------------------------------------------
def format_num_class_credit(cc_dict: dict):
  """ Format (num_classes | num_credits) clauses, which appear in requirements.
      They have been converted into  min_classes, max_classes, min_credits, max_credits,
      and conjunction keys by dgw_utils.num_class_or_num_credit()

      Ignore allow_credits and allow_classes that might be present because they are auditor
      directives, not requirements.

      Returns None if the expected keys are not found in the cc_dict.
  """
  assert isinstance(cc_dict, dict), f'{type(cc_dict)} is not dict'

  try:
    num_classes_str = ''
    if cc_dict['min_classes'] is not None:
      min_classes = int(cc_dict['min_classes'])
      max_classes = int(cc_dict['max_classes'])
      if min_classes == max_classes:
        if min_classes != 0:
          suffix = '' if min_classes == 1 else 'es'
          num_classes_str = f'{min_classes} class{suffix}'
      else:
        num_classes_str = f'Between {min_classes} and {maxclasses} classes'

    num_credits_str = ''
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
    return None


# format_course_list()
# -------------------------------------------------------------------------------------------------
def format_course_list(info: dict, num_areas_required: int = 0) -> str:
  """ The dict for a course_list has the following structure:
        scribed_courses     List of all (discipline, catalog_number, with_clause) tuples in the list
                            after distributing disciplines across catalog_numbers. (Show "BIOL 1, 2"
                            as "BIOL 1, BIOL 2")
        active_courses      Catalog information and WITH clause (if any) for all active courses that
                            match the scribed_courses list after expanding wildcards and
                            catalog_number ranges.
        inactive_courses    Catalog information for all inactive courses that match the scribed
                            course list after wildcard and range expansions.
        missing_courses     Explicitly-scribed courses that do not exist in CUNYfirst.
        qualifiers          Qualifiers that apply to all courses in the list
        label               The name of the property (head) or requirement (body)
        course_areas        List of active_courses divided into distribution areas; presumably the
                            full course list will have a MinArea qualifier, but this is not checked
                            here. Omit inactive, missing, and except courses because they are
                            handled in the full course list.
        except_courses      Scribed list used for culling from active_courses.
        include_courses     Like except_courses, except this list is not actually used for anything
                            in this method.

        list_type           'AND' or 'OR'
        attributes          List of all attribute values the active courses list have in common,
                            currently limited to WRIC and BKCR

      Return the HTML representation of the dict; if there is a label is it used as the summary
      element of a details element that contains the remaining parts.
  """
  if DEBUG:
    print(f'*** format_course_list({info.keys()})', file=sys.stderr)
  assert isinstance(info, dict), f'{type(info)} is not dict'

  # This is the HTML string that will be returned, possibly embedded in a details element.
  details_str = ''

  try:
    # Allow for missing or empty label
    summary = None
    if label_str := info['label']:
      summary = f'<summary>{label_str}</summary>'
  except KeyError:
    # Label is optional
    pass

  scribed_courses = info['scribed_courses']
  active_courses = info['active_courses']
  course_areas = info['course_areas']
  num_areas = len(course_areas)
  try:
    list_type = info['list_type']
    assert isinstance(scribed_courses, list)
    scribed_text = ''.join([str(sc) for sc in scribed_courses])
    if len(scribed_courses) > 1 or ':' in scribed_text or '@' in scribed_text:
      if (list_type == 'OR') and (num_areas == 0):
        if len(scribed_courses) == 2:
          details_str += f'<p>Either of these courses</p>'
        else:
          details_str += f'<p>Any of these courses</p>'
      elif num_areas == 0:
        details_str += f'<p>All of these courses</p>'

    details_str += list_of_courses(scribed_courses, 'Scribed Course')

    # We can infer that if there are any qualifiers, this course_list is in the body.
    if qualifiers := format_body_qualifiers.dispatch_body_qualifiers(info):
      details_str += '\n'.join(qualifiers)
      print(f'xxxx THIS IS OK: got qualifiers in format_course_list: {qualifiers}', file=sys.stderr)

    # The active courses may be divided into "course areas." If so the same courses appear in both
    # lists. So either the active list or the areas list gets displayed, not both.
    #   It's possible that all courses within an area have a common attribute
    #   (BKCR not likely, but maybe WRIC.) But the common attributes are shown only if _all_ the
    #   activee courses, across areas, share them.
    assert isinstance(active_courses, list)
    if len(active_courses) < 0:
      details_str += '<div class="error">No Active Courses!</div>'
    else:
      attributes_str = ''
      try:
        if attributes := info['attributes']:
          attributes_str = '<span class="error">' + and_list(attributes) + '</span> '
      except KeyError as ke:
        pass
      if (num_areas := len(course_areas)) > 0:
        suffix = '' if num_areas == 1 else 's'
        if num_areas < len(number_names):
          num_areas = number_names[num_areas].lower()
        if num_areas_required < len(number_names):
          num_areas_required = number_names[num_areas_required].lower()
        details_str += (f'<p>The active courses that satisfy this requirement are divided into the '
                        f'following {num_areas} area{suffix}. Courses must be taken from a minimum '
                        f'of {num_areas_required} of these areas to satisfy this requirement.</p>')
        for index, area_courses in enumerate(course_areas):
          area_id = to_roman(index + 1)
          area_summary = f'<summary>Area {area_id}</summary>'
          area_details = list_of_courses(area_courses, f'Active {attributes_str}Course')
          details_str += f'<details>{area_summary}{area_details}</details>'
      else:
        details_str += list_of_courses(active_courses, f'Active {attributes_str}Course')

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
    error_msg = f'Error: invalid course list: missing key is {ke}'
    details_str = f'<p class="error">{error_msg}</p>' + details_str
    print(error_msg, info, file=sys.stderr)

  if summary is not None:
    return f'<details>{summary}{details_str}</details>'
  else:
    return details_str


# format_number()
# -------------------------------------------------------------------------------------------------
def format_number(number_arg, is_int=False):
  """ A number string can be 1, 1.0, an int other than 1, a float other than 1.0, a range of ints,
      or a range of floats. Handle all cases here, you're welcome.
  """
  parts = number_arg.split(':')
  if is_int:
    if len(parts) == 2:
      min_part = int(parts[0])
      max_part = int(parts[1])
      number_str = f'between {min_part} and {max_part}'
    else:
      value = int(number_arg)
      is_unity = value == 1
      number_str = f'{value}'
  else:
    if len(parts) == 2:
      min_part = float(parts[0])
      max_part = float(parts[1])
      number_str = f'between {min_part:.2f} and {max_part:.2f}'
    else:
      value = float(number_arg)
      is_unity = abs(value - 1.0) < 0.01
      number_str = f'{value:.2f}'

  return number_str, is_unity


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
        f'{len(course_tuple)} is not three or seven'
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


# to_roman()
# -------------------------------------------------------------------------------------------------
def to_roman(value: int, make_upper: bool = True) -> str:
  """ The presence of 500 (D) and 50 (L), coupled with the special handling of 400, 900, 40, 90, 4
      and 9, make table lookup seem like the best approach.
  """
  if value == 0:
    return 'Zero'
  if value > 3999:
    return f'{value:,}'
  thousands, value = divmod(value, 1000)
  hundreds, value = divmod(value, 100)
  tens, ones = divmod(value, 10)
  return_str = thousands * 'm'
  return_str += ['', 'c', 'cc', 'ccc', 'cd', 'd', 'dc', 'dcc', 'dccc', 'cm'][hundreds]
  return_str += ['', 'x', 'xx', 'xxx', 'xl', 'l', 'lx', 'lxx', 'lxxx', 'xc'][tens]
  return_str += ['', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix'][ones]
  return_str = return_str.upper() if make_upper else return_str.lower()
  return return_str
