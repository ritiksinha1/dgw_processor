#! /usr/local/bin/bash

# Combine duplicate rows from header_body_report text file into a "sumary" CSV file.
# The first row of the report is the CSV header; other rows are CSV values, but begin with the
# institution and requirement id, which have to be dropped. And omit rows for cross-listed and
# equivalency groups.

(
 cd /Users/vickery/Projects/dgw_processor/Tech_Reports
SECONDS=0
# Save the CSV header row from the report
head -1 header_body_report.txt > header_row

# Show number of blocks containing potential redundancies
echo Generate header_body_summary.csv
tail -n+2 header_body_report.txt | ack 'CROSS|EQUIV|MATCH' | cut -c 37- | sort | uniq -c | sort -r
tail -n+2 header_body_report.txt | ack -v 'CROSS|EQUIV|MATCH' | cut -c 24- | sort | uniq -c | \
  sort -r > body_rows
cat header_row body_rows > header_body_summary.csv
rm -f header_row body_rows
echo $SECONDS sec.
SECONDS=0
echo -e "\nGenerate patterns_to_blocks.txt"
patterns_to_blocks.sh > patterns_to_blocks.txt
echo $SECONDS sec.
)