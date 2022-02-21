#! /usr/local/bin/bash

echo `date` > reports.txt
for r in debug log fail
do
    echo $r >> reports.txt
    cut -c 16- course_mapper.${r}.txt|sort|uniq -c|sort -r >> reports.txt
done
