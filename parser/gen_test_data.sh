#! /usr/local/bin/bash

value=CSCI-BA
if [[ $# -gt 0 ]]
then value=$1
fi

psql cuny_programs -Xqtc "select requirement_text \
from requirement_blocks
where institution = 'qns'
and block_value = '$value'
and period_stop = '99999999'" | sed s/\ *+$// |sed s/\\\\r//
