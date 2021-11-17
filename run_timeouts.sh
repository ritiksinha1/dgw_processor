#! /usr/local/bin/bash

# Given an error file, pick out the Timeout lines, and re-parse them with a longer timeout interval

if [[ $# != 1 ]]
then  echo Usage: run_timeouts.sh [file]
      exit 1
fi

num_todo=`ack Timeout $1 |wc -l`
echo "$num_todo Timeouts"
let $(( num_done = 0 ))

timeout=1800
[[ $TIMEOUT_INTERVAL != '' ]] && timeout=$TIMEOUT_INTERVAL

echo "Timeout Interval is $timeout seconds"

SECONDS=0
while read institution requirement_id reason remainder
do
  if [[ ${reason} == Timeout ]]
  then
    let $(( num_done += 1 ))
    echo -n "$num_done / $num_todo "
    institution=`echo $institution| cut -c 1-3 | tr A-Z a-z`
    requirement_id=`echo $requirement_id |cut -c 3-8`
    dgw_parser.py -i ${institution} -ra ${requirement_id} -ti ${timeout}
  fi
done < $1

echo "That took $SECONDS seconds"
