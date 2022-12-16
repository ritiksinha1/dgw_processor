#! /usr/local/bin/python3
""" Read from stdin a list of course_ids or (institution, discipline, catalog_number) tuples,
    generate a list of requirements each course satisfies. A "requirement" is a program name and
    requirement name., but does not show the requirement structure.
"""

import psycopg
import sys

from argparse import ArgumentParser
from psycopg.rows import namedtuple_row


def show_requirements(course_id_str: str, full_context=False) -> list:
  """ Given
  """
  return_list = []

  condition_str = ''
  num_groups = 0
  num_required = 0
  group_number = 0

  with psycopg.connect(dbname='cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as requirements_cursor:

      requirements_cursor.execute("""
      select r.context, r.requirement_id
        from course_mappings.requirements r
        where r.requirement_key in (select requirement_key
                                      from course_mappings.mappings
                                     where course_id = %s)
        order by r.requirement_key
      """, (course_id_str, ))

      if requirements_cursor.rowcount == 0:
        return_list.append('  No major/minor requirements')

      for requirement_row in requirements_cursor:
        context_list = requirement_row.context

        if not full_context:
          # Show the plan/sub-plan(s) and last requirement_name in the context chain
          requirement_name = None
          depth = 0
          for index in range(len(context_list) - 1, -1, -1):
            if 'requirement_name' in context_list[index].keys():
              requirement_name = context_list[index]['requirement_name']
              break
            elif 'requirement' in context_list[index].keys():
              requirement_name = context_list[index]['requirement']['label']
              break

          if requirement_name is not None:
              # # Ignore intermediate "marker" items
              # if requirement_name in ['if_true', 'if_false', 'condition', 'group_requirement',
              #                         'num_groups', 'num_required', 'group_number',
              #                         'group_number_str']:
              #   continue
              for j in range(index):
                try:
                  requirement_id = context_list[j]['block_info']['requirement_id']
                  block_type = context_list[j]['block_info']['block_type']
                  block_title = context_list[j]['block_info']['block_title']
                  enrollment = context_list[j]['block_info']['plan_info']['plan_enrollment']
                  s = ' ' if enrollment == 1 else 's'
                  if j == 0:
                    return_list.append('')
                  return_list.append(f'{requirement_id} {block_type} ({enrollment:,} student{s}) '
                                     f'“{block_title}”')
                except KeyError:
                  pass
              return_list.append(f'{requirement_id} {requirement_name}')

          else:
            return_list.append(f'Error: no requirement_name found in {len(context_list)} contexts')

        else:
          # Show entire context chain
          depth = 0
          requirement_id = requirement_row.requirement_id
          # Mark the beginning of a requirement chain
          return_list.append('')

          for context in context_list:
            for key, value in context.items():

              match key:

                case 'block_info':
                  depth += 1
                  leader = depth * '  '
                  requirement_id = value['requirement_id']
                  block_type = value['block_type']
                  block_title = value['block_title']
                  if 'plan_info' in value.keys():
                    enrollment = value['plan_info']['plan_enrollment']
                  elif 'subplan' in value.keys():
                    enrollment = value['subplan']['subplan_enrollment']
                  else:
                    enrollment = None
                  return_list.append(f'{requirement_id}{leader}{block_type} “{block_title}” '
                                     f'({enrollment:,} students) ')

                case 'if_true':
                  depth += 1
                  leader = depth * '  '
                  return_list.append(f'{requirement_id} {leader}If {value} is TRUE')

                case 'if_false':
                  depth += 1
                  leader = depth * '  '
                  return_list.append(f'{requirement_id} {leader}If {value} is FALSE')

                case 'mingrade':
                  depth += 1
                  leader = depth * '  '
                  return_list.append(f'{requirement_id}{leader}Minimum grade of {value} required')

                case 'num_groups':
                  num_groups = value

                case 'num_required':
                  depth += 1
                  leader = depth * '  '
                  num_required = value
                  s = '' if num_required == 1 else 's'
                  return_list.append(f'{requirement_id}{leader}{num_required} Group{s} required')

                case 'group_number':
                  # ss = '' if num_groups == 1 else 's'
                  # return_list.append(f'{requirement_id}{leader}Group {group_number + 1} of '
                  #                    f'{num_required} required group{s} out of {num_groups} '
                  #                    f'group{ss}')
                  pass

                case 'group_number_str':
                  return_list.append(f'{requirement_id}{leader}{value}')

                case 'remark':
                  # Ignore
                  pass

                case 'requirement':
                  # Ignore: this the label was already handled as 'requirement_name'
                  pass

                case 'requirement_name':
                  depth += 1
                  leader = depth * '  '
                  if value == 'if_true':
                    return_list.append(f'{requirement_id}{leader}If {condition_str} is TRUE')
                  elif value == 'if_false':
                    return_list.append(f'{requirement_id}{leader}If {condition_str} is FALSE')
                  else:
                    return_list.append(f'{requirement_id}{leader}{value}')

                case _:
                  return_list.append(f'{requirement_id}{leader}{key=}??')

  return return_list


if __name__ == '__main__':

  parser = ArgumentParser()
  parser.add_argument('-c', '--full_context', action='store_true')
  parser.add_argument('-p', '--prompt_str', default='')
  args = parser.parse_args()

  with psycopg.connect('dbname=cuny_curriculum') as conn:
    with conn.cursor(row_factory=namedtuple_row) as course_cursor:
      # The input list comes from stdin
      print(args.prompt_str, end='')
      sys.stdout.flush()
      while line := sys.stdin.readline():

        command = line.lower().strip()
        if command in ['q', '']:
          # Quit
          exit()
        if command == '-c':
          # Toggle compact mode
          args.full_context = not args.full_context
          print('Full context is', args.full_context)
          continue

        parts = command.split()
        match len(parts):

          case 1:
            course_id = f'{int(parts[0]):06}'

            course_cursor.execute("""
            select course_id, offer_nbr, institution, discipline, catalog_number,
                   designation, attributes
              from cuny_courses
             where course_id = %s
               and course_status = 'A'
            """, (course_id, ))

          case 3:
            institution, discipline, catalog_number = parts
            course_cursor.execute("""
            select course_id, offer_nbr, institution, discipline, catalog_number,
                   designation, attributes
              from cuny_courses
             where institution ~* %s
               and discipline ~* %s
               and catalog_number ~* %s
               and course_status = 'A'
            """, parts)

          case _:
            print(f'Expected 1 or three parts. “{command}” has {len(parts)}')

        if course_cursor.rowcount == 0:
          return_list.append(f'{course_id} not found')
          continue

        for row in course_cursor:
          course_id = str(row.course_id)
          course_id_str = f'{row.course_id:06}:{row.offer_nbr}'
          if row.attributes != 'None':
            attributes = row.attributes.split(';')
            attributes = ', '.join([a.split(':')[1] for a in attributes])

          else:
            attributes = 'None'

          print(f'{course_id_str} {row.institution[0:3]} {row.discipline:>6} '
                f'{row.catalog_number:6} {row.designation:5} {attributes}')
          print('\n'.join(show_requirements(course_id_str, args.full_context)))
          print(args.prompt_str, end='')
          sys.stdout.flush()
