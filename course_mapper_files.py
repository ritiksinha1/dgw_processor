#! /usr/local/bin/python3
""" Logging/Development Report files
      anomaly_file        Things that look wrong, but we handle anyway
      blocks_file         List of blocks processed
      fail_file           Blocks that failed for one reason or another
      log_file            Record of requirements processed successfully. Bigger is better!
      no_courses_file     Requirements with no course lists.
      subplans_file       What active subplans are (not) referenced?
      todo_file           Record of all known requirements not yet handled. Smaller is better!

    Data files for T-Rex
      programs_file       Spreadsheet of info about majors, minors, and concentrations
      requirements_file   Spreadsheet of program requirement names
      mapping_file        Spreadsheet of course-to-requirements mappings

"""
anomaly_file = open('/Users/vickery/Projects/dgw_processor/anomalies.txt', 'w')
blocks_file = open('/Users/vickery/Projects/dgw_processor/blocks.txt', 'w')
fail_file = open('/Users/vickery/Projects/dgw_processor/fail.txt', 'w')
log_file = open('/Users/vickery/Projects/dgw_processor/log.txt', 'w')
no_courses_file = open('/Users/vickery/Projects/dgw_processor/no_courses.txt', 'w')
subplans_file = open('/Users/vickery/Projects/dgw_processor/subplans.txt', 'w')
todo_file = open(f'/Users/vickery/Projects/dgw_processor/todo.txt', 'w')

programs_file = open(f'{__file__.replace(".py", ".programs.csv")}', 'w', newline='')
requirements_file = open(f'{__file__.replace(".py", ".requirements.csv")}', 'w', newline='')
mapping_file = open(f'{__file__.replace(".py", ".course_mappings.csv")}', 'w', newline='')
