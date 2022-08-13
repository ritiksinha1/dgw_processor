#! /usr/local/bin/bash

echo -e `date` '\n' > reports.txt
cat blocks.txt|cut -c 1-3,15-|sort|uniq -c >> reports.txt
n=`wc -l blocks.txt`
echo "   ${n/.txt/}" >> reports.txt

for r in log todo fail no_courses debug analysis
do
    echo -e "\n$r" | tr a-z A-Z >> reports.txt
    if [[ $r = no_courses ]]
    then
        cat ${r}.txt|sort|uniq -c|sort -r >> reports.txt
    else
        cut -c 16- ${r}.txt|sort|uniq -c|sort -r >> reports.txt
    fi
done
