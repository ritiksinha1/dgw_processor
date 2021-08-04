#! /usr/local/bin/bash

# Be sure ReqBlock.g4 here matches the real one, one directory up.
cp ../ReqBlock.g4 .

# Clean out the test_results directories
# Parse all requirement blocks in the test_data directories.
# Capture error messages in the test_results directories.
#  Empty result files indicate complete parsing with no errors.

# Default timelimit is 3 minutes
[[ ${TIMELIMIT} == '' ]] && export TIMELIMIT=180

# csv_file=run_tests-`date -I`.csv
dirs=()
while [[ $# > 0 ]]
do
  dirs+=($1)
  shift
done
if [[ ${#dirs[@]} == 0 ]]
then
  dirs=(major minor degree conc other)
fi

SECONDS=0

# if [[ ${#dirs[@]} == 5 ]]
# then
#       echo -e 'Type\tBlock\tLines\tMessages\tSeconds' > ${csv_file}
# fi

rm -f ./timeouts.log
touch ./timeouts.log

let $((total = 0))
for dir in ${dirs[@]}
do
  block_type=${dir##*.}
  # if [[ ${#dirs[@]} != 5 ]]
  # then csv_file=./run_tests.out/`date -I`_${dir}.csv
  #      echo -e 'Type\tBlock\tLines\tMessages\tSeconds' > ${csv_file}
  # fi
  csv_file=./run_tests.out/`date -I`_${dir}.csv
  echo -e 'Type\tBlock\tLines\tMessages\tSeconds' > ${csv_file}

  block_str=`echo $block_type|tr a-z A-Z`
  rm -fr test_results.$block_type
  mkdir test_results.$block_type
  num_files=`ls test_data.$block_type|wc -l`
  echo -e "\nThere are $num_files $block_str files"
  let count=0
  for file in test_data.$block_type/*
  do
    [[ $DEBUG ]] && echo  -e "$count/$num_files\t$file"
    let $((count = count + 1))
    ./run.py $block_type ${file#*/} --timelimit ${TIMELIMIT} >> ${csv_file} 2>>./timeouts.log
    echo -en "               \r$count/$num_files\r"
  done
  num_errors=`ls test_results.$block_type|wc -l`
  echo -e "\n$block_str completed after $SECONDS seconds with $num_errors errors."
  let $(( total += $SECONDS ))
  SECONDS=0
done
./count_results.py
let $((mins = total/60))
let $((secs = total - (mins * 60) ))
printf "%02d:%02d total time" $mins $secs
