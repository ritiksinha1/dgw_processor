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
import argparse
from pprint import pprint

from course_lookup import lookup_course
from dgw_interpreter import dgw_interpreter, catalog_years
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

# Quarantined blocks
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
        title, credits, and optional with clause, so the length of those tuples is 7.
  """
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


# course_list_to_details_element()
# -------------------------------------------------------------------------------------------------
def course_list_to_details_element(info: dict) -> str:
  """  The dict for a course_list must have a scribed_courses list, and should have an
       active_courses list. After that, there might be include and except lists, and possibly a
       missing (from CUNYfirst) list. The label becomes the summary for the details element.
       If there is no label, return just the lists, not enclosed in a details element.
       Note: the course_list tag itself was removed by dict_to_html_details before calling this
       method.
  """
  if DEBUG:
    print('course_list_to_details_element', info.keys())

  return_str = ''

  try:
    label = info.pop('label')
  except KeyError as ke:
    label = None
  if label is not None:
    summary = f'<summary>{label.title()}</summary>'

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

  if label is None:
    return return_str
  else:
    return f'<details open="open">{summary}{return_str}</details>'


# requirement_to_details_element()
# -------------------------------------------------------------------------------------------------
def requirement_to_details_element(requirement: dict) -> str:
  """ This starts as class_credit_body in the grammar; dgw_interpreter has turned it into a list of
      dicts. This method interprets one element of that list.
      If there is a label, return a full details element with the label as the summary. Otherwise,
      just return the HTML that will make up the body of an enclosing details element.
      Keys: allow_classes, allow_credits, conjunction, COURSE_LIST, is_pseudo, label, num_classes,
            num_credits.
      Ignoring allow_classes and allow_credits: they are audit controls.
  """

  try:
    label = requirement.pop('label')
    if not label:
      raise KeyError
    label_str = f'<p><strong>{label}</strong></p>'
  except KeyError as ke:
    label_str = None

  requirement_list = []
  if 'is_pseudo' in requirement.keys() and requirement['is_pseudo']:
    requirement_list.append('<p><strong>NOTE:</strong> This requirement does not have a strict '
                            'credit limit.</p>')

  try:
    conjunction = requirement.pop('conjunction')
    conjunction_str = f' {conjunction} '
  except KeyError as ke:
    conjunction_str = '<span class="error">Missing Conjunction</span>'

  try:
    if num_classes := requirement['num_classes']:
      suffix = '' if num_classes == '1' else 'es'
      requirement_list.append(f'{num_classes} class{suffix}')
  except KeyError as ke:
    pass
  try:
    if num_credits := requirement['num_credits']:
      suffix = '' if num_credits == '1' else 's'
      requirement_list.append(f'{num_credits} credit{suffix}')
  except KeyError as ke:
    pass

  if not requirement_list:
    requirements_str = ''
  else:
    requirements_str = f'<p><strong>{conjunction_str.join(requirement_list)} required</strong></p>'

  # If nothing else, expect a list of courses for the requirement
  try:
    course_str = course_list_to_details_element(requirement.pop('course_list'))
  except KeyError as ke:
    course_str = ''

  print(f'rtode: {label_str=}\nrtode: {requirements_str=}\nrtode: {course_str=}', file=sys.stderr)
  if label_str:
    return (f'<details open="open"><summary>{label_str}</summary>'
            f'{requirements_str}{course_str}</details>')
  else:
    return f'{requirements_str}{course_str}'


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
      Then all the other items. Note that dgw_interpreter has renamed class_credit_body as
      'requirements', which gets listed last as “courses.”

       There are four possibilities for labels: outer, inner, both, or neither (really?). If both,
       return the inner part nested inside a details element with the outer label as its summary
  """
  print(f'SUBSET: {info.keys()=}', file=sys.stderr)

  try:
    inner_label = info.pop('label')
  except KeyError as ke:
    inner_label = None

  try:
    remark = info.pop('remark')
    remark_str = f'<p>{remark}</p>'
  except KeyError as ke:
    remark_str = ''

  try:
    qualifiers = info.pop('qualifiers')
    if len(qualifiers) == 0:
      raise KeyError
    qualifiers_str = f'<p>{qualifiers}</p>'
  except KeyError as ke:
    qualifiers_str = ''

  print(f'stode: {inner_label=}\n{remark_str=}\n{qualifiers_str=}\n{info.keys()=}', file=sys.stderr)
  # List of course requirements
  try:
    course_requirements = info.pop('requirements')
    suffix = '' if len(course_requirements) == 1 else 's'
    course_requirements_summary = (f'<summary><strong>{len(course_requirements)} '
                                   f'Course Requirement{suffix}</strong></summary>')
    course_requirements_body = ''.join([requirement_to_details_element(course_requirement)
                                        for course_requirement in course_requirements])
    course_requirements_element = (f'<details>{course_requirements_summary}'
                                   f'{course_requirements_body}</details>')
  except KeyError as ke:
    print(f'{ke=}', file=sys.stderr)
    course_requirements_element = ''

  # Remaining keys are info to appear before the course_requirements
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

  print(f'stode: {summary=}', file=sys.stderr)
  print(f'stode: {body=}', file=sys.stderr)
  return f'<details>{summary}{body}</details>'


