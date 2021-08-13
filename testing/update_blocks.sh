#! /usr/local/bin/bash

# This script automates the verification process when updating the requirement_blocks table after a
# new dataset is downloaded from Tumbleweed. The verification process consists of determining
# whether any previously-quarantined blocks have been fixed and whether any new blocks fail to
# parse cleanly. Generate a list of any newly-failing blocks for manual intervention (determine why
# the block failed and quarantine it, with an explanation.)

# Developer’s Guide
#   I use the following variables, aliases, and functions, which are defined in a startup script
#   that runs whenever I start a command-line session.
#
#     Get into the testing directory
#       export PROJS_DIR=/Users/vickery/Projects
#       export testing="$PROJS_DIR/dgw_processor/testing"
#       alias testing='cd "$testing"; use major'
#
#     View the test_data and test_results folders
#       alias lt='echo $TEST_DIR; ls -l $TEST_DIR'
#       alias lr='echo $RESULT_DIR; ls -lS $RESULT_DIR|m'
#
#     Copy the name of a test_data.{block_type} file to the system clipboard, and use the following
#     commands to set the TEST_DATA environment variable, and to copy it to/from the temporary file
#     named t.
#       function tot
#       {
#         export target_filename=`pbpaste`
#         if [[ -f $TEST_DIR/$target_filename ]]
#         then
#           export saved_t=$TEST_DIR/$target_filename
#           cp $saved_t ./t
#           export TEST_DATA=./t
#           alias fromt='export TEST_DATA=$saved_t'
#           alias vr='m $RESULT_DIR/$target_filename'
#           alias rmt='rm -i $RESULT_DIR/$target_filename'
#           echo $saved_t
#         else
#           echo File does not exist: $TEST_DIR/$target_filename
#         fi
#       }
#
#     Edit the block residing in the file ./t to locate the problem. (subl is an alias for the
#     programming editor that I use. I delete parts of the Scribe block until I locate what line(s)
#     caused the problem.)
#       alias sublt='subl t'
#
#     Shortened names for shell scripts
#       alias update_blocks=update_blocks.sh
#       alias run_tests=run_tests.sh
#       alias run_timeouts=run_timeouts.sh
#       alias quarantine=quarantine.sh
#
#     Determine which block_type to work with
#       function use {
#         if [[ -d test_data.$1 ]]
#         then
#           export TEST_DIR=test_data.$1
#           export RESULT_DIR=test_results.$1
#           echo "Using $1"
#         else
#           echo "test_data.$1 does not exist"
#         fi
#
#     The default block_type
#       use major

# The report_progress function sends email to the operations director to let them know what’s
# happening. Pass the subject as an argument string; ./.mesg_$$ will be the message body.
OPERATIONS_DIRECTOR='Christopher.Vickery@qc.cuny.edu'

function report_progress
{
  # sendemail must be in the PATH as a (hard) link to sendemail.py in transfer-app.
  /Users/vickery/bin/sendemail -s "Update Blocks: $1" -t .mesg_$$ "$OPERATIONS_DIRECTOR"
  rm -f .mesg_*
}

# =================================================================================================

rm -f .mesg_*
SECONDS=0
date > .mesg_$$
report_progress "Starting on $HOSTNAME"

# Generate Test Data
#    This step makes copies of all the requirement_blocks as files, distributing them into test_data
#    folders with suffixes according to their block types. The ../quarantine_list.csv file is used
#    to partition previously-quarantined blocks into the test_data.quarantine folder.
echo -e "\n*** GENERATE TEST DATA ***"
./generate_test_data.py >> .mesg_$$ 2>&1
[[ $? != 0 ]] && report_progress "Exiting: generate_test_data.py failed." \
              && rm -f .mesg_$$ \
              && exit 1

# Check Quarantined Blocks
#    Here, we try to parse the previously-quarantined blocks. Any blocks that now parse correctly
#    are removed from ../quarantine_list.csv and the files are moved from test_data.quarantine into
#    the appropriate test_data.{block_type} folder.
echo -e "\n*** CHECK QUARANTINED BLOCKS ***"
./check_quarantined_blocks.py >> .mesg_$$ 2>&1
[[ $? != 0 ]] && report_progress "Exiting: check_quarantined_blocks.py failed." \
              && rm -f .mesg_$$ \
              && exit 1

# Run Tests
#    Parse all blocks in the test_data.{block_type} folders. Any new parsing errors will be found in
#    test_results.{block_type}.
echo -e "\n*** RUN TESTS ***"
./run_tests.sh 2>> .mesg_$$
[[ $? != 0 ]] && report_progress "Exiting: run_tests.sh failed." \
              && rm -f .mesg_$$ \
              && exit 1

# Investigate Timeouts
#    Timeouts are blocks that take a long time to parse. The problem could be either that the block
#    is really complex or that there is an error in the grammar. During the Run Tests stage, blocks
#    that fail to parse within a certain time limit (3 minutes by default) were identified, and this
#    step tries just those blocks again with a longer time limit (10 minutes by default).
echo -e "\n*** RUN TIMEOUTS ***"
./run_timeouts.sh >> .mesg_$$ 2>&1
[[ $? != 0 ]] && report_progress "Exiting: run_timeouts.sh failed." \
              && rm -f .mesg_$$ \
              && exit 1

# All Done
#    Report all parsing and timeout errors for manual review. The quarantine.sh script can be run to
#    add blocks to ../quarantine_list.csv along with an explanation of why the block failed.
echo -e "\n*** CHECK RESULTS ***"
need_to_check=False
for block_type in major minor conc degree other
do
  total=`ls -l test_results.${block_type} | ack '_' | wc -l`
  if [[ $total != 0 ]]
  then
    if [[ $total == 1 ]]
    then
      echo "One $block_type error" >> .mesg_$$
    else
      echo "$total $block_type errors" >> .mesg_$$
    fi
    need_to_check=True
    for file in test_results.${block_type}/*
    do
      echo "${file##*/} failed to parse" >> .mesg_$$
    done
  else echo "No $block_type errors" >> .mesg_$$
  fi
done

msg="completed after $SECONDS sec."
[[ need_to_check ]] && msg="$msg Manual intervention required!"
report_progress "$msg"

exit 0
