#! /usr/local/bin/python3
""" Count the sizes of the test_result files.
    Tell what percentage were length 0, indicating complete parsing.
    Report CUNY-wide (highlighted) as well as individual colleges’ results.
"""
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict, namedtuple

highlight_on = '\u001b[31m'  # Red Text
highlight_off = '\u001b[0m'

if os.getenv('DEBUG'):
  logfile = sys.stderr
else:
  time_stamp = str(datetime.now()).replace(' ', '_').rstrip('0123456789').rstrip('.')
  logfile = open(f'count_results_{time_stamp}.log', 'w')

colleges = 'bar bcc bkl bmc csi cty hos htr jjc lag leh mec ncc nyt qcc qns slu sps yrk'.split()
block_types = 'major minor conc degree other'.split()
college_data = {}
for college in colleges:
  college_data[college] = {}
  for block_type in block_types:
    college_data[college][block_type] = {'blocks': 0,
                                         'correct': 0,
                                         'timeouts': 0,
                                         'lines': 0,
                                         'seconds': 0.0}

with open('./run_tests.csv') as csv_file:
  reader = csv.DictReader(csv_file, delimiter='\t')
  for line in reader:
    college = line['Block'].split('_')[0].lower().strip('01')
    block_type = line['Type']
    college_data[college][block_type]['blocks'] += 1
    if line['Messages'] == 'timeout':
      college_data[college][block_type]['timeouts'] += 1
    else:
      college_data[college][block_type]['lines'] += int(line['Lines'])
      college_data[college][block_type]['seconds'] += float(line['Seconds'])
      if int(line['Messages']) == 0:
        college_data[college][block_type]['correct'] += 1

for block_type in block_types:
  all_blocks = 0
  all_correct = 0
  all_timeouts = 0
  all_lines = 0
  all_seconds = 0.0
  for college in colleges:
    try:
      num_blocks = college_data[college][block_type]['blocks']
      all_blocks += num_blocks
      num_correct = college_data[college][block_type]['correct']
      all_correct += num_correct
      num_timeouts = college_data[college][block_type]['timeouts']
      all_timeouts += num_timeouts
      num_lines = college_data[college][block_type]['lines']
      all_lines += num_lines
      num_seconds = college_data[college][block_type]['seconds']
      all_seconds += num_seconds
      rate = num_lines / num_seconds
      s = 's; ' if num_timeouts != 1 else ';  '
      print(f'{college}: {num_blocks:5,} {block_type} blocks;'
            f' {100 * num_correct / num_blocks:5.1f}% correct,'
            f' {num_timeouts:>2} timeout{s} {rate:5.1f} lines per second.', file=logfile)
    except ZeroDivisionError:
      pass
  try:
    all_rate = all_lines / all_seconds
    print(f'{highlight_on}ALL{highlight_off}: {all_blocks:5,} {block_type} blocks;'
          f' {100 * all_correct / all_blocks:5.1f}% correct,'
          f' {all_timeouts:>2} timeout{s} {all_rate:5.1f} lines per second.\n', file=logfile)
  except ZeroDivisionError:
    pass
