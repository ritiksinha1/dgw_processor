#! /usr/local/bin/bash

# Combine duplicate rows from header_body_report text file into a "sumary" CSV file.
# The first row of the report is the CSV header; other rows are CSV values, but begin with the
# institution and requirement id, which have to be dropped. And omit rows for cross-listed and
# equivalency groups.

head -1 header_body_report.txt > header_row
tail -n+1 header_body_report.txt | ack -v 'CROSS|EQUIV' | cut -c 15- | sort | uniq -c | \
  sort -r > body_rows
cat header_row body_rows > header_body_summary.csv
rm -f header_row body_rows
