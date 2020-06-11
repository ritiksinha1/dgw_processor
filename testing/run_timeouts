#! /usr/local/bin/bash

# This is like run_tests, but it does just those blocks listed in the timeouts.log file
# Default timelimit is 10 minutes instead of 3
[[ ${TIMELIMIT} == '' ]] && export TIMELIMIT=900
[[ -d test_results.timeout ]] && rm -fr test_results.timeout
mkdir test_results.timeout
[[ -f run_timeouts.log ]] && rm -f run_timeouts.log
touch run_timeouts.log

csv_file=run_timeouts-`date -I`.csv
echo -e 'Type\tBlock\tLines\tMessages\tSeconds' > ${csv_file}

SECONDS=0
let $((total = 0))
ack timeout run_tests-2020-06-09.csv | while read -a line
do
  block_type=${line[0]}
  file=${line[1]}
  echo $block_type $file
  ./run.py $block_type ${file#*/} --timelimit ${TIMELIMIT} >> ${csv_file} 2>>./run_timeouts.log
    echo -en "               \r$count/$num_files\r"
  let $(( total += $SECONDS ))
  SECONDS=0
done

let $((mins = total/60))
let $((secs = total - (mins * 60) ))
printf "%02d:%02d total time" $mins $secs
