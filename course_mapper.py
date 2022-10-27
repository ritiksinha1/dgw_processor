#! /usr/local/bin/python3
""" List program requirements and courses that satisfy them.
"""

import csv
import datetime
import os
import json
import psycopg
import re
import sys

from argparse import ArgumentParser
from catalogyears import catalog_years
from collections import namedtuple, defaultdict
from psycopg.rows import namedtuple_row, dict_row
from recordclass import recordclass
from typing import Any

from activeplans import active_plans
from coursescache import courses_cache
from dgw_parser import parse_block

""" Logging/Development Reports
      analysis_file:      Analsis of as-yet-unhandled constructs.
      blocks_file:        List of blocks processed
      debug_file:         Info written during debugging (to avoid stdout/stderr)
      fail_file:          Blocks that failed for one reason or another
      log_file:           Record of requirements processed successfully. Bigger is better!
      no_courses_file:    Requirements with no course lists.
      todo_file:          Record of all known requirements not yet handled. Smaller is better!

    Data for T-Rex
      programs_file:      Spreadsheet of info about majors, minors, and concentrations
      requirements_file:  Spreadsheet of program requirement names
      mapping_file        Spreadsheet of course-to-requirements mappings

"""
analysis_file = open('analysis.txt', 'w')
anomaly_file = open('anomalies.txt', 'w')
blocks_file = open('blocks.txt', 'w')
debug_file = open('debug.txt', 'w')
fail_file = open('fail.txt', 'w')
log_file = open('log.txt', 'w')
missing_file = open(f'missing_ra.txt', 'w')
new_plan_file = open(f'new_plans.txt', 'w')
inactive_plan_file = open(f'inactive_plans.txt', 'w')
no_courses_file = open('no_courses.txt', 'w')
todo_file = open(f'todo.txt', 'w')

programs_file = open(f'{__file__.replace(".py", ".programs.csv")}', 'w', newline='')
requirements_file = open(f'{__file__.replace(".py", ".requirements.csv")}', 'w', newline='')
mapping_file = open(f'{__file__.replace(".py", ".course_mappings.csv")}', 'w', newline='')

programs_writer = csv.writer(programs_file)
requirements_writer = csv.writer(requirements_file)
map_writer = csv.writer(mapping_file)

generated_date = str(datetime.date.today())

# def dict_factory():
#   """ Support for three index levels, as in courses_by_institution and subplans_by_institution.
#   """
#   return defaultdict(dict)


# courses_by_institution = defaultdict(dict_factory)
# subplans_by_institution = defaultdict(dict_factory)

