#! /usr/local/bin/bash

# Summarize the .txt files generated by course_mapper

# Command line options: -i to skip (ignored) lines
unset ignore
while [[ $# > 0 ]]
do
  case $1 in

      -i) ignore=ignore
          ;;

       *) echo "Usage: $0 [-i]"
          echo "   -i:  Skip “(ignored)” lines"
          exit 1
          ;;
  esac
  shift
done

echo -e `date` '\n\nBLOCK COUNTS' > reports.txt

cat blocks.txt|cut -c 1-3,15-|sort|uniq -c >> reports.txt
n=`wc -l blocks.txt`
echo "   ${n/blocks.txt/}Total" >> reports.txt

echo -e "\nMAJORS WITH NON-MAJOR BLOCK TYPES" >> reports.txt
cat anomalies.txt >> reports.txt

echo -e "\nMAJORS WITH NO SCRIBE BLOCKS" >> reports.txt
cat missing_ra.txt >> reports.txt

for r in log todo fail no_courses debug analysis
do
  echo -e "\n$r" | tr a-z A-Z >> reports.txt
  if [[ $r = no_courses ]]
  then
      cat ${r}.txt|sort|uniq -c|sort -r >> reports.txt
  else
    if [[ $ignore ]]
    then
      cut -c 16- ${r}.txt|ack -v '(ignored)'|sort|uniq -c|sort -r >> reports.txt
    else
      cut -c 16- ${r}.txt|${ignore}sort|uniq -c|sort -r >> reports.txt
    fi
  fi
done
