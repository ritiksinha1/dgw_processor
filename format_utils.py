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

import format_body_qualifiers
import html_utils

from collections import namedtuple, defaultdict
from coursescache import courses_cache, CourseTuple

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
        num_classes_str = f'Between {min_classes} and {max_classes} classes'

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
  """ Return the HTML representation of the dict.

      The dict for a course_list has the following structure:
        institution         Which college
        scribed_courses     A list of course tuples (discipline, catalog_number, with_clause),
                            organized as sublists of course areas. If there were no square-bracketed
                            course areas scribed, all courses will be in scribed_courses[0].
                            Disciplines and catalog_numbers may include wildcards (@); with_clause
                            may be None.
        list_type           AND or OR
        except_courses      Scribed list used for culling from active_courses.
        include_courses     Scribed list of courses that must be taken. Displayed separately.

  """
  if DEBUG:
    print(f'*** format_course_list({info.keys()})', file=sys.stderr)
  assert isinstance(info, dict), f'{type(info)} is not dict'

  # Construct a HTML representation of the list.
  # -----------------------------------------------------------------------------------------------
  html_str = ''

  try:

    # If there are any qualifiers, show them first.
    if qualifiers_list := format_body_qualifiers.dispatch_body_qualifiers(info):
      html_str += '\n'.join(qualifiers_list)

    institution = info['institution']
    requirement_id = info['requirement_id']
    scribed_courses = info['scribed_courses']
    except_courses = info['except_courses']
    include_courses = info['include_courses']

    # Create list of actual courses that will be excluded, if any. This will be used as a filter
    # when the scribed_courses are looked up.
    exclude_courses = []
    for discipline, catalog_number, with_clause in except_courses:
      # Log with_clauses
      if with_clause is not None:
        print(f'{institution} {requirement_id}: Except with ({with_clause})', file=sys.stderr)
      exclude_courses += [f'k[0] k[1]'
                          for k in courses_cache((institution, discipline, catalog_number))]

    # Display the list of courses that must be included
    if len(include_courses) > 0:
      suffix = ' is' if len(include_courses) == 1 else 's are'
      include_clause = ' and '.join([f'{c[0]} {c[1]}' for c in except_courses])
      html_str += f'<p>Note: The following course{suffix} must be included: {include_clause}</p>'

    # Display all the scribed courses, with areas if appropriate, and with active course information
    """ Area I
          CSCI 101 title credits {min_grade no_transfer is_graduate}
          CSCI 1@: 21 active courses
            CSCI 101: title credits is_graduate
          CSCI 1@: No active courses
    """
    multiple_areas = len(scribed_courses) > 1
    total_courses = 0
    for area_index in range(len(scribed_courses)):
      if multiple_areas:
        if area_index > 0:
          html_str += '</details>'
        html_str += f'<details><summary>Area {to_roman(area_index + 1)}</summary>'

      for scribed_course in scribed_courses[area_index]:
        discipline, catalog_number, with_clause = scribed_course
        course_str = f'{discipline} {catalog_number}'

        # Look for residency/grade restriction in with_clause
        residency_req = grade_req = ''
        if with_clause is not None:
          expressions = with_clause.split(',')
          for expression in expressions:
            try:
              lhs, op, rhs = expression.split(' ')
              rhs = rhs.lower().strip('"')
              match lhs.lower():
                case 'dwresident':
                  assert op == '=' and rhs in 'yn', f'Bad expression: {expression}'
                  residency_req = ' <em>Must take at {institution[0:3]}.</em>'
                case 'dwgrade':
                  grade_req = f' <em>Minimum grade {op} {rhs} required.</em>'
                case _:
                  pass
            except ValueError:
              continue

        # A scribed course could expand to 0, 1, or multiple active, non-administrative courses
        active_courses = courses_cache((institution, discipline, catalog_number))
        num_courses = len(active_courses)
        total_courses += num_courses
        match num_courses:

          case 0:
            if '@' in discipline or '@' in catalog_number or ':' in catalog_number:
              suffix = 's'
            else:
              suffix = ''
            html_str += (f'<p>{course_str}: <span class="error">No credit-bearing, currently-'
                         f'active, non-administrative course{suffix} found.</span></p>')

          case 1:
            key, value = active_courses.popitem()
            if key in exclude_courses:
              html_str += f'<p>{key} may not be used for this requirement.</p>'
            else:
              match value.career:
                case 'UGRD':
                  career_str = ''
                case 'GRAD':
                  career_str = f' <em class="error">Graduate course</em>'
                case _:
                  career_str = f' <em class="error">{value.career} course</em>'
              html_str += (f'<p>{course_str}: <em>“{value.title}”</em> {value.credits} cr.'
                           f'{grade_req}{residency_req}{career_str}</p>')

          case _:
            details_body = ''
            num_excluded = 0
            for key, value in active_courses.items():
              if key in exclude_courses:
                num_excluded += 1
                continue
              match value.career:
                case 'UGRD':
                  career_str = ''
                case 'GRAD':
                  career_str = f' <em class="error">Graduate course</em>'
                case _:
                  career_str = f' <em class="error">{value.career} course</em>'
              details_body += (f'<p>{key}: <em>“{value.title}”</em> {value.credits} cr.'
                               f'{grade_req}{residency_req}{career_str}</p>')
            # Report any exclusions
            if num_excluded > 0:
              suffix = '' if num_excluded == 1 else 's'
              html_str += f'<p>{num_excluded} course{suffix} excluded.</p>'
            # If there is only one course remaining after exclusions, no need for a details element
            remaining = num_courses - num_excluded
            if remaining < 1:
              html_str += (f'<p class="error">Unexpected number of courses ('
                           f'{remaining}) remain after exclusions.</p>')
            elif remaining == 1:
              html_str += details_body
            else:
              html_str += f'<details><summary>{remaining:,} {course_str} courses</summary>'
              html_str += f'{details_body}</details>'

    if multiple_areas:
      html_str += '<details>'

  except KeyError as ke:
    error_msg = f'Error: invalid course list: missing key is {ke}'
    html_str = f'<p class="error">{error_msg}</p>' + html_str
    print(error_msg, info, file=sys.stderr)

  return html_str


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
