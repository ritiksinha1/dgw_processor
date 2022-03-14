#! /usr/local/bin/bash

echo `date` > reports.txt
for r in log todo no_courses fail debug
do
    echo $r | tr a-z A-Z >> reports.txt
    cut -c 16- course_mapper.${r}.txt|sort|uniq -c|sort -r >> reports.txt
done
