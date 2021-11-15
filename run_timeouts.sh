#! /usr/local/bin/bash

# Given an error file, pick out the Timeout lines, and re-parse them with a longer timeout interval

if [[ $# != 1 ]]
then  echo Usage: run_timeouts.sh [file]
      exit 1
fi

if [[ !($1 =~ err$) ]]
then read -p "Are you sure $1 is an err file [yN]? "
     [[ !($REPLY =~ [Yy]) ]] && exit
fi

timeout=1800
[[ $TIMEOUT_INTERVAL != '' ]] && timeout=$TIMEOUT_INTERVAL

echo "Timeout Interval is $timeout seconds"

read -p 'Truncate out and err [Yn]? '
if [[ $REPLY =~ [Nn] ]]
then echo Not truncated
else truncate -s 0 run_timeouts.out run_timeouts.err
fi

SECONDS=0
while read institution requirement_id reason remainder < $1
do
  if [[ ${reason} == Timeout ]]
  then
    institution=`echo $institution| cut -c 1-3 | tr A-Z a-z`
    requirement_id=`echo $requirement_id |cut -c 3-8`
    dgw_parser.py -i ${institution} -ra ${requirement_id} -ti ${timeout} >>run_timeouts.out 2>>run_timeouts.err
  fi
done

echo "That took $SECONDS seconds"
