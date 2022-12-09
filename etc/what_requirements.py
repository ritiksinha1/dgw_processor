#! /usr/local/bin/python3
""" Given a list of course_ids or (institution, discipline, catalog_number) tuples, generate a list
    of requirements each course satisfies.
    A "requirement" is a program name and requirement name., but does not show the requirement
    structure.
"""

import psycopg
import sys

from psycopg.rows import namedtuple_row

with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=namedtuple_row) as course_cursor:
    with conn.cursor(row_factory=namedtuple_row) as requirement_cursor:
      # The input list comes from stdin
      while line := sys.stdin.readline():
        parts = line.split()
        match len(parts):
          case 1:
            course_id = parts[0]
            course_cursor.execute("""
            select course_id, offer_nbr, institution, discipline, catalog_number,
                   designation, attributes
              from cuny_courses
             where course_id = %s
            """, (course_id, ))
            offer_nbrs = []
            for row in course_cursor:
              offer_nbrs.append(row.offer_nbr)
              if row.attributes != 'None':
                attributes = row.attributes.split(';')
                attributes = ', '.join([a.split(':')[1] for a in attributes])

              else:
                attributes = 'None'
              print(f'{row.course_id:06}:{row.offer_nbr} {row.institution[0:3]} {row.discipline:>6} '
                    f'{row.catalog_number:6} {row.designation:5} {attributes:64}', end='')

              requirement_cursor.execute("""
              select p.type, p.code, r.context
                from course_mappings.mappings m,
                     course_mappings.programs p,
                     course_mappings.requirements r
                where m.course_id = %s
                  and r.requirement_key = m.requirement_key
                  and p.requirement_id = r.requirement_id
              """, (course_id, ))
              if requirement_cursor.rowcount == 0:
                print('  No major/minor requirements')
              else:
                for row in requirement_cursor:
                  context = row.context
                  print(f'{row.type} {row.code:10} {context[-1]["requirement_name"]}')

          case 3:
            print('not yet')

          case _:
            print(f'Expected 1 or three parts. “{line}” has {len(parts)}')

      """
==> ../course_mapper.course_mappings.csv <==
Requirement Key,Course ID,Career,Course,With,Generate Date

==> ../course_mapper.programs.csv <==
Institution,Requirement ID,Type,Code,Title,Total Credits,Max Transfer,Min Residency,Min Grade,Min GPA,Other,Generate Date

==> ../course_mapper.requirements.csv <==
Institution,Requirement ID,Requirement Key,Program Name,Context,Generate Date

      """
