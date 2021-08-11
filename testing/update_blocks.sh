#! /usr/local/bin/bash

# This script automates the verification process when updating the requirement_blocks table after a
# new dataset is downloaded from Tumbleweed. The verification process consists of determining
# whether any previously-quarantined blocks have been fixed and whether any new blocks fail to
# parse cleanly.

# The report_progress function sends email to the operations director to let them know what's
# happening.
OPERATIONS_DIRECTOR='Christopher.Vickery@qc.cuny.edu'

function report_progress
{
  echo $1 > .mesg_$$
  # sendemail must be in the PATH as a (hard) link to sendemail.py in transfer-app.
  /Users/vickery/bin/sendemail -s "Update Blocks: $1" -t .mesg_$$ "$OPERATIONS_DIRECTOR"
  rm -f .mesg_*
}

# Generate Test Data
#    This step makes copies of all the requirement_blocks as files, distributing them into test_data
#    folders with suffixes according to their block types. The ../quarantine_list.csv file is used
#    to partition previously-quarantined blocks into the test_data.quarantine folder.
report_progress "`date` Start update_blocks.sh on $HOSTNAME"
rm -f .err_*
./generate_test_data.py 2> .err_$$
[[ $? != 0 ]] && report_progress "Exiting: generate_test_data.py failed: `cat .err_$$`" \
              && rm -f .err_$$ \
              && exit 1

# Check Quarantined Blocks
#    Here, we try to parse the previously-quarantined blocks. Any blocks that now parse correctly
#    are removed from ../quarantine_list.csv and the files are moved from test_data.quarantine into
#    the appropriate test_data.{block_type} folder.
./check_quarantined_blocks.py 2> .err_$$
[[ $? != 0 ]] && report_progress "Exiting: check_quarantined_blocks.py failed: `cat .err_$$`" \
              && rm -f .err_$$ \
              && exit 1

# Run Tests
#    Parse all blocks in the test_data.{block_type} folders. Any new parsing errors will be found in
#    test_results.{block_type}.
./run_tests.sh 2> .err_$$
[[ $? != 0 ]] && report_progress "Exiting: run_tests.sh failed: `cat .err_$$`" \
              && rm -f .err_$$ \
              && exit 1

# Investigate Timeouts
#    Timeouts are blocks that take a long time to parse. The problem could be either that the block
#    is really complex or that there is an error in the grammar. During the Run Tests stage, blocks
#    that fail to parse within a certain time limit (3 minutes by default) were identified, and this
#    step tries just those blocks again with a longer time limit (10 minutes by default).
./run_timeouts.sh 2> .err_$$
[[ $? != 0 ]] && report_progress "Exiting: run_timeouts.sh failed: `cat .err_$$`" \
              && rm -f .err_$$ \
              && exit 1


# All Done
#    Report all parsing and timeout errors for manual review. The quarantine.sh script can be run to
#    add blocks to ../quarantine_list.csv along with an explanation of why the block failed.
need_to_check=False
for block_type in major minor conc degree other
do
  total=`ls -l test_results.$block_type|ack total|cut 7-`
  if [[ $total != 0 ]]
  then
    for file in test_results.block_type
    do
      echo "ERROR: $file failed to parse" >> .err_$$
      need_to_check=True
    done
  fi
done

# Developer’s Guide
#   I use the following variables, aliases, and function, defined in my ~/.aliases_du_jour, to
#   facilitate manual review of anomalies:
#     Get into the testing directory
#       export testing="$PROJS_DIR/dgw_processor/testing"
#       alias testing='cd "$testing"'
#     Copy the name of a test_data.{block_type} file to the system clipboard, and use the following
#     commands to set the TEST_DATA environment variable, and to copy it to/from the temporary file
#     named t.
#       alias setit='export TEST_DATA=$TEST_DIR/`pbpaste`*'
#       alias tot='export saved_t=$TEST_DATA; cp $TEST_DATA ./t; export TEST_DATA=./t'
#       alias fromt='export TEST_DATA=$saved_t'
#     Edit the offending block to locate the problem. (subl is an alias for the programming editor
#     that I use.)
#       alias sublt='subl t'
#     View the test_data and test_results folders
#       alias lt='echo $TEST_DIR; ls -l $TEST_DIR'
#       alias lr='echo $RESULT_DIR; ls -lS $RESULT_DIR|m'
#       alias vr='m $RESULT_DIR/`pbpaste`'
#     Shortened names for shell scripts
#       alias update_blocks=update_blocks.sh
#       alias run_tests=run_tests.sh
#       alias run_timeouts=run_timeouts.sh
#       alias quarantine=quarantine.sh
#     Determine which block_type to work with
#       function use {
#         export TEST_DIR=test_data.$1
#         export RESULT_DIR=test_results.$1
#       }
#     The default block_type after running ~/.aliases_du_jour
#       use major


msg="Requirement block checks complete."
[[ need_to_check ]] && msg="$msg Manual intervention required."
report_progress $msg
exit 0
