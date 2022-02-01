#! /usr/local/bin/bash

# Given an error file, pick out the Timeout lines, and re-parse them with a longer timeout interval

if [[ $# != 1 ]]
then  echo "Usage: $0 [file]"
      exit 1
fi

_this=$0
log_file=${_this/.sh/}.log
err_file=${_this/.sh/}.err

num_todo=`ack Timeout $1 |wc -l`
suffix='s'
[[ $num_todo = 1 ]] && suffix=''
echo "$num_todo Timeout${suffix} requirement block to parse."
let $(( num_done = 0 ))

timeout=1800
[[ $TIMEOUT_INTERVAL != '' ]] && timeout=$TIMEOUT_INTERVAL

# Initialize log_file and err_file
echo "Timeout Interval is $timeout seconds" >$log_file 2>$err_file

SECONDS=0
max_time=0
while read institution requirement_id remainder
do
  if [[ ${remainder} =~ Timeout ]]
  then
    start=$SECONDS
    let $(( num_done += 1 ))
    institution=`echo $institution| cut -c 1-3 | tr A-Z a-z`
    requirement_id=`echo $requirement_id |cut -c 3-8`
    echo -ne "\r$num_done / $num_todo $institution $requirement_id "
    dgw_parser.py -i ${institution} -ra ${requirement_id} -ti ${timeout} >> $log_file 2>$err_file
    elapsed=$(( $SECONDS - $start ))
    [[ $(( $elapsed > $max_time )) ]] && max_time=$elapsed
    echo -n "$elapsed sec."
  fi
done < $1

echo -e "\nThat took $SECONDS seconds; max was $max_time sec."  >> $log_file
