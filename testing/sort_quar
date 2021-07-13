#! /usr/local/bin/bash
# Put the quarantine list CSV file into institution/requirement_id order
(head -n 1 ../quarantine_list.csv && /usr/bin/tail -n +2 ../quarantine_list.csv | sort) > .sort_$$
mv .sort_$$ ../quarantine_list.csv
