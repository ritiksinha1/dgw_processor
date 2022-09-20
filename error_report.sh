#! /usr/local/bin/bash
# Show enrollments for programs and requirement blocks where errors occurred

# missing.txt: no requirement block for an academic plan listed as current in acad_plan_tbl
echo -e "NO DAP_REQ_BLOCK\n----------------"
while read institution program type title
do
  echo -e "  $institution $program:\t`enrollments.py $institution $program`"
done < $dgws/missing.txt

echo -e "\nMAPPING FAIL BLOCKS\n-------------------"
while read institution requirement_id rest
do
  echo -e "  $institution $requirement_id: `enrollments.py $institution $requirement_id`\t$rest"
done < $dgws/fail.txt
