#! /usr/local/bin/bash

# For each pattern in header_body_summary.csv, list the blocks where it occurred.
# Output is in the same order as the in the csv file: decreasing frequency with which the pattern
# occurred.
(
  cd /Users/vickery/Projects/dgw_processor/Tech_Reports

  # Extract the patterns found in header_body_summary, without the frequencies at the beginning
  tail -n+2 header_body_summary.csv |cut -c 10- > patterns

  # For each pattern, print the pattern, followed by the block(s) where it was found.
  while read
  do echo $REPLY|tr -d ' '|tr ',' '-'
    ack "$REPLY" header_body_report.txt | cut -c 1-14|sort|uniq|sed "s/^/  /"
  done <patterns
  rm patterns
)