# group_to_details_element()
# -------------------------------------------------------------------------------------------------
def group_to_details_element(info: dict, outer_label: str) -> str:
  """  The dict for a conditional construct must have a condition, which becomes the summary of the
       html details element. The optional label goes next, followed by nested details elements for
       the true and the optional false branches.

       There are four possibilities for labels: outer, inner, both, or neither (really?). If both,
       return the parts nested inside a details element with the outer summary
  """
  return details


# conditional_to_details_element()
# -------------------------------------------------------------------------------------------------
def conditional_to_details_element(info: dict, outer_label: str) -> str:
  """  The dict for a conditional construct must have a condition, which becomes the summary of the
       html details element. The optional label goes next, followed by nested details elements for
       the true and the optional false branches.

       There are four possibilities for labels: outer, inner, both, or neither (really?). If both,
       return the parts nested inside a details element with the outer summary
  """

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
    inner_details = (f'<details><summary open="open">{inner_label}</summary'
                     f'{if_true_part}{if_false_part}</details>')

    # Return one of the four possibilities
    if outer_label is None:
      return inner_details
    else:
      return (f'<details><summary open="open"><summary{outer_label}</summary>'
              f'<details>{inner_details}</details>')
  else:
    inner_details = f'{if_true_part}{if_false_part}'
    if outer_label is None:
      return inner_details
    else:
      return (f'<details><summary open="open"><summary{outer_label}</summary>'
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
      print('dict_to_html_details_element', info.keys(), file=sys.stderr)

  # Indicator for not returning a nest-able display element
  label = None
  try:
    label = info.pop('label')
  except KeyError as ke:
    pass

  keys = info.keys()

  if len(keys) == 1:
    # If there is a single key, see if it is group, subset, or conditional, and special-case if so
    key = list(info)[0]
    if key == 'conditional':  # Special case for conditional dicts
      return conditional_to_details_element(info['conditional'], label)
    elif key == 'subset':
      return subset_to_details_element(info['subset'], label)
    elif key == 'group':
      return group_to_details_element(info['group'], label)
    # Not special-case
    if label is None:
      summary = f'<summary>{key.replace("_", " ").title()}</summary>'
    else:
      summary = f'<summary>{label}</summary>'
    value = info[key]
    if isinstance(value, dict):
      return f'<details>{summary}{dict_to_html_details_element(value)}</details>'
    elif isinstance(value, list):
      return f'<details>{summary}{list_to_html_list_element(value)}</details>'
    else:
      return f'<details>{summary}{to_html(value)}</details>'

  else:
    # Case 2

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
      course_list = course_list_to_details_element(info.pop('course_list'))

    # Development aid
    context_path = ''
    if DEBUG:
      try:
        context_path = f'<div><strong>Context:</strong>{info.pop("context_path")}</div>'
      except KeyError as ke:
        pass

    return_str = f'{pseudo_msg}{context_path}{remark}{display}{numerics}{course_list}'

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

    if label is None:
      return return_str
    else:
      return f'<details><summary>{label}</summary>{return_str}</details>'


# list_to_html_list_element()
# -------------------------------------------------------------------------------------------------
def list_to_html_list_element(info: list, kind='Item') -> str:
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
    # Pluralization awkwardness
    if kind == 'Property':
      kind = 'Properties'
    else:
      kind = kind + 's'
    return_str = f'<details open="open"/><summary>{num_str} {kind}</summary>'
    return_str += '\n'.join([f'{to_html(element)}'
                             for element in info])
    return return_str + '</details>'


# to_html()
# -------------------------------------------------------------------------------------------------
def to_html(info: any) -> str:
  """  Return a nested HTML data structure as described above.
  """
  if info is None:
    return ''
  if isinstance(info, bool):
    return 'True' if info else 'False'
  if isinstance(info, list):
    return list_to_html_list_element(info)
  if isinstance(info, dict):
    return dict_to_html_details_element(info)

  return info


# scribe_block_to_html()
# -------------------------------------------------------------------------------------------------
def scribe_block_to_html(row: tuple, period_range='current') -> str:
  """ Generate html for the scribe block and interpreted head and body lists objects, unless the
      block has been quarantined.
  """
  if row.requirement_html == 'Not Available':
    return ('<h1 class="error">This scribe block is not available.</h1>'
            '<p><em>Should not occur.</em></p>')

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
    if len(row.header_list) == 0 and len(row.body_list) == 0:
      header_list, body_list = dgw_interpreter(row.institution,
                                               row.block_type,
                                               row.block_value,
                                               period_range=period_range)
    else:
      header_list, body_list = row.header_list, row.body_list

    return disclaimer + f"""
    <h1>{college_name} {row.requirement_id}: <em>{row.title}</em></h1>
    <p>Requirements for {catalog_type} Catalog Years {catalog_years_text}</p>
    <section>{row.requirement_html}</section>
    <section>
      <details><summary>Header</summary>
        {to_html(header_list)}
      </details>
      <details><summary>Body</summary>
        {to_html(body_list)}
      </details
    </section>
    """


# __main__
# =================================================================================================
# Select Scribe Blocks for parsing
if __name__ == '__main__':
  """ You can select blocks by institutions, block_types, block_values, and period from here.
      By default, the requirement_blocks table's head_objects and body_objects fields are updated
      for each block parsed.
  """
  # Command line args
  parser = argparse.ArgumentParser(description='Test DGW Parser')
  parser.add_argument('-d', '--debug', action='store_true', default=False)
  parser.add_argument('-i', '--institutions', nargs='*', default=['QNS01'])
  parser.add_argument('-np', '--progress', action='store_false')
  parser.add_argument('-p', '--period', choices=['all', 'current', 'latest'], default='latest')
  parser.add_argument('-pp', '--pprint', action='store_true')
  parser.add_argument('-t', '--block_types', nargs='+', default=['MAJOR'])
  parser.add_argument('-ra', '--requirement_id')
  parser.add_argument('-nu', '--update_db', action='store_false')
  parser.add_argument('-v', '--block_values', nargs='+', default=['CSCI-BS'])

  # Parse args
  args = parser.parse_args()
  if args.requirement_id:
    # During development, the use of the ra option generates a web page for debugging.
    institution = args.institutions[0].strip('10').upper() + '01'
    requirement_id = args.requirement_id.strip('AaRr')
    if not requirement_id.isdecimal():
      sys.exit(f'Requirement ID “{args.requirement_id}” must be a number.')
    requirement_id = f'RA{int(requirement_id):06}'
    # Look up the block type and value
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute(f'select block_type, block_value, requirement_html from requirement_blocks'
                   f"  where institution = '{institution}'"
                   f"    and requirement_id = '{requirement_id}'")
    assert cursor.rowcount == 1, (f'Found {cursor.rowcount} block_type/block_value pairs '
                                  f'for {institution} {requirement_id}')
    block_type, block_value, scribe_html = cursor.fetchone()
    conn.close()
    print(f'{institution} {requirement_id} {block_type} {block_value} {args.period}',
          file=sys.stderr)
    header_list, body_list = dgw_interpreter(institution,
                                             block_type,
                                             block_value,
                                             period_range=args.period,
                                             update_db=args.update_db)
    html_head = """<html>
  <head>
    <style>details {border: 1px solid green; padding: 0.2em}</style>
  </head>"""
    html = (f'{html_head}<body>{scribe_html}'
            f'<details open="open"><summary><strong>HEAD</strong></summary>'
            f'{to_html(header_list)}</details>'
            f'<details open="open"><summary><strong>BODY</strong></summary>'
            f'{to_html(body_list)}</details><body></html>')
    print(html)
    exit()

  if args.institutions[0] == 'all':
    conn = PgConnection()
    cursor = conn.cursor()
    cursor.execute('select code from cuny_institutions')
    institutions = [row.code for row in cursor.fetchall()]
    conn.close()
  else:
    institutions = args.institutions

  num_institutions = len(institutions)
  institution_count = 0
  for institution in institutions:
    institution_count += 1
    institution = institution.upper() + ('01' * (len(institution) == 3))
    if args.block_types[0] == 'all':
      args.block_types = ['DEGREE', 'MAJOR', 'MINOR', 'CONC', 'OTHER']
    types_count = 0
    num_types = len(args.block_types)
    for block_type in args.block_types:
      block_type = block_type.upper()
      types_count += 1
      if args.block_values[0].lower() == 'all':
        conn = PgConnection()
        cursor = conn.cursor()
        cursor.execute('select distinct block_value from requirement_blocks '
                       'where institution = %s and block_type = %s'
                       'order by block_value', (institution, block_type))
        block_values = [row.block_value for row in cursor.fetchall()]
        conn.close()
      else:
        block_values = [value.upper() for value in args.block_values]

      num_values = len(block_values)
      values_count = 0
      for block_value in block_values:
        values_count += 1
        if block_value.isnumeric() or block_value.startswith('MHC'):
          continue
        if args.progress:
          print(f'{institution_count:2} / {num_institutions:2};  {types_count} / {num_types}; '
                f'{values_count:3} / {num_values:3} ', end='', file=sys.stderr)