requirement_index = 0
number_names = ['none', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve']
number_ordinals = ['zeroth', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
                   'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth']

_parse_trees = defaultdict(dict)

dap_block_counts = defaultdict(int)
subplan_references = defaultdict(dict)


# =================================================================================================

# get_parse_tree()
# -------------------------------------------------------------------------------------------------
def get_parse_tree(dap_req_block_key: tuple) -> dict:
  """ Look up the parse tree for a dap_req_block.
      Cache it, and return it.
  """
  if dap_req_block_key not in _parse_trees.keys():
    with psycopg.connect('dbname=cuny_curriculum') as conn:
      with conn.cursor(row_factory=namedtuple_row) as cursor:
        cursor.execute("""
        select period_start, period_stop, parse_tree
          from requirement_blocks
         where institution ~* %s
           and requirement_id = %s
        """, dap_req_block_key)
        assert cursor.rowcount == 1
        parse_tree = cursor.fetchone().parse_tree
        if parse_tree is None:
          parse_tree = parse_block(institution, requirement_id, row.period_start, row.period_stop)
          print(f'{institution} {requirement_id} Reference to un-parsed block', file=log_file)
    _parse_trees[dap_req_block_key] = parse_tree
  return _parse_trees[dap_req_block_key]


# letter_grade()
# -------------------------------------------------------------------------------------------------
def letter_grade(grade_point: float) -> str:
  """ Convert a passing grade_point value to a passing letter grade.
      Treat anything less than 1.0 as "Any" passing grade, and anything above 4.3 as "A+"
        GPA Letter
        4.3    A+
        4.0    A
        3.7    A-
        3.3    B+
        3.0    B
        2.7    B-
        2.3    C+
        2.0    C
        1.7    C-
        1.3    D+
        1.0    D
        0.7    D- => "Any"
  """
  if grade_point < 1.0:
    return 'Any'
  else:
    letter_index, suffix_index = divmod((10 * grade_point) - 7, 10)
  letter = ['D', 'C', 'B', 'A'][min(int(letter_index), 3)]
  suffix = ['-', '', '+'][min(int(suffix_index / 3), 2)]
  return letter + suffix


# expand_course_list()
# -------------------------------------------------------------------------------------------------
def expand_course_list(institution: str, requirement_id: str, course_dict: dict) -> dict:
  """ Generate a dict of active courses that match a scribed list with except courses removed (and
      include courses ignored), taking wildcards and ranges into account. Dict keys are (course_id,
      offer_nbr) tuples; values are with-clause expressions (which may be null).

      With-expressions can appear within the scribed list and/or the except list.
        scribed PHYS @
        except  @ 1@ with dwgrade < 2.0 or dwtransfer = y
      Unable to evaluate except list where there are wildcards and the with-expression is not empty,
      so log those cases. But if there is no with-expression, even with wildcards, the matching
      courses get deleted from the return dict.

  """
  # Check for empty list
  if not course_dict:
    return None

  # Get the scribed list and flatten it
  course_list = course_dict['scribed_courses']
  courses = [course for area in course_list for course in area]

  # Create set of (course_id, offer_nbr) tuples for exclude courses that have no with-expressions
  exclude_list = course_dict['except_courses']
  exclude_set = set()
  for item in exclude_list:
    if with_expression := item[2]:
      # Ignore cases where the with clause references DWTerm
      if 'dwterm' in with_expression.lower():
        print(f'{institution} {requirement_id} Exclude course based on DWTerm (ignored)',
              file=log_file)
        continue
      # Log and skip remaining cases that have with-expressions
      print(f'{institution} {requirement_id} expand_course_list(): exclude w/ with',
            file=todo_file)
      print(f'{institution} {requirement_id} expand_course_list(): exclude {with_expression}',
            file=debug_file)
    else:
      print(f'{institution} {requirement_id} Exclude course', file=log_file)
      for k, v in courses_cache((institution, item[0].strip(), item[1].strip())).items():
        exclude_set.add(k)

  # Get rid of redundant scribes
  courses_set = set([tuple(course) for course in courses])

  # Dict of active scribed courses
  return_dict = {}
  for discipline, catalog_nbr, with_clause in courses_set:
    for k, v in courses_cache((institution, discipline, catalog_nbr)).items():
      if k not in exclude_set:
        return_dict[(v.course_id, v.offer_nbr)] = (k, with_clause)

  return return_dict


# format_group_description()
# -------------------------------------------------------------------------------------------------
def format_group_description(num_groups: int, num_required: int):
  """ Return an English string to replace the label (requirement_name) for group requirements.
  """
  assert isinstance(num_groups, int) and isinstance(num_required, int), 'Precondition failed'

  suffix = '' if num_required == 1 else 's'
  if num_required < len(number_names):
    num_required_str = number_names[num_required].lower()
  else:
    num_required_str = f'{num_required:,}'

  s = '' if num_groups == 1 else 's'

  if num_groups < len(number_names):
    num_groups_str = number_names[num_groups].lower()
  else:
    num_groups_str = f'{num_groups:,}'

  if num_required == num_groups:
    if num_required == 1:
      prefix = 'The'
    elif num_required == 2:
      prefix = 'Both of the'
    else:
      prefix = 'All of the'
  elif (num_required == 1) and (num_groups == 2):
    prefix = 'Either of the'
  else:
    prefix = f'Any {num_required_str} of the'
  return f'{prefix} following {num_groups_str} group{s}'


# header_minres()
# -------------------------------------------------------------------------------------------------
def header_minres(value):
  """
  """
  min_classes = value['minres']['min_classes']
  min_credits = value['minres']['min_credits']
  # There must be a better way to do an xor check ...
  match (min_classes, min_credits):
    case [None, None]:
      print(f'Invalid minres {block_info}', file=sys.stderr)
    case [None, credits]:
      return f'{float(credits):.1f} credits'
    case [classes, None]:
      return f'{int(classes)} classes'
    case _:
      print(f'Invalid minres {block_info}', file=sys.stderr)


# map_courses()
# -------------------------------------------------------------------------------------------------
def map_courses(institution: str, requirement_id: str, requirement_name: str, context_list: list,
                requirement_dict: dict):
  """ Write courses and their With clauses to the map file.
      Object returned by courses_cache():
        CourseTuple = namedtuple('CourseTuple', 'course_id offer_nbr title credits career')

      Each program requirement has a unique key based on institution, requirement_id, block_title,
      and context list.

Programs: Handled by process_block()
Institution, Requirement ID, Type, Code, Total, Max Transfer, Min Residency, Min Grade, Min GPA

Requirements: Handled here
Institution, Requirement ID, Requirement Key, Name, Context, Grade Restriction, Transfer Restriction

Course Mappings: Handled here
Requirement Key, Course ID, Career, Course, With

  """

  # The requirement_index is used to join the requirements and the courses that map to them.
  global requirement_index
  requirement_index += 1

  # Copy the requirement_dict in case a local version has to be constructed
  requirement_info = requirement_dict.copy()
  try:
    course_list = requirement_info['course_list']
  except KeyError:
    # Sometimes the course_list _is_ the requirement. In these cases, all scribed courses are
    # required. So create a requirement_info dict with a set of values to reflect this.
    course_list = requirement_dict
    num_scribed = sum([len(area) for area in course_list['scribed_courses']])
    requirement_info = {'label': None,
                        'conjunction': None,
                        'course_list': requirement_dict,
                        'max_classes': num_scribed,
                        'max_credits': None,
                        'min_classes': num_scribed,
                        'min_credits': None,
                        'allow_classes': None,
                        'allow_credits': None}
    try:
      # Ignore context_path, if it is present. (It makes the course list harder to read)
      del course_list['context_path']
    except KeyError:
      pass

  # Filter out duplicated courses: people scribe course lists that include the same course(s) more
  # than once.
  courses_set = set()
  for course_area in range(len(course_list['scribed_courses'])):
    for course_tuple in course_list['scribed_courses'][course_area]:
      # Unless there is a With clause, skip "any course" wildcards (@ @)
      if ['@', '@', None] == course_tuple:
        continue
      discipline, catalog_number, with_clause = course_tuple
      if with_clause is not None:
        with_clause = f'With ({with_clause})'

      courses_dict = courses_cache((institution, discipline, catalog_number))
      for key, value in courses_dict.items():
        courses_set.add(f'{value.course_id:06}:{value.offer_nbr}|{value.career}|'
                        f'{key}: {value.title}|{with_clause}')
    requirement_info['num_courses'] = len(courses_set)
    for course in courses_set:
      map_writer.writerow([requirement_index] + course.split('|') + [generated_date])

  if requirement_info['num_courses'] == 0:
    print(institution, requirement_id, requirement_name, file=no_courses_file)
  else:
    # The requirement_id has to come from the first block_info in the context
    # list (is this ever actually used?).
    try:
      requirement_id = context_list[0]['block_info']['requirement_id']
    except KeyError as err:
      breakpoint()
    data_row = [institution, requirement_id, requirement_index, requirement_name,
                json.dumps(context_list + [{'requirement': requirement_info}], ensure_ascii=False),
                generated_date]
    requirements_writer.writerow(data_row)


# get_restrictions()
# -------------------------------------------------------------------------------------------------
def get_restrictions(node: dict) -> dict:
  """ Return qualifiers that might affect transferability.
  """
  assert isinstance(node, dict)

  return_dict = dict()
  # The maxtransfer restriction puts a limit on the number of classes or credits that can be
  # transferred, possibly with a list of "types" for which the limit applies. I think the type names
  # have to come from a dgw table somewhere.
  try:
    transfer_dict = node.pop('maxtransfer')
    return_dict['maxtransfer'] = transfer_dict
  except KeyError:
    pass

  # The mingrade restriction puts a limit on the minimum required grade for all courses in a course
  # list. It’s a float (like a GPA) in Scribe, but is replaced with a letter grade here.
  mingrade_dict = {}
  try:
    mingrade_dict = node.pop('mingrade')
    number = float(mingrade_dict['number'])
    grade_str = letter_grade(number)
    return_dict['mingrade'] = grade_str
  except KeyError:
    pass

  return return_dict


# process_block()
# =================================================================================================
def process_block(block_info: dict,
                  context_list: list = [],
                  plan_dict: dict = None):
  """ Process a dap_req_block.
      The block will be:
        - An academic plan (major or minor)
        - A subplan (concentration)
        - A nested requirement referenced from a plan or subplan.

      Plans are special: they are the top level of a program, and get entered into the programs
      table. The context list for requirements get initialized here with information about the
      program, including header-level requirements/restrictions, and a list of active subplans
      associated with the plan. When the plan's parse tree is processed, any block referenced by
      a block, block_type, or copy_rules clause will be checked and, if it is of type CONC, verified
      against the plan's list of active subplans.

      Orphans are subplans (concentrations) that are never referenced by its plan's requirements.
  """

  # Every block has to have an error-free parse_tree
  institution = block_info['institution']
  requirement_id = block_info['requirement_id']
  dap_req_block_key = (institution, requirement_id)
  parse_tree = get_parse_tree(dap_req_block_key)
  if 'error' in parse_tree.keys():
    print(f'{institution} {requirement_id} Parse Error', file=fail_file)
    return
  header_dict = traverse_header(institution, requirement_id, parse_tree)

  # How many times do blocks get processed?
  dap_block_counts[dap_req_block_key + (block_info['block_type'], )] += 1

  # Characterize blocks as top-level or nested for reporting purposes; use capitalization to sort
  # top-level before nested.
  toplevel_str = 'Top-level' if plan_dict else 'nested'
  print(f'{institution} {requirement_id} {toplevel_str}', file=blocks_file)

  """ A block_info object contains information about a dap_req_block. When blocks are nested, either
      as a subplan of a plan, or when referenced by a blocktype, block, or copy_rules construct, a
      block_info object is pushed onto the context_list.

      Information for block_info comes from:
        * dap_req_block metadata
        * acad_plan and acad_subplan tables
        * parse_tree header

      plan_dict:
       plan_name, plan_type, plan_description, plan_cip_code, plan_effective_date,
       requirement_block, subplans_list

      subplans_list:
        subplan_dict:
          subplan_name, subplan_type, subplan_description, subplan_cip_code, subplan_effective_date,
          requirement_block

      requirement_block: (Will appear in plan_dicts, subplan_dicts, and nested dicts)
        institution, requirement_id, block_type, block_value, block_title, catalog_years_str,
        num_active_terms, enrollment

      header_dict: (Not part of block_info: used to populate program table, and handled here if
                    a plan_dict is received.)
        class_credits, min_residency, min_grade, min_gpa, max_transfer, max_classes,
        max_credits, other
  """
  catalog_years_str = catalog_years(block_info['period_start'],
                                    block_info['period_stop']).text

  block_info_dict = {'institution': institution,
                     'requirement_id': requirement_id,
                     'block_type': block_info['block_type'],
                     'block_value': block_info['block_value'],
                     'block_title': block_info['block_title'],
                     'catalog_years': catalog_years_str}

  if plan_dict:
    """ For plans, the block_info_dict gets updated with info about the plan and its subplans.
    """
    plan_name = plan_dict['plan']
    plan_info_dict = {'requirement_id': requirement_id,
                      'plan_name': plan_name,
                      'plan_type': plan_dict['type'],
                      'plan_description': plan_dict['description'],
                      'plan_effective_date': plan_dict['effective_date'],
                      'plan_cip_code': plan_dict['cip_code'],
                      'plan_active_terms': block_info['num_recent_active_terms'],
                      'plan_enrollment': block_info['recent_enrollment'],
                      'subplans': []
                      }

    for subplan in plan_dict['subplans']:
      rb = subplan['requirement_block']
      subplan_name = subplan['subplan']
      subplan_dict = {'requirement_id': rb['requirement_id'],
                      'subplan_name': subplan_name,
                      'subplan_type': subplan['type'],
                      'subplan_description': subplan['description'],
                      'subplan_effective_date': subplan['effective_date'],
                      'subplan_cip_code': subplan['cip_code'],
                      'subplan_active_terms': rb['num_recent_active_terms'],
                      'subplan_enrollment': rb['recent_enrollment'],
                      }
      plan_info_dict['subplans'].append(subplan_dict)

      subplan_reference_key = (institution, plan_name)
      if subplan_name in subplan_references[subplan_reference_key].keys():
        print(f'{institution} {requirement_id} Multiple references to subplan {subplan_name}',
              file=fail_file)
        return
      subplan_reference_dict = {subplan_name: {'requirement_id': rb['requirement_id'],
                                               'reference_count': 0}}
      subplan_references[subplan_reference_key] = subplan_reference_dict

    block_info_dict['plan_info'] = plan_info_dict

    # Add the plan_info_dict to the programs table too, but I'm not sure this is needed ...
    header_dict['other']['plan_info'] = plan_info_dict

    # Enter the plan in the programs table
    programs_writer.writerow([f'{institution[0:3]}',
                              f'{requirement_id}',
                              f'{block_info_dict["block_type"]}',
                              f'{block_info_dict["block_value"]}',
                              f'{block_info_dict["block_title"]}',
                              f'{header_dict["class_credits"]}',
                              f'{header_dict["max_transfer"]}',
                              f'{header_dict["min_residency"]}',
                              f'{header_dict["min_grade"]}',
                              f'{header_dict["min_gpa"]}',
                              json.dumps(header_dict['other'], ensure_ascii=False),
                              generated_date
                              ])

    # THE UNRESOLVED ISSUE IS WHEN TO PROCESS CONC BLOCKS. DO ALL THE SUBPLANS WITHIN THE PROCESSING
    # FOR A PLAN, OR WAIT FOR THEM TO BE CALLED FROM WITHIN THE PLAN REQUIREMENTS? I LIKE THE IDEA
    # OF DOING THEM HERE AND THEN FLAGGING ANY UN-PROCESSED ONES WHEN A BLOCKTYPE(CONC) APPEARS.
    # THIS ALSO RESOLVES THE ISSUE OF MULTIPLE SUBPLANS, WHICH ONE TO USE? IT'S ANY ONE OF THE ONES
    # THAT ARE ACTIVE. STILL, NEED TO CHECK FOR BLOCKTYPE WITH N OTHER THAN 1 TO BE SURE IT DOESN'T
    # OCCUR. SO, EVERY ACTIVE CONC SHOULD BE MAPPED, BUT ANOMALIES OCCUR WHEN THERE IS A CONC
    # REQUIRED BUT NONE ACTIVE. BUT WHERE THERE ARE LOTS OF OPTIONS AND WE CAN'T FIGURE OUT WHICH
    # "ONE," THAT'S OK BECAUSE THE T-REX USER WILL PICK ONE TO LOOK AT AND WE WILL HAVE MAPPED THEM
    # ALL.
    # OK, SO WE SET UP A GLOBAL DICT OF ACTIVE SUBPLANS HERE, KEYED BY INSTITUTION, PLAN. THEN
    # BLOCKTYPE MAKES SURE THERE IS AT LEAST ONE AVAILABLE. BUMP THE REFERENCE COUNTS OF ALL
    # POSSIBLE ONES. AT THE END, NOTE ORPHANS.

  # traverse_body() is a recursive procedure that handles nested requirements, so to start, it has
  # to be primed with the root node of the body tree: the body_list. process_block() itself may be
  # invoked from within traverse_body() to handle block, blocktype and copy_rules constructs.
  try:
    body_list = parse_tree['body_list']
  except KeyError as ke:
    print(institution, requirement_id, 'Missing Body', file=fail_file)
    return
  if len(body_list) == 0:
    print(institution, requirement_id, 'Empty Body', file=log_file)
  else:
    context_list += [{'block_info': block_info_dict}]
    for body_item in body_list:
      # traverse_body(body_item, item_context)
      traverse_body(body_item, context_list)

  # Finally, if this is a plan block, map all the subplans, if there are any.
  if plan_dict:
    for subplan in plan_dict['subplans']:
      # THIS DOESN'T WORK: WHAT IF THE SUBPLAN IS DETERMINED CONDITIONALLY?
      # CHECK THIS WHEN THERE IS A BLOCKTYPE CONC, SEE WHAT THE CONTEXT IS. IF IT'S NOT DIRECTLY
      # UNDER A PLAN BLOCK, ... WELL, DO SOMETHING SMART.
      process_block(subplan['requirement_block'], [{'block_info': block_info_dict}])


# traverse_header()
# =================================================================================================
def traverse_header(institution: str, requirement_id: str, parse_tree: dict) -> dict:
  """ Extract program-wide qualifiers, and update block_info with the values found. Handles only
      fields deemed relevant to transfer.
  """

  return_dict = dict()
  # Empty strings for default values that might or might not be found.
  for key in ['class_credits', 'min_residency', 'min_grade', 'min_gpa']:
    return_dict[key] = ''
  # Empty lists as default limits that might or might not be specified in the header.
  for key in ['max_transfer', 'max_classes', 'max_credits']:
    return_dict[key] = []
  # The ignomious 'other' column.
  return_dict['other'] = {'maxclass': [],
                          'maxcredit': [],
                          'maxperdisc': [],
                          'minclass': [],
                          'mincredit': [],
                          'minperdisc': [],
                          'conditional': []}
  try:
    if len(parse_tree['header_list']) == 0:
      print(f'{institution} {requirement_id} Empty Header', file=log_file)
      return return_dict
  except KeyError as ke:
    # You can't have a parse_tree with no header_list, even it it's empty.
    print(parse_tree)
    exit(f'{institution} {requirement_id} Header KeyError ({ke})')

  for header_item in parse_tree['header_list']:

    if not isinstance(header_item, dict):
      exit(f'{institution} {requirement_id} Header “{header_item}” is not a dict')

    for key, value in header_item.items():
      match key:

        case 'header_class_credit':
          if return_dict['class_credits']:
            print(f'{institution} {requirement_id}: Header repeated class-credit declaration',
                  file=todo_file)

          if label_str := value['label']:
            print(f'{institution} {requirement_id}: Header class_credit label: {label_str}',
                  file=todo_file)
          min_classes = None if value['min_classes'] is None else int(value['min_classes'])
          min_credits = None if value['min_credits'] is None else float(value['min_credits'])
          max_classes = None if value['max_classes'] is None else int(value['max_classes'])
          max_credits = None if value['max_credits'] is None else float(value['max_credits'])
          assert not (min_credits and max_credits is None), f'{min_credits} {max_credits}'
          assert not (min_credits is None and max_credits), f'{min_credits} {max_credits}'
          assert not (min_classes and max_classes is None), f'{min_classes} {max_classes}'
          assert not (min_classes is None and max_classes), f'{min_classes} {max_classes}'
          class_credit_list = []
          if min_classes and max_classes:
            if min_classes == max_classes:
              class_credit_list.append(f'{max_classes} classes')
            else:
              class_credit_list.append(f'{min_classes}-{max_classes} classes')

          if min_credits and max_credits:
            if min_credits == max_credits:
              class_credit_list.append(f'{max_credits:.1f} credits')
            else:
              class_credit_list.append(f'{min_credits:.1f}-{max_credits:.1f} credits')
            try:
              proxy_advice = value['proxy_advice']
              if do_proxy_advice:
                print(f'{institution} {requirement_id} Header {key} proxy_advice',
                      file=todo_file)
              else:
                print(f'{institution} {requirement_id} Header {key} proxy_advice (ignored)',
                      file=log_file)
            except KeyError:
              # No proxy-advice (normal))
              pass
          return_dict['class_credits'] = ' and '.join(class_credit_list)

        case 'conditional':
          """ Observed:
                No course list items
                 58   T: ['header_class_credit']
                 30   F: ['header_class_credit']
                 49   T: ['header_share']
                 49   F: ['header_share']
                  7   T: ['header_minres']

                Items with course lists
                The problem is that many of these expand to un-useful lists of courses, but others
                are meaningful. Need to look at them in more detail.
                 15   T: ['header_maxcredit']
                  1   T: ['header_maxtransfer']
                  2   T: ['header_minclass']
                  5   T: ['header_mincredit']
                  1   F: ['header_mincredit']

                Recursive item
                 28   F: ['conditional']
          """
          print(f'{institution} {requirement_id} Header conditional', file=todo_file)

          conditional_dict = header_item['conditional']
          condition_str = conditional_dict['condition_str']
          print(f'\n{institution} {requirement_id} Header conditional: {condition_str}',
                file=debug_file)
          if_true_list = conditional_dict['if_true']
          for item in if_true_list:
            print(f'  T: {list(item.keys())}', file=debug_file)
          try:
            if_false_list = conditional_dict['if_false']
            for item in if_false_list:
              print(f'    F: {list(item.keys())}', file=debug_file)
          except KeyError:
            if_false_list = []

        case 'header_lastres':
          # A subset of residency requirements
          print(f'{institution} {requirement_id} Header lastres (ignored)', file=log_file)
          pass

        case 'header_maxclass':
          print(f'{institution} {requirement_id} Header maxclass', file=log_file)
          try:
            for cruft_key in ['institution', 'requirement_id']:
              del(value['maxclass']['course_list'][cruft_key])
          except KeyError:
            # The same block might have been mapped in a different context already
            pass

          number = int(value['maxclass']['number'])
          course_list = value['maxclass']['course_list']
          course_list['courses'] = [{'course_id': f'{k[0]:06}:{k[1]}',
                                     'course': v[0],
                                     'with': v[1]}
                                    for k, v in expand_course_list(institution,
                                                                   requirement_id,
                                                                   course_list).items()]
          limit_dict = {'number': number,
                        'courses': course_list
                        }
          return_dict['other']['maxclass'].append(limit_dict)

        case 'header_maxcredit':
          try:
            for cruft_key in ['institution', 'requirement_id']:
              del(value['maxcredit']['course_list'][cruft_key])
          except KeyError:
            pass

          number = float(value['maxcredit']['number'])
          course_list = value['maxcredit']['course_list']
          course_list['courses'] = [{'course_id': f'{k[0]:06}:{k[1]}',
                                     'course': v[0],
                                     'with': v[1]}
                                    for k, v in expand_course_list(institution,
                                                                   requirement_id,
                                                                   course_list).items()]
          limit_dict = {'number': number,
                        'courses': course_list
                        }
          return_dict['other']['maxcredit'].append(limit_dict)
          print(f'{institution} {requirement_id} Header maxcredit', file=log_file)

        case 'header_maxpassfail':
          print(f'{institution} {requirement_id} Header maxpassfail', file=log_file)
          assert 'maxpassfail' not in return_dict['other'].keys()
          return_dict['other']['maxpassfail'] = value['maxpassfail']

        case 'header_maxperdisc':
          print(f'{institution} {requirement_id} Header maxperdisc', file=log_file)
          return_dict['other']['maxperdisc'].append(value['maxperdisc'])

        case 'header_maxtransfer':
          print(f'{institution} {requirement_id} Header maxtransfer', file=log_file)
          if label_str := value['label']:
            print(f'{institution} {requirement_id} Header maxtransfer label', file=todo_file)

          transfer_limit = {}
          number = float(value['maxtransfer']['number'])
          class_or_credit = value['maxtransfer']['class_or_credit']
          if class_or_credit == 'credit':
            transfer_limit['limit'] = f'{number:3.1f} credits'
          else:
            suffix = '' if int(number) == 1 else 'es'
            transfer_limit['limit'] = f'{int(number):3} class{suffix}'
          try:
            transfer_limit['transfer_types'] = value['transfer_types']
          except KeyError:
            pass
          return_dict['max_transfer'].append(transfer_limit)

        case 'header_minclass':
          print(f'{institution} {requirement_id} Header minclass', file=log_file)
          return_dict['other']['minclass'].append(value['minclass'])

        case 'header_mincredit':
          print(f'{institution} {requirement_id} Header mincredit', file=log_file)
          return_dict['other']['mincredit'].append(value['mincredit'])

        case 'header_mingpa':
          print(f'{institution} {requirement_id} Header mingpa', file=log_file)
          if label_str := value['label']:
            print(f'{institution} {requirement_id} Header mingpa label', file=todo_file)
          mingpa = float(value['mingpa']['number'])
          return_dict['min_gpa'] = f'{mingpa:4.2f}'

        case 'header_mingrade':
          print(f'{institution} {requirement_id} Header mingrade', file=log_file)
          if label_str := value['label']:
            print(f'{institution} {requirement_id} Header mingrade label', file=todo_file)
          return_dict['min_grade'] = letter_grade(float(value['mingrade']['number']))

        case 'header_minperdisc':
          if label := value['label']:
            print(f'{institution} {requirement_id} Header minperdisc label', file=todo_file)
          return_dict['other']['minperdisc'].append(value['minperdisc'])
          print(f'{institution} {requirement_id} Header minperdisc', file=log_file)

        case 'header_minres':
          print(f'{institution} {requirement_id} Header minres', file=log_file)
          return_dict['min_residency'] = header_minres(value)

        case 'proxy_advice':
          if do_proxy_advice:
            print(f'{institution} {requirement_id} Header {key}', file=todo_file)
          else:
            print(f'{institution} {requirement_id} Header {key} (ignored)', file=log_file)

        case 'remark':
          # (Not observed to occur)
          print(f'{institution} {requirement_id} Header remark', file=log_file)
          assert 'remark' not in return_dict['other'].keys()
          return_dict['other']['remark'] = value['remark']

        case 'header_maxterm' | 'header_minterm' | 'noncourse' | 'optional' | \
             'rule_complete' | 'standalone' | 'header_share' | 'header_tag':
          # Intentionally ignored
          print(f'{institution} {requirement_id} Header {key} (ignored)', file=log_file)
          pass

        case _:
          print(f'{institution} {requirement_id}: Unexpected {key} in header', file=sys.stderr)

  return return_dict


# traverse_body()
# =================================================================================================
def traverse_body(node: Any, context_list: list) -> None:
  """ Extract Requirement names and course lists from body rules. Unlike traverse_header(), which
      makes a single pass over all the elements in the header list for a Scribe Block, this is a
      recursive function to handle nested requirements.

      Element 0 of the context list is always information about the block, including header
      restrictions: MaxTransfer, MinResidency, MinGrade, and MinGPA. (See traverse_header(), which
      adds this info to the BlockInfo object in the context_list.)

      If there is a label, that becomes the requirement_name to add to the context_list when
      entering sub-dicts.

      Block, Conditional, CopyRules, Groups, and Subsets all have to be handled individually here.

      If a node's subdict has a course_list, that becomes an output.

        body_rule       : block
                        | blocktype
                        | class_credit
                        | conditional
                        | course_list_rule
                        | copy_rules
                        | group_requirement
                        | noncourse
                        | proxy_advice
                        | remark
                        | rule_complete
                        | subset
  """

  global do_remarks, args

  # Find the containing block’s context.
  # Ir’s the last block_info item in the context_list
  for ctx in reversed(context_list):
    try:
      block_info = ctx['block_info']
      institution = block_info['institution']
      requirement_id = block_info['requirement_id']
      block_type = block_info['block_type']
      block_value = block_info['block_value']
      block_title = block_info['block_title']
      break
    except KeyError as ke:
      continue

  # Handle lists
  if isinstance(node, list):
    for item in node:
      traverse_body(item, context_list)

  elif isinstance(node, dict):
    # A dict should have one key that identifies the requirement type, and a sub-dict that gives the
    # details about that requirement, including the label that gives it its name.

    assert len(node) == 1, f'{list(node.keys())}'
    requirement_type, requirement_value = list(node.items())[0]

    # String values are remarks: add to context, and continue. Can be suppressed from command line.
    if isinstance(requirement_value, str):
      assert requirement_type == 'remark'
      if do_remarks:
        print(f'{institution} {requirement_id} Body remark',
              file=log_file)
        context_list += [{requirement_type: requirement_value}]
      else:
        pass

    # Lists happen in requirement_values because of how the grammar handles requirements that can
    # occur in different orders. (“This or that, zero or more times.”)
    elif isinstance(requirement_value, list):
      for list_item in requirement_value:
        traverse_body(list_item, context_list)

    elif isinstance(requirement_value, dict):
      context_dict = get_restrictions(requirement_value)
      try:
        context_dict['requirement_name'] = requirement_value['label']
      except KeyError:
        # Unless a conditional, if there is no label, add a placeholder name, and log the situation
        if requirement_type != 'conditional':
          context_dict['requirement_name'] = 'Unnamed Requirement'
          if requirement_type not in ['copy_rules']:  # There may be others (?) ...
            print(f'{institution} {requirement_id} Body {requirement_type} with no label',
                  file=log_file)
      requirement_context = [context_dict]

      match requirement_type:

        case 'block':
          # The number of blocks has to be 1, and there has to be a matching block_type/value block
          num_required = int(requirement_value['number'])

          if num_required != 1:
            print(f'{institution} {requirement_id} Body block: {num_required=}', file=todo_file)
          else:
            block_args = [requirement_value['institution'],
                          requirement_value['block_type'],
                          requirement_value['block_value']]
            with psycopg.connect('dbname=cuny_curriculum') as conn:
              with conn.cursor(row_factory=dict_row) as cursor:
                blocks = cursor.execute("""
                select institution, requirement_id, block_type, block_value, title as block_title,
                       period_start, period_stop, major1
                  from requirement_blocks
                 where institution = %s
                   and block_type = %s
                   and block_value = %s
                   and period_stop ~* '^9'
                """, block_args)

                target_block = None
                if cursor.rowcount == 0:
                  print(f'{institution} {requirement_id} Body block: no active {block_args[1:]} '
                        f'blocks', file=fail_file)
                elif cursor.rowcount > 1:
                  # Hopefully, the major1 field of exactly one block will match this program's block
                  # value, resolving the issue.
                  matching_rows = []
                  for row in cursor:
                    if row['major1'] == block_value:
                      matching_rows.append(row)
                  if len(matching_rows) == 1:
                    target_block = matching_rows[0]
                  else:
                    print(f'{institution} {requirement_id} Body block: {cursor.rowcount} active '
                          f'{block_args[1:]} blocks; {len(matching_rows)} major1 matches',
                          file=fail_file)
                else:
                  target_block = cursor.fetchone()

                if target_block is not None:
                  process_block(target_block, context_list + requirement_context)
                  print(f'{institution} {requirement_id} Body block {target_block["block_type"]}',
                        file=log_file)

        case 'blocktype':
          # Presumably, this is a reference to a subplan (concentration), which has already been
          # mapped as part of the plan's processing. If not, it's either an error or a problem.

          preconditions = True
          # Crash if multiple blocks required
          num_required = int(requirement_value['number'])
          if num_required != 1:
            print(f'{institution} {requirement_id} Body blocktype num_required ({num_required}) is '
                  f'not unity', file=fail_file)
            preconditions = False

          required_blocktype = requirement_value['block_type']
          if required_blocktype != 'CONC':
            print(f'{institution} {requirement_id} Body blocktype Required blocktype '
                  f'({required_blocktype}) is not “CONC”', file=fail_file)
            preconditions = False

          try:
            subplans_list = context_list[0]['block_info']['plan_info']['subplans']
          except KeyError as err:
            print(f'{institution} {requirement_id} Body blocktype KeyError ({err})', file=fail_file)
            preconditions = False

          if len(subplans_list) < 1:
            print(f'{institution} {requirement_id} Body blocktype no subplans ', file=fail_file)
            preconditions = False

          if preconditions:
            # Add one to the reference counts for each of the plan's subplans
            subplan_references_key = (institution,
                                      context_list[0]['block_info']['plan_info']['plan_name'])
            for subplan_reference in subplan_references[subplan_references_key]:
              subplan_references[subplan_references_key][subplan_reference]['reference_count'] += 1

            # try:
            #   # The subplans list comes from the top-level (plan) block_info, even if the rule comes
            #   # from a nested context.
            #   subplans_list = context_list[0]['block_info']['plan_info']['subplans']
            # except KeyError:
            #   subplans_list = []
            # plan_enrollment = context_list[0]['block_info']['plan_info']['plan_enrollment']
            # if plan_enrollment is None:
            #   plan_enrollment = 0
            # else:
            #   plan_enrollment = int(plan_enrollment)
            # s = '' if plan_enrollment == 1 else 's'
            # plan_enrollment_str = f'{plan_enrollment:,} student{s}.'
            # num_subplans = len(subplans_list)
            # s = '' if num_subplans == 1 else 's'
            # if num_subplans < num_required:
            #   print(f'{institution} {requirement_id} Body blocktype: program has {num_subplans} '
            #         f'subplan{s} but {num_required} needed. {plan_enrollment_str}',
            #         file=fail_file)
            # else:
            #   # Look up all matching subplans
            #   try:
            #     subplan_names, enrollments = zip(*[(s['subplan'], s['enrollment'])
            #                                      for s in subplans_list])
            #   except ValueError as ve:
            #     exit(f'{institution} {requirement_id} Unexpected ValueError {ve} in Body blocktype')
            #   block_value_list = ','.join([f"'{name}'" for name in subplan_names])
            #   with psycopg.connect('dbname=cuny_curriculum') as conn:
            #     with conn.cursor(row_factory=namedtuple_row) as cursor:
            #       cursor.execute(f"""
            #       select institution, requirement_id, block_type, block_value, title as block_title,
            #              period_start, period_stop, parse_tree
            #         from requirement_blocks
            #        where institution = %s
            #          and block_type = %s
            #          and block_value in ({block_value_list})
            #          and period_stop ~* '^9'
            #       """, (institution, required_blocktype))
            #       s = '' if num_required == 1 else 's'
            #       if cursor.rowcount < num_required:
            #         print(f'{institution} {requirement_id} Body blocktype {num_required} block{s} '
            #               f'needed but no more than {cursor.rowcount} found.'
            #               f' {plan_enrollment_str}', file=fail_file)
            #       else:
            #         requirement_name = f'{num_required} concentration{s} required'
            #         choice_context = {'choice': {'num_choices': num_subplans,
            #                                      'num_required': num_required,
            #                                      'index': 0,
            #                                      'block_type': required_blocktype}}
            #         block_values = []
            #         for row in cursor:
            #           choice_context['choice']['index'] += 1
            #           if row.block_value in block_values:
            #             print(f'{institution} {requirement_id} Body blocktype Duplicate '
            #                   f'{row.block_value} with {row.block_title}. {plan_enrollment_str}',
            #                   file=fail_file)
            #             continue
            #           block_values.append(row.block_value)
            #           process_block(row, context_list + requirement_context + [choice_context])

        case 'class_credit':
          print(institution, requirement_id, 'Body class_credit', file=log_file)
          # This is where course lists turn up, in general.
          try:
            if course_list := requirement_value['course_list']:
              map_courses(institution, requirement_id, block_title,
                          context_list + requirement_context, requirement_value)
          except KeyError:
            # Course List is an optional part of ClassCredit
            pass

        case 'conditional':
          assert isinstance(requirement_value, dict)
          # Use the condition as the pseudo-name of this requirement
          condition = requirement_value['condition_str']
          for if_true_dict in requirement_value['if_true']:
            condition_dict = {'requirement_name': 'if_true', 'condition': condition}
            condition_list = [condition_dict]
            traverse_body(if_true_dict, context_list + condition_list)
          try:
            for if_false_dict in requirement_value['if_false']:
              condition_dict = {'requirement_name': 'if_false', 'condition': condition}
              condition_list = [condition_dict]
              traverse_body(if_false_dict, context_list + condition_list)
          except KeyError:
            # Scribe Else clause is optional
            pass
          print(institution, requirement_id, 'Body conditional', file=log_file)

        case 'copy_rules':
          print(institution, requirement_id, 'Body copy_rules', file=log_file)
          # Use the title of the block as the label.
          with psycopg.connect('dbname=cuny_curriculum') as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
              cursor.execute("""
              select institution, requirement_id, block_type, block_value, title as block_title,
                     period_start, period_stop, parse_tree
                from requirement_blocks
               where institution = %s
                 and requirement_id = %s
                 and period_stop ~* '^9'
              """, (requirement_value['institution'],
                    requirement_value['requirement_id']))
              if cursor.rowcount != 1:
                print(f'{institution} {requirement_id} Body copy_rules: {cursor.rowcount} active '
                      f'blocks', file=fail_file)
                return

              row = cursor.fetchone()

              is_circular = False
              for context_dict in context_list:
                try:
                  # Assume there are no cross-institutional course requirements
                  if row['requirement_id'] == context_dict['requirement_id']:
                    print(institution, requirement_id, 'Body circular copy_rules', file=fail_file)
                    is_circular = True
                except KeyError:
                  pass
              if not is_circular:

                parse_tree = row['parse_tree']
                if parse_tree == '{}':
                  # Not expecting to do this
                  print(f'{row.institution} {row.requirement_id} Body copy_rules parse target block'
                        f'{row.requirement_id}', file=log_file)
                  parse_tree = parse_block(row['institution'], row['requirement_id'],
                                           row['period_start'], row['period_stop'])

                body_list = parse_tree['body_list']
                local_dict = {'requirement_block': row['requirement_id'],
                              'requirement_name': ['block_title']}
                local_context = [local_dict]
                traverse_body(body_list,
                              context_list + requirement_context + local_context)

        case 'course_list':
          # Not observed to occur
          print(institution, requirement_id, 'Body course_list', file=fail_file)

        case 'course_list_rule':
          if 'course_list' not in requirement_value.keys():
            # Can't have a Course List Rule w/o a course list
            print(f'{institution} {requirement_id} Body course_list_rule w/o a Course List',
                  file=fail_file)
          else:
            map_courses(institution, requirement_id, block_title,
                        context_list + requirement_context, requirement_value)
            print(institution, requirement_id, 'Body course_list_rule', file=log_file)

        case 'rule_complete':
          # There are no course requirements for this, but whether “is_complete” is true or false,
          # coupled with what sort of conditional structure it is nested in, could be used to tell
          # whether a concentration is required (or not). For now, it is ignored, and unless there
          # is a group structure to hold references to other blocks (which could be used if a
          # student has to complete, say, 3 of 5 possible concentrations), assume that however many
          # concentration blocks are found, the student has to declare one and complete its
          # requirements.)
          print(institution, requirement_id, 'Body rule_complete (ignored)', file=log_file)

        case 'group_requirements':
          # Group requirements is a list , so it should not show up here.
          exit(f'{institution} {requirement_id} Error: unexpected group_requirements',
               file=sys.stderr)

        case 'group_requirement':
          print(institution, requirement_id, 'Body group_requirement', file=log_file)
          # ---------------------------------------------------------------------------------------
          """ Each group requirement has a group_list, label, and number (num_required)
              A group_list is a list of groups (!)
              Each group is one of: block, blocktype, class_credit, course_list,
                                    group_requirement(s), noncourse, or rule_complete)
          """
          groups = requirement_value['group_list']
          num_groups = len(groups)
          s = '' if num_groups == 1 else 's'
          if num_groups < len(number_names):
            num_groups_str = number_names[num_groups]
          else:
            num_groups_str = f'{num_groups:,}'

          num_required = int(requirement_value['number'])
          context_dict['num_groups'] = num_groups
          context_dict['num_required'] = num_required

          # Replace common variants of the requirement_name with standard-format version
          description_str = format_group_description(num_groups, num_required)

          ignore_words = number_names + ['and', 'area', 'areas', 'choose', 'following', 'from',
                                         'group', 'groups', 'module', 'modules', 'of', 'option',
                                         'options', 'or', 'select', 'selected', 'selct', 'slect',
                                         'sequence', 'sequences', 'set', 'study', 'the']
          word_str = context_dict['requirement_name']

          # Strip digits and punctuation and extract resulting words from description string
          words = [word.lower() for word in
                   re.sub(r'[\d,:]+', ' ', word_str).split()]
          for ignore_word in ignore_words:
            try:
              del words[words.index(ignore_word)]
            except ValueError:
              pass

          # Are there any not-to-ignore words left?
          if words:
            # Yes: keep the current requirement_name.
            pass
          else:
            # No: Replace the Scribed name with our formatted one.
            context_dict['requirement_name'] = description_str

          for group_num, group in enumerate(groups):
            if (group_num + 1) < len(number_ordinals):
              group_num_str = (f'{number_ordinals[group_num + 1].title()} of {num_groups_str} '
                               f'group{s}')
            else:
              group_num_str = f'Group number {group_num + 1:,} of {num_groups_str} group{s}'

            group_context = [{'group_number': group_num + 1,
                              'requirement_name': group_num_str}]

            assert len(group.keys()) == 1

            for key, value in group.items():
              match key:
                case 'block':
                  block_name = value['label']
                  block_num_required = int(value['number'])
                  if block_num_required > 1:
                    print(f'{institution} {requirement_id} Group block: {block_num_required=}',
                          file=todo_file)
                    continue
                  block_type = value['block_type']
                  block_value = value['block_value']
                  block_institution = value['institution']
                  with psycopg.connect('dbname=cuny_curriculum') as conn:
                    with conn.cursor(row_factory=dict_row) as cursor:
                      cursor.execute("""
                      select institution,
                                  requirement_id,
                                  block_type,
                                  block_value,
                                  title as block_title,
                                  period_start, period_stop, major1
                             from requirement_blocks
                            where institution = %s
                              and block_type =  %s
                              and block_value = %s
                              and period_stop ~* '^9'
                      """, [institution, block_type, block_value])
                      if cursor.rowcount == 0:
                        print(f'{institution} {requirement_id} Group block: no active '
                              f'[{block_type}, {block_value}] blocks', file=fail_file)
                      elif cursor.rowcount > block_num_required:
                        print(f'{institution} {requirement_id} Group block: {cursor.rowcount} '
                              f'active [{block_type}, {block_value}] blocks', file=fail_file)
                      else:
                        process_block(cursor.fetchone(),
                                      context_list + requirement_context + group_context)
                        print(f'{institution} {requirement_id} Group block', file=log_file)

                case 'blocktype':
                  # Not observed to occur
                  print(institution, requirement_id, 'Group blocktype (ignored)', file=todo_file)

                case 'class_credit':
                  # This is where course lists turn up, in general.
                  try:
                    map_courses(institution, requirement_id, block_title,
                                context_list + requirement_context + group_context, value)
                  except KeyError as ke:
                    # Course List is an optional part of ClassCredit
                    pass
                  print(institution, requirement_id, 'Group class_credit', file=log_file)

                case 'course_list_rule':
                  if 'course_list' not in requirement_value.keys():
                    # Can't have a Course List Rule w/o a course list
                    print(f'{institution} {requirement_id} Group course_list_rule w/o a Course '
                          f'List', file=fail_file)
                  else:
                    map_courses(institution, requirement_id, block_title,
                                context_list + group_context, value)
                    print(institution, requirement_id, 'Group course_list_rule', file=log_file)

                case 'group_requirements':
                  assert isinstance(value, list)
                  for group_requirement in value:
                    traverse_body(value, context_list + requirement_context + group_context)
                  print(institution, requirement_id, 'Body nested group_requirements',
                        file=log_file)

                case 'noncourse':
                  print(f'{institution} {requirement_id} Group noncourse (ignored)',
                        file=log_file)

                case 'rule_complete':
                  # Not observed to occur
                  print(f'{institution} {requirement_id} Group rule_complete', file=todo_file)

                case _:
                  exit(f'{institution} {requirement_id} Unexpected Group {key}')

        case 'subset':
          print(institution, requirement_id, 'Body subset', file=log_file)
          # ---------------------------------------------------------------------------------------
          # Process the valid rules in the subset

          # Track MaxTransfer and MinGrade restrictions (qualifiers).
          context_dict = get_restrictions(requirement_value)

          try:
            context_dict['requirement_name'] = requirement_value.pop('label')
          except KeyError:
            context_dict['requirement_name'] = 'No requirement name available'
            print(f'{institution} {requirement_id} Subset with no label', file=fail_file)
          try:
            context_dict['remark'] = requirement_value.pop('remark')
            print(f'{institution} {requirement_id} Subset remark', file=log_file)
          except KeyError:
            # Remarks are optional
            pass

          subset_context = [context_dict]

          # The requirement_value should be a list of requirement_objects. The subset context
          # provides information for the whole subset; each requirement takes care of its own
          # context.
          for requirement in requirement_value['requirements']:
            assert len(requirement.keys()) == 1, f'{requirement.keys()}'

            for key, rule in requirement.items():
              # try:
              #   context_dict = get_restrictions(rule)
              # except AssertionError as ae:
              #   print('\n', requirement, '\n', rule, file=sys.stderr)
              #   exit()
              # try:
              #   context_dict['requirement_name'] = rule.pop('label')
              # except KeyError:
              #   print(f'{key} object has no label', file=sys.stderr)

              match key:

                case 'block':
                  # label number type value
                  if isinstance(rule, list):
                    block_dicts = rule
                  else:
                    block_dicts = [rule]
                  for block_dict in block_dicts:
                    num_required = int(block_dict['block']['number'])
                    if num_required != 1:
                      print(f'{institution} {requirement_id} Subset block: {num_required=}',
                            file=fail_file)
                      continue
                    block_label = block_dict['block']['label']
                    required_block_type = block_dict['block']['block_type']
                    required_block_value = block_dict['block']['block_value']
                    with psycopg.connect('dbname=cuny_curriculum') as conn:
                      with conn.cursor(row_factory=dict_row) as cursor:
                        cursor.execute("""
                        select institution, requirement_id, block_type, block_value,
                               title as block_title, period_start, period_stop, major1
                          from requirement_blocks
                         where institution = %s
                           and block_type = %s
                           and block_value = %s
                           and period_stop ~* '^9'
                        """, [institution, required_block_type, required_block_value])
                        if cursor.rowcount == 0:
                          print(f'{institution} {requirement_id} Subset block: no active '
                                f'[{required_block_type}, {required_block_value}] blocks',
                                file=fail_file)
                        elif cursor.rowcount > num_required:
                          print(f'{institution} {requirement_id} Subset block: {cursor.rowcount} '
                                f'active [{required_block_type}, {required_block_value}] blocks',
                                file=fail_file)
                        else:
                          local_context = [{'requirement_name': block_label}]
                          process_block(cursor.fetchone(),
                                        context_list + subset_context + local_context)
                          print(institution, requirement_id, f'Subset block', file=log_file)

                case 'blocktype':
                  # Not observed to occur
                  print(f'{institution} {requirement_id} Subset blocktype (ignored)',
                        file=todo_file)

                case 'conditional_list':
                  print(f'{institution} {requirement_id} Subset conditional_list', file=log_file)
                  # if isinstance(rule, list):
                  #   conditional_dict = rule[0]
                  # else:
                  #   conditional_dict = rule
                  traverse_body(rule, context_list + subset_context)

                  # # Use the condition as the pseudo-name of this requirement
                  # condition = conditional['condition_str']
                  # for if_true_dict in conditional['if_true']:
                  #   condition_list = [{'requirement_name': 'if_true', 'condition': condition}]
                  #   traverse_body(if_true_dict, context_list + subset_context + condition_list)
                  # try:
                  #   for if_false_dict in conditional['if_false']:
                  #     condition_list = [{'requirement_name': 'if_true', 'condition': condition}]
                  #     traverse_body(if_true_dict, context_list + subset_context + condition_list)
                  # except KeyError:
                  #   # Scribe Else clause is optional
                  #   pass

                case 'copy_rules':
                  print(institution, requirement_id, 'Subset copy_rules', file=log_file)
                  try:
                    target_requirement_id = rule['requirement_id']
                  except KeyError as err:
                    print(f'{institution} {requirement_id} Missing key {ke} in Subset copy_rules',
                          file=sys.stderr)
                    exit(rule)
                  target_block = f'{institution} {target_requirement_id}'
                  if target_block in requirement_context:
                    print(target_block, 'Subset copy_rules: Circular target', file=fail_file)
                  else:
                    with psycopg.connect('dbname=cuny_curriculum') as conn:
                      with conn.cursor(row_factory=namedtuple_row) as cursor:
                        cursor.execute("""
                        select institution,
                               requirement_id,
                               block_type,
                               block_value,
                               title as block_title,
                               period_start,
                               period_stop,
                               parse_tree
                          from requirement_blocks
                         where institution = %s
                           and requirement_id = %s
                           and period_stop ~* '^9'
                        """, [institution, target_requirement_id])
                        if cursor.rowcount != 1:
                          print(f'{institution} {requirement_id} Subset copy_rules: '
                                f'{target_requirement_id} not active',
                                file=fail_file)
                        else:
                          row = cursor.fetchone()
                          is_circular = False
                          for context_dict in context_list:
                            try:
                              # Assume there are no cross-institutional course requirements
                              if row.requirement_id == context_dict['requirement_id']:
                                print(institution, requirement_id, 'Subset circular CopyRules',
                                      file=fail_file)
                                is_circular = True
                            except KeyError:
                              pass
                          if not is_circular:
                            parse_tree = row.parse_tree
                            if parse_tree == '{}':
                              print(f'Parsing {row.institution} {row.requirement_id}')
                              parse_tree = parse_block(row.institution, row.requirement_id,
                                                       row.period_start, row.period_stop)
                            try:
                              body_list = parse_tree['body_list']
                            except KeyError as ke:
                              if 'error' in parse_tree.keys():
                                problem = 'compile error'
                              else:
                                problem = 'no body_list'
                              print(f'{institution} {requirement_id} Subset copy_rules target = '
                                    f'{row.requirement_id}: {problem}', file=fail_file)
                              print(f'{institution} {requirement_id} Subset copy_rules target = '
                                    f'{row.requirement_id}: {parse_tree["error"]} ',
                                    file=debug_file)
                            else:
                              local_dict = {'requirement_block': target_block,
                                            'requirement_name': row.block_title}
                              local_context = [local_dict]
                              traverse_body(body_list,
                                            context_list + requirement_context + local_context)

                case 'course_list_rule':
                  if 'course_list' not in rule.keys():
                    # Can't have a Course List Rule w/o a course list
                    print(f'{institution} {requirement_id} Subset course_list_rule w/o a '
                          f'course_list', file=fail_file)
                  else:
                    map_courses(institution, requirement_id, block_title,
                                context_list + requirement_context,
                                rule)
                    print(f'{institution} {requirement_id} Subset course_list_rule', file=log_file)

                case 'class_credit':
                  if isinstance(rule, list):
                    rule_dicts = rule
                  else:
                    rule_dicts = [rule]
                  for rule_dict in rule_dicts:
                    local_dict = get_restrictions(rule_dict)
                    try:
                      local_dict['requirement_name'] = rule_dict['label']
                    except KeyError as ke:
                      print(f'{institution} {requirement_id} '
                            f'Subset class_credit with no label', file=todo_file)
                    # for k, v in rule_dict.items():

                    #   if local_dict:
                    #     local_context = [local_dict]
                    #   else:
                    #     local_context = []
                    try:
                      map_courses(institution, requirement_id, block_title,
                                  context_list + subset_context + [local_dict],
                                  rule_dict)
                    except KeyError as err:
                      print(f'{institution} {requirement_id} {block_title} '
                            f'KeyError ({err}) in subset class_credit', file=sys.stderr)
                      exit(rule)
                  print(f'{institution} {requirement_id} Subset {key}', file=log_file)

                case 'group_requirements':
                  # This is a list of group_requirement dicts
                  print(f'{institution} {requirement_id} Subset {key}', file=log_file)
                  assert isinstance(rule, list)
                  for group_requirement in rule:
                    # This will now show up in log_file as a Body group requirement, but the context
                    # will include the subset context.
                    traverse_body(group_requirement, context_list + subset_context)

                case 'maxpassfail' | 'maxperdisc' | 'mingpa' | 'minspread' | 'noncourse' | 'share':
                  # Ignored Qualifiers and rules
                  print(f'{institution} {requirement_id} Subset {key} (ignored)', file=log_file)

                case 'proxy_advice':
                  if do_proxy_advice:
                    print(f'{institution} {requirement_id} Subset {key}', file=todo_file)
                  else:
                    print(f'{institution} {requirement_id} Subset {key} (ignored)', file=log_file)

                case _:
                  print(f'{institution} {requirement_id} Unhandled Subset {key=}: '
                        f'{str(type(rule)):10} {len(rule)}', file=sys.stderr)

        case 'remark':
          if do_remarks:
            print(f'{institution} {requirement_id} Body remark', file=todo_file)
          else:
            print(f'{institution} {requirement_id} Body remark (ignored)', file=log_file)

        case 'proxy_advice':
          if do_proxy_advice:
            print(f'{institution} {requirement_id} Body {requirement_type}', file=todo_file)
          else:
            print(f'{institution} {requirement_id} Body {requirement_type} (ignored)',
                  file=log_file)

        case 'noncourse':
          # Ignore this
          print(f'{institution} {requirement_id} Body {requirement_type} (ignored)', file=log_file)

        case _:
          # Fatal error
          exit(f'{institution} {requirement_id} Unhandled Requirement Type: {requirement_type}'
               f' {requirement_value}')
  else:
    # Another fatal error (not a list, str, or dict)
    exit(f'{institution} {requirement_id} Unhandled node type {type(node)} ({node})')


# main()
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
  """ For all recently active CUNY undergraduate plans/subplans and their requirements, generate
      CSV tables for the programs, their requirements, and course-to-requirement mappings.

      An academic plan may be eithr a major or a minor. Note, however, that minors are not required
      for a degree, but at least one major is required.

      For a plan/subplan to be mapped here, it must be recently-active as defined in activeplans.py.
      That is, it must an approved program with a current dap_req_block giving the requireents for
      the program, and there must be students currently attending the institution who have declared
      their enrollment in the plan or subplan.
  """
  start_time = datetime.datetime.now()
  parser = ArgumentParser()
  parser.add_argument('-a', '--all', action='store_true')
  parser.add_argument('-d', '--debug', action='store_true')
  parser.add_argument('--do_degrees', action='store_true')
  parser.add_argument('--do_proxy_advice', action='store_true')
  parser.add_argument('--no_remarks', action='store_true')
  parser.add_argument('-w', '--weeks', type=int, default=26)
  parser.add_argument('-p', '--progress', action='store_true')
  parser.add_argument('-t', '--timing', action='store_true')
  args = parser.parse_args()
  do_degrees = args.do_degrees
  do_proxy_advice = args.do_proxy_advice
  do_remarks = not args.no_remarks

  gestation_period = datetime.timedelta(weeks=args.weeks)
  gestation_days = gestation_period.days
  today = datetime.date.today()

  empty_tree = "'{}'"

  programs_writer.writerow(['Institution',
                            'Requirement ID',
                            'Type',
                            'Code',
                            'Title',
                            'Total Credits',
                            'Max Transfer',
                            'Min Residency',
                            'Min Grade',
                            'Min GPA',
                            'Other',
                            'Generate Date'])

  requirements_writer.writerow(['Institution',
                                'Requirement ID',
                                'Requirement Key',
                                'Program Name',
                                'Context',
                                'Generate Date'])

  map_writer.writerow(['Requirement Key',
                       'Course ID',
                       'Career',
                       'Course',
                       'With',
                       'Generate Date'])

  missing_plan_req_block_count = 0
  inactive_plan_req_block_count = 0
  new_plan_count = 0
  missing_subplan_req_block_count = 0
  inactive_subplan_req_block_count = 0
  new_subplan_count = 0
  programs_count = 0
  quarantine_plan_count = 0
  quarantine_subplan_count = 0
  block_types = defaultdict(int)

  # # These are the names of the values to obtain from the requirement_blocks, acad_plan_tbl,
  # # acad_subplan_tbl, and plan/subplan enrollment tables
  # dgw_keys = ['institution', 'requirement_id', 'block_type', 'block_value', 'block_title',
  #             'period_start', 'period_stop', 'parse_tree']
  # plan_keys = ['institution', 'plan', 'plan_type', 'description', 'effective_date', 'cip_code',
  #              'hegis_code', 'subplans', 'enrollment']

  # DGW_Row = namedtuple('DGW_Row', dgw_keys)

  # with psycopg.connect('dbname=cuny_curriculum') as conn:
  #   with conn.cursor(row_factory=namedtuple_row) as cursor:
  #     """ Use the CUNYfirst plan and subplan tables to look up all CUNY majors and minors (plans).
  #         their associated subplans (if any), and each plan's associated requirement block (if any).
  #     """
  #     missing_plan_req_block_count = 0
  #     inactive_plan_req_block_count = 0
  #     new_plan_count = 0
  #     missing_subplan_req_block_count = 0
  #     inactive_subplan_req_block_count = 0
  #     new_subplan_count = 0
  #     programs_count = 0
  #     quarantine_plan_count = 0
  #     quarantine_subplan_count = 0
  #     block_types = defaultdict(int)
  #     cursor.execute(r"""
  #     select p.*, string_agg(s.subplan,':') as subplan_names,
  #            r.requirement_id, r.block_type, r.block_value, r.title as block_title,
  #            r.period_start, r.period_stop, r.parse_date, r.parse_tree,
  #            e.enrollment
  #       from cuny_acad_plan_tbl p
  #            left join cuny_acad_plan_enrollments e
  #                   on p.institution = e.institution
  #                  and p.plan = e.plan
  #            left join cuny_acad_subplan_tbl s
  #                   on p.institution = s.institution
  #                  and p.plan = s.plan
  #            left join cuny_acad_subplan_enrollments ss
  #                   on ss.institution = s.institution
  #                  and ss.plan = s.plan
  #                  and ss.subplan = s.subplan
  #            left join requirement_blocks r
  #                   on p.institution = r.institution
  #                  and p.plan = r.block_value
  #                  and r.period_stop ~* '^9'
  #     where p.plan !~* '^(mhc|cbuis)'
  #       and p.plan ~* '\-[AB]' -- Must lead to bachelor or associate degree
  #       and p.description !~* '^Unde'
  #     group by p.institution, p.plan, p.plan_type, p.description, p.effective_date, p.cip_code,
  #              p.hegis_code, r.requirement_id, r.block_type, r.block_value, block_title,
  #              r.period_start, r.period_stop, r.parse_date, r.parse_tree, e.enrollment
  #     order by institution, plan
  #     """)
  #     num_programs = cursor.rowcount
  #     for row in cursor:
  #       if args.progress:
  #         print(f'\r{cursor.rownumber:,}/{num_programs:,} programs {row.institution[0:3]}', end='')

  #       # plan_dict collects fields from the plan and plan_enrollments tables
  #       plan_dict = dict()
  #       # dgw_dict is used to determine current-active requirement blocks
  #       dgw_dict = dict()

  #       # Populate the plan_dict and dgw_dict for this row
  #       for key, value in row._asdict().items():
  #         if key in plan_keys:
  #           plan_dict[key] = str(value) if key.endswith('date') else value
  #           # Convert the string_agg of subplan names to a list of names
  #           subplans_list = []
  #           if key == 'subplan_names':
  #             if value is None:
  #               pass
  #             else:
  #               subplans_list.append(value.split(':'))
  #             plan_dict['subplans'] = subplans_list

  #         if key in dgw_keys:
  #           dgw_dict[key] = str(value) if key.endswith('date') else value

  #       # Skip Macaulay Honors College programs
  #       # ... these were already filtered out by the query above
  #       # if plan_dict['plan'].lower().startswith('mhc'):
  #       #   mhc_count += 1
  #       #   continue

  #       # If there is no requirement_block, this plan is done
  #       if row.requirement_id is None:
  #         # Log the issue
  #         print(f"  {plan_dict['institution']} {plan_dict['plan']:12} {plan_dict['plan_type']} "
  #               f"{plan_dict['description']}", file=missing_file)
  #         missing_plan_req_block_count += 1
  #         continue

  #       # Note plans with zero enrollment, which might be too new to have students yet.
  #       last_change = max(row.parse_date, row.effective_date)
  #       if row.enrollment is None and (today - last_change) < gestation_period:
  #         print(f"  {plan_dict['institution']} {plan_dict['plan']:12} {plan_dict['plan_type']} "
  #               f"{plan_dict['description']}", file=new_plan_file)
  #         new_plan_count += 1
  #       else:
  #         # Is this an active requirement block, per ir_dgw_active_blocks?
  #         try:
  #           plan_info = active_plans[(row.institution, plan_dict['plan'])]
  #         except KeyError:
  #           # Plan not active: log the situation and ignore the plan
  #           print(f"  {plan_dict['institution']} {plan_dict['plan']:12} {plan_dict['plan_type']} "
  #                 f"{plan_dict['description']}", file=inactive_plan_file)
  #           inactive_plan_req_block_count += 1
  #           continue

  #         # Log, and skip plans where the scribe block has parse errors
  #         if quarantine_dict.is_quarantined((row.institution, row.requirement_id)):
  #           print(f'{row.institution} {row.requirement_id} Quarantined plan req_block',
  #                 file=fail_file)
  #           quarantine_plan_count += 1
  #           continue

  #         # We have a plan ...
  #         plan_dict['requirement_id'] = row.requirement_id

  #         # ... retain only those subplans that have and active req_block or are too new to attract
  #         # students yet.
  #         for subplan in plan_dict['subplans']:
  #           print(row.institution, row.requirement_id, plan_dict['plan'], subplan)
  #           # Find the dap_req_block for this plan, which could be multiple or missing (errors)...

  #           # Be sure the dap_req_block is active

  #         # Process the scribe block for this program, subject to command line exclusions and errors

  #         dgw_row = DGW_Row._make([dgw_dict[k] for k in dgw_keys])
  # process_block(dgw_row, context_list=[], plan_info={'plan_info': plan_dict})

  for acad_plan in active_plans():
    programs_count += 1
    requirement_block = acad_plan['requirement_block']
    block_types[requirement_block['block_type']] += 1
    if requirement_block['block_type'] not in ['MAJOR', 'MINOR']:
      # We can handle this, but it should be noted.
      print(f"{requirement_block['institution']} {requirement_block['requirement_id']} "
            f"{requirement_block['block_value']} with block type {requirement_block['block_type']}",
            file=anomaly_file)
    process_block(requirement_block, context_list=[], plan_dict=acad_plan)
    # process_block(dgw_row, context_list=[], plan_info={'plan_info': plan_dict})

  if args.progress:
    print()
  s = '' if args.weeks == 1 else 's'
  print(f'{programs_count:5,} Blocks')
  for k, v in block_types.items():
    print(f'{v:5,} {k.title()}')
  print(f'-----\n'
        f'{missing_plan_req_block_count:5,} Missing plan dgw_req_block\n'
        f'{inactive_plan_req_block_count:5,} Inactive plan dgw_req_block\n'
        f'{new_plan_count:5,} Zero-enrollment plan less than {gestation_days} days old\n'
        f'{missing_subplan_req_block_count:5,} Missing subplan dgw_req_block\n'
        f'{inactive_subplan_req_block_count:5,} Inactive subplan dgw_req_block\n'
        f'{new_subplan_count:5,} Zero-enrollment subplan less than {gestation_days} days old\n')
  with open('block_counts.txt', 'w') as counts_file:
    print('Block                   Count', file=counts_file)
    for key, value in dap_block_counts.items():
      if value > 1:
        i, r, t = key
        print(f'{i} {r} {t:7} {value:2}', file=counts_file)
  if args.timing:
    print(f'{(datetime.datetime.now() - start_time).seconds} seconds')
