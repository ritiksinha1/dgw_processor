#! /usr/local/bin/bash
psql cuny_programs -Xqtc "select requirement_text \
from requirement_blocks
where institution = 'qns'
and block_value = 'CSCI-BA'
and period_stop = '99999999'" | sed s/\ *+$// > qns.txt
