#! /usr/local/bin/bash

# This is like run_tests, but it does just those blocks listed in the timeouts.log file
# Default timelimit is 10 minutes instead of 3. The idea is to see whether a block that takes too
# long to parse is triggering an "endless" loop or is just slow.

[[ ${TIMELIMIT} == '' ]] && export TIMELIMIT=900
[[ -d test_results.timeout ]] && rm -fr test_results.timeout
mkdir test_results.timeout

[[ -f run_timeouts.log ]] && rm -f run_timeouts.log
touch run_timeouts.log

mkdir -p run_timeouts.out

csv_file=run_timeouts.out/run_timeouts_`date -I`.csv
echo -e 'Type\tBlock\tLines\tMessages\tSeconds' > ${csv_file}

SECONDS=0
let $((total = 0))

# Get the most recent set of run_test outputs
all_files=(`ls -t run_tests.out`)
run_date=`echo $all_files[0] | cut -c 1-10`

for file in ${all_files[*]}
do
  if [[ $file =~ $run_date ]]
  then
    echo $file
    if [[ `ack timeout run_tests.out/$file | wc -l` == 0 ]]
    then echo '  No timeouts'
    else
      ack timeout run_tests.out/$file | while read -a line
      do
        block_type=${line[0]}
        test_data_file=${line[1]}
        echo $block_type $test_data_file
        ./run.py $block_type ${test_data_file#*/} --timelimit ${TIMELIMIT} >> ${csv_file} 2>>./run_timeouts.log
        echo -en "               \r$count/$num_files\r"
        let $(( total += $SECONDS ))
        SECONDS=0
      done
    fi
  fi
done

let $((mins = total/60))
let $((secs = total - (mins * 60) ))
printf "%02d:%02d total time" $mins $secs
