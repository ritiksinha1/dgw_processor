#! /usr/local/bin/python3
""" Given a list of course_ids or (institution, discipline, catalog_number) tuples, generate a list
    of requirements each course satisfies.
    A "requirement" is a program name and requirement name., but does not show the requirement
    structure.
"""

import psycopg
import sys

from argparse import ArgumentParser
from psycopg.rows import namedtuple_row


parser = ArgumentParser()
parser.add_argument('-c', '--full_context', action='store_true')
parser.add_argument('-o', '--output_file', default=None)
args = parser.parse_args()

if args.output_file:
  out_file = open(args.output_file, 'w')
else:
  out_file = sys.stdout

condition_str = ''
num_groups = 0
num_required = 0
group_number = 0


def show_requirements(requirement_cursor):
  """ Given an open cursor
  """
  for requirement_row in requirement_cursor:
    if args.full_context:
      context_list = requirement_row.context
      leader = f'{requirement_row.requirement_id}'
      for context in context_list:
        for key, value in context.items():
          match key:

            case 'block_info':
              leader += '  '
              block_type = value['block_type']
              block_title = value['block_title']
              print(f'\n{leader} {block_type} “{block_title}”', file=out_file)

            case 'condition':
              condition_str = value

            case 'mingrade':
              leader += '  '
              print(f'{leader} Minimum grade of {value} required', file=out_file)

            case 'num_groups':
              num_groups = value

            case 'num_required':
              num_required = value

            case 'group_number':
              leader += '  '
              s = '' if num_required == 1 else 's'
              ss = '' if num_groups == 1 else 's'
              print(f'{leader}Group {group_number + 1} of {num_required} required '
                    f'group{s} out of {num_groups} alternative{ss}', file=out_file)
            case 'remark':
              # Ignore
              pass

            case 'requirement':
              # Ignore: this the label was already handled as 'requirement_name'
              pass

            case 'requirement_name':
              leader += '  '
              if value == 'if_true':
                print(f'{leader}If {condition_str} is TRUE', file=out_file)
              elif value == 'if_false':
                print(f'{leader}If {condition_str} is FALSE', file=out_file)
              else:
                print(leader, value, file=out_file)

            case _:
              print(f'{leader} {key=}??')


with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as course_cursor:
    with conn.cursor(row_factory=namedtuple_row) as requirement_cursor:
      # The input list comes from stdin
      while line := sys.stdin.readline():

        if line.lower().strip() == 'q':
          exit()

        parts = line.split()
        match len(parts):
          case 0:
            # Ignore blank lines
            pass

          case 1:
            course_id = f'{int(parts[0]):06}'

            course_cursor.execute("""
            select course_id, offer_nbr, institution, discipline, catalog_number,
                   designation, attributes
              from cuny_courses
             where course_id = %s
               and course_status = 'A'
            """, (course_id, ))

            if course_cursor.rowcount == 0:
              print(f'{course_id} not found', file=out_file)

            offer_nbrs = []
            for row in course_cursor:
              course_id = str(row.course_id)
              offer_nbrs.append(row.offer_nbr)
              if row.attributes != 'None':
                attributes = row.attributes.split(';')
                attributes = ', '.join([a.split(':')[1] for a in attributes])

              else:
                attributes = 'None'
              print(f'{row.course_id:06}:{row.offer_nbr} {row.institution[0:3]} {row.discipline:>6} '
                    f'{row.catalog_number:6} {row.designation:5} {attributes}', file=out_file)

              for offer_nbr in offer_nbrs:
                course_id_str = f'{int(row.course_id):06}:{offer_nbr}'
                requirement_cursor.execute("""
                select p.type, p.code, r.context, r.requirement_id
                  from course_mappings.mappings m,
                       course_mappings.programs p,
                       course_mappings.requirements r
                  where m.course_id = %s
                    and r.requirement_key = m.requirement_key
                    and p.requirement_id = r.requirement_id
                """, (course_id_str, ))
                if requirement_cursor.rowcount == 0:
                  print('  No major/minor requirements', file=out_file)
                else:
                  show_requirements(requirement_cursor)

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

            if course_cursor.rowcount == 0:
              print(f'{line.strip()}: not found', file=out_file)

            offer_nbrs = []

            for row in course_cursor:

              course_id = str(row.course_id)

              offer_nbrs.append(row.offer_nbr)
              if row.attributes != 'None':
                attributes = row.attributes.split(';')
                attributes = ', '.join([a.split(':')[1] for a in attributes])
              else:
                attributes = 'None'

              print(f'\n{row.course_id:06}:{row.offer_nbr} {row.institution[0:3]} '
                    f'{row.discipline:>6} {row.catalog_number:6} {row.designation:5} {attributes}',
                    file=out_file)

              for offer_nbr in offer_nbrs:
                course_id_str = f'{int(row.course_id):06}:{offer_nbr}'
                requirement_cursor.execute("""
                select p.type, p.code, r.context, r.requirement_id
                  from course_mappings.mappings m,
                       course_mappings.programs p,
                       course_mappings.requirements r
                  where m.course_id = %s
                    and r.requirement_key = m.requirement_key
                    and p.requirement_id = r.requirement_id
                """, (course_id_str, ))

                if requirement_cursor.rowcount == 0:
                  print('  No major/minor requirements', file=out_file)

                else:
                  show_requirements(requirement_cursor)

          case _:
            print(f'Expected 1 or three parts. “{line}” has {len(parts)}')
