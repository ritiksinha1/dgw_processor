#! /usr/local/bin/bash

echo -e `date` '\n' > reports.txt
cat blocks.txt|cut -c 1-3|sort|uniq -c >> reports.txt
n=`wc -l blocks.txt`
echo "   ${n/.txt/}" >> reports.txt

for r in log todo fail debug analysis no_courses
do
    echo -e "\n$r" | tr a-z A-Z >> reports.txt
    cut -c 16- ${r}.txt|sort|uniq -c|sort -r >> reports.txt
done
