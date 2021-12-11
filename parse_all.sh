#! /usr/local/bin/bash

# Parse all current blocks for all institutions

# All institutions
institutions=(bar bcc bkl bmc csi cty grd hos htr jjc kcc lag law leh mec med ncc nyt qcc qns slu \
              soj sph sps yrk)

# Option to skip institutions by listing them on the command line
export truncate=True
while [[ $# > 0 ]]
do
  inst=`echo ${1} | cut -c 1-3 | tr A-Z a-z`
  if [[ ${#inst} != 3 ]]
  then echo "invalid institution: $1"
  else echo "Will skip $inst"
       institutions=( "${institutions[@]/$inst}" )
       # Keep previous out and error files
       unset truncate
  fi
  shift
done

# Option to use an environment variable to specify a timeout interval different from the default of
# 120 sec.
if [[ $TIMEOUT_INTERVAL ]]
then timeout_arg="-ti $TIMEOUT_INTERVAL"
     echo "Timeout interval is $TIMEOUT_INTERVAL seconds"
else timeout_arg='-ti 120'
     echo "Timeout interval is default value (120 sec)"
fi

# Truncate pre-existing out and err files if this is a "full run"
if [[ $truncate ]]
then
     truncate -s 0 parse_all.out
     truncate -s 0 parse_all.err
fi

SECONDS=0
# Process each institution separately
for institution in ${institutions[@]}
do
  start=$SECONDS
  dgw_parser.py -i $institution -t all -v all $timeout_arg >>parse_all.out 2>>parse_all.err
  end=$SECONDS
  let $(( interval = end - start ))
  let $(( hours = interval / 3600  ))
  let $(( minutes = (interval - (hours * 3600)) / 60 ))
  let $(( seconds = interval - ( (hours * 3600) + (minutes * 60) ) ))
  printf "%s completed in %02d:%02d:%02d\n" `echo $institution|tr a-z A-Z` $hours $minutes $seconds
done

# Timing summary
interval=$SECONDS
let $(( hours = interval / 3600  ))
let $(( minutes = (interval - (hours * 3600)) / 60 ))
let $(( seconds = interval - ( (hours * 3600) + (minutes * 60) ) ))
printf "All institutions completed in %02d:%02d:%02d\n" $hours $minutes $seconds
