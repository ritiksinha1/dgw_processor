#! /usr/local/bin/python3

from pgconnection import PgConnection

block_type = 'MAJOR'

conn = PgConnection()
cursor = conn.cursor()

cursor.execute('select code from cuny_institutions')
for row in cursor.fetchall():
  college = row.code
  print(college)
  query = f"""
    select institution, block_type, block_value, requirement_text
    from requirement_blocks
    where institution = '{college}'
    and block_type = '{block_type}'
    and period_stop = '99999999'
    """

  cursor.execute(query)
  if cursor.rowcount > 0:
    with open(f'{row.code.lower()[0:3]}_majors', 'w') as outfile:
      for row in cursor.fetchall():
        program = row.block_value
        if program == '?' or program.isdecimal() or program.startswith('UNDECL'):
          continue
        print(college, block_type, program, file=outfile)
