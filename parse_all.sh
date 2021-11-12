#! /usr/local/bin/bash

# Parse all blocks for all institutions with option to ignore institutions
institutions=(bar bcc bkl bmc csi cty grd hos htr jjc kcc lag law leh mec med ncc nyt qcc qns slu \
              soj sph sps yrk)

while [[ $# > 0 ]]
do
  inst=`echo ${1} | cut -c 1-3 | tr A-Z a-z`
  if [[ ${#inst} != 3 ]]
  then echo "invalid institution: $1"
  else institutions=( "${institutions[@]/$inst}" )
  fi
  shift
done

for institution in ${institutions[@]}
do
  dgw_parser.py -i $institution -t all -v all >>parse_all.out 2>>parse_all.err
done
