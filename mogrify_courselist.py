#! /usr/local/bin/python3
"""
"""

from collections import namedtuple
from courses_cache import courses_cache

log_file = open('/Users/vickery/Projects/dgw_processor/log.txt', 'w')
todo_file = open(f'/Users/vickery/Projects/dgw_processor/todo.txt', 'w')

MogrifiedInfo = namedtuple('MogrifiedInfo', 'course_id_str course_str career with_clause')


# mogrify_course_list()
# -------------------------------------------------------------------------------------------------
def mogrify_course_list(institution: str, requirement_id: str, course_dict: dict) -> list:
  """
      This gets called from traverse_header (max_classes, max_credits), and map_courses (via various
      body rules) to turn a scribed course_list into information needed for populating the programs
      table (header info) or mapping table (body rules).

      First flatten the dict of scribed courses to get rid of the areas structure.
        Log cases where there is more than one area
      Create a set of courses (eliminates duplicates)
      Use courses_cache() to look up catalog_information for each course in the courses set.
      The courses_cache handles wildcard expansion.

      Use courses_cache to look up catalog information for all matchig courses for each course in
      the exclude list.
      Remove excluded courses from the courses_set.
      Distribute certain with_clauses onto courses; ignore others
      return the list of CourseInfo items.

  The course_dict has three course lists to be managed: scribed, include, and exclude. (Terminology
  note: the Scribe language uses “except” for what I’m calling “exclude.”) The include and exclude
  lists may be empty. Each list consists of 3-tuples: {discipline, catalog_number, with-clause}.
  Disciplines and catalog numbers can contain wildcards (@), and catalog_numbers can specify ranges
  (:). With-clauses are optional (i.e., can be None).

  We ignore include lists here, but log them for possible future action.

  With-clauses in the scribed list are distributed across all courses in the list after wildcard and
  range expansion.

  With-clauses might or might not be significant. Based on samples examined (see below), two cases
  are currently logged but otherwise ignored: references to DWTerm (because they seem to refer to
  special policies during the COVID pandemic) and references to course attributes. Attributes might
  actually specify requirements, such as writing intensive courses, although the cases seen so far
  only apply to some hidden requirements referring to Pathways requirements. Note, however, that the
  use of ATTRIBUTE=FCER, etc. in the examples found don't make sense: FCER is a requirement
  designation, not a course attribute.

  Sample cases encountered across CUNY:

    CSI01 RA001460 Exclude course based on DWTerm (ignored)
      MaxCredits 0 in @ @ (With DWPassfail=Y)
        Except @ @ (With DWTerm = 1202) # allow p/f classes in spring 2020 to apply

    CTY01 RA000718 Exclude course
      MaxCredits 6 in @ @ (With DWTransfer=Y)
      EXCEPT PHYS 20300, 20400, 20700, 20800 ## Updated as of 1/13/20

    HTR01 RA002566 Exclude course
      MaxCredits 30 in ARTCR 1@, 2@, 3@, 4@ Except ARTCR 10100

    HTR01 RA002617 Exclude course
      MaxCredits 3 in ECO 1@ Except ECO 10000

    NYT01 RA000727
      BeginSub
            2 Classes in ARTH 1@, AFR 1301, 1304
        Label 1.1 "ARTH 1100-SERIES OR AFR 1301, 1304";
            1 Class in ARTH 3311,
              {HIDE @ (WITH ATTRIBUTE=FCER and DWTransfer = Y),}
              {HIDE @ (WITH ATTRIBUTE=FCEC and DWTransfer = Y),}
              {HIDE @ (WITH ATTRIBUTE=FCED and DWTransfer = Y)}
       RuleTag Category=FCCE1
       Label 1.2 "Creative Expression";
      EndSub
       Label 1.0 "Required Gen. Ed.";
         Remark "Transferred students are allowed to fulfill the Creative Expression area with any
         approved Creative Expression from their prior school.";

  """
  # There has to be a course_dict to mogrify
  assert course_dict, 'Empty course_dict in mogrify_course_dict'

  # Log non-empty include lists
  if course_dict['include_courses']:
    print(f'{institution} {requirement_id} Non-empty include_courses (ignored)', file=log_file)

  # Get the scribed list, which is divided into areas even if there are nont, and flatten it.
  course_list = course_dict['scribed_courses']
  # Course tuples are (0: discipline, 1: catalog_number, 2: with_clause)
  course_tuples = [tuple(course) for area in course_list for course in area]
  # Get rid of redundant scribes
  course_tuples_set = set([course_tuple for course_tuple in course_tuples])

  # Create a set of active courses and a dict of corresponding with-clauses
  course_info_set = set()
  with_clauses = dict()
  for course_tuple in course_tuples_set:
    course_infos = courses_cache(institution, course_tuple[0], course_tuple[1])
    for course_info in course_infos:
      if course_tuple[2]:
        with_clause = course_tuple[2].lower()
        if 'dwterm' in with_clause or 'attribute' in with_clause:
          continue
        with_key = (course_info.course_id, course_info.offer_nbr)
        if with_key in with_clauses.keys() and with_clauses[with_key] != course_tuple[2].lower():
          print(f'{institution} {requirement_id} Mogrify: multiple with-clauses. '
                f'{with_clauses[with_key]} != {course_tuple[2].lower()}',
                file=debug_file)
        with_clauses[with_key] = course_tuple[2].lower()
      course_info_set.add(course_info)

  # Create set of exclude courses (there is no areas structure in exclude lists)
  exclude_list = course_dict['except_courses']
  exclude_tuples_set = set([tuple(course) for course in exclude_list])
  exclude_info_set = set()
  for exclude_tuple in exclude_tuples_set:
    course_infos = courses_cache(institution, exclude_tuple[0], exclude_tuple[1])
    for course_info in course_infos:
      exclude_info_set.add(course_info)

  if len(exclude_info_set):
    print(f'{institution} {requirement_id} Non-empty exclude list', file=log_file)

  # Log any with-clauses in the exclude list to determine whether they need to be dealt with.
  for discipline, catalog_number, with_clause in exclude_list:
    if with_clause:
      # Ignore cases where the with clause references DWTerm: they look like COVID special cases,
      # and even if they are not, they can’t be “program requirements”
      if 'dwterm' in with_clause.lower():
        print(f'{institution} {requirement_id} Exclude course based on DWTerm (ignored)',
              file=log_file)
      else:
        # Log and skip remaining cases that have with-expressions
        """ If there is a grade or transfer restriction, one might be able to invert it and simply
            add it to the with clause of all the scribed_courses. But for now, we're just finding
            out whether it is a real issue or not.
        """
        print(f'{institution} {requirement_id} mogrify_course_list(): exclude with {with_clause}',
              file=todo_file)

  # Remove excluded courses from the courses
  course_info_set -= exclude_info_set

  return_list = []
  for course in course_info_set:
    with_key = (course_info.course_id, course_info.offer_nbr)
    with_clause = with_clauses[with_key] if with_key in with_clauses.keys() else ''
    # MogrifiedInfo = namedtuple('MogrifiedInfo', 'course_id_str course_str career with_clause')
    mogrified_info = MogrifiedInfo._make([f'{course.course_id:06}:{course.offer_nbr}',
                                          f'{course.discipline} {course.catalog_number}: '
                                          f'{course.course_title}',
                                          course.career,
                                          with_clause])
    return_list.append(mogrified_info)
  return return_list
