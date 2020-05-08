#! /usr/local/bin/python3
""" Look up the requirement blocks for all active majors and save them in the test_data directory.
"""
from pathlib import Path
from pgconnection import PgConnection
import re

conn = PgConnection()
cursor = conn.cursor()

cursor.execute('select * from requirement_blocks order by institution, requirement_id')
print(cursor.rowcount)
count = 0
for block in cursor.fetchall():
  if block.block_type == 'MAJOR' and block.period_stop == '99999999':
    count += 1
    title_str = re.sub(r'\s$', '', re.sub(r'_+', '_', re.sub(r'[\][\(\):/\& ]', '_', block.title)))
    file = Path('test_data/',
                f'{block.institution}_{block.requirement_id}_{title_str}')
    file.write_text(re.sub(r'[Ee][Nn][Dd]\.(.|\n)*', 'END.\n', block.requirement_text))
print(count)
