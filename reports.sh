#! /usr/local/bin/bash

echo `date` > reports.txt
for r in log todo fail debug no_courses
do
    echo $r | tr a-z A-Z >> reports.txt
    cut -c 16- ${r}.txt|sort|uniq -c|sort -r >> reports.txt
done
