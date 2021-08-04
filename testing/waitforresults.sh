#! /usr/local/bin/bash

if [[ $# == 1 ]]
then
  which=$1
else
  which=major
fi
printf "\033c"
ls -l ./test_results.$which
touch .lastwait
while true
do
  sleep 1
  find test_results.$which -cnewer .lastwait -exec  ls -l test_results.$which \;
  touch .lastwait
done
