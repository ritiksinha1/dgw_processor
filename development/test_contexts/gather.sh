#! /usr/local/bin/bash

numlines=`cat $1 | wc -l`
let $(( count = 1 ))
truncate -s 0 if_expressions
while read -ra line
do echo -e "$count/$numlines\t${line[0]} ${line[1]} ${line[2]}" 1>&2
../dgw_parser.py -i ${line[0]} -t ${line[1]} -v ${line[2]} >> if_expressions
  let $(( count = count + 1 ))
done < $1
