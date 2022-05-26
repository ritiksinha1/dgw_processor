#! /usr/local/bin/bash

# Combine duplicate rows from header_body_summary CSV file.
head -1 header_body_summary.txt > header_row
tail -n+1 header_body_summary.txt | sort |uniq -c | sort -r > body_rows
cat header_row body_rows > header_body_summary.csv
