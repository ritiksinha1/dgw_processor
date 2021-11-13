#! /usr/local/bin/bash

# Given an error file, pick out the Timeout lines, and re-parse them with a longer timeout interval

timeout=1800
[[ $TIMEOUT_INTERVAL != '' ]] && timeout=$TIMEOUT_INTERVAL

while read institution requirement_id reason remainder
do
  if [[ ${reason} == Timeout ]]
  then
    institution=`echo $institution| cut -c 1-3 | tr A-A a-z`
    requirement_id=`echo $requirement_id |cut -c 3-8`
    echo "dgw_parser.py -i ${institution} -ra ${requirement_id} -ti ${timeout} >>$0.out 2>>$0.err"
  fi
done
