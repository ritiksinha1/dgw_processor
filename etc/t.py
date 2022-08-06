#! /usr/local/bin/python3

import csv

cb = []
cv = []
with open('cb.out') as csv_file:
  reader = csv.reader(csv_file)
  for line in reader:
    cb.append(line)
with open('cv.out') as csv_file:
  reader = csv.reader(csv_file)
  for line in reader:
    cv.append(line)
for line in cv:
  if line not in cb:
    print('cv not cb', line)
for line in cb:
  if line not in cv:
    print('cb not in cv', line)
