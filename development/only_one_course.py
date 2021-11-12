#! /usr/local/bin/python3

import csv
from pgconnection import PgConnection

conn = PgConnection()
cursor = conn.cursor()

cursor.execute("""
  select r.institution,
         r.requirement_id,
         p.block_type,
         p.block_value,
         r.requirement_name,
         r.num_courses_required,
         r.num_credits_required,
         string_agg(c.discipline||' '||c.catalog_number, ',') as courses
    from program_requirements r, course_requirement_mappings m, cuny_courses c, requirement_blocks p
   where r.id = m.program_requirement_id
     and c.course_id = m.course_id
     and p.institution = r.institution
     and p.requirement_id = r.requirement_id
group by r.institution, r.requirement_id, r.requirement_name, p.block_type, p.block_value,
         r.num_courses_required, r.num_credits_required
order by r.institution, block_type, block_value
  """)
with open('only_one_course.csv', 'w') as csvfile:
  writer = csv.writer(csvfile)
  writer.writerow(['College', 'Requirement ID', 'Block Type', 'Block Value', 'Requirement Name',
                  'Course', 'Courses Required', 'Credits Required'])
  for row in cursor.fetchall():
    courses = row.courses.split(',')
    if len(courses) == 1:
      writer.writerow([row.institution, row.requirement_id, row.block_type, row.block_value,
                      row.requirement_name, courses[0], row.num_courses_required,
                      row.num_credits_required])
