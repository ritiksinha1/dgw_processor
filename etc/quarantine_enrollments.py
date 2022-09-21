#! /usr/local/bin/python3

from quarantine_manager import QuarantineManager
from enrollments import enrollments

qm = QuarantineManager()
for institution, requirement_id in qm.keys():
  enrollment, explanation = enrollments(institution, requirement_id)
  if enrollment:
    print(enrollment, f'{explanation} students')
  else:
    print(explanation)
