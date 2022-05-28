#! /usr/local/bin/bash

tail -n+2 header_body_summary.csv |cut -c 10- > patterns

while read
do echo $REPLY
   ack "$REPLY" header_body_report.txt | cut -c 1-14|sort|uniq
done <patterns
rm patterns