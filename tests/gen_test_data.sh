#! /usr/local/bin/bash

# Extract requirement_text from the db.


# Defaults
institution=QNS
type=MAJOR
value=CSCI-BA

while [[ $# > 0 ]]
do
  case $1 in
    -i) institution=$2
        shift
        ;;
    -t) type=$2
        shift
        ;;
    -v) value=$2
        shift
        ;;
     *) echo "usage: gen_test_data.sh [-i institution] [-t type] [-v value]"
        exit 1
        ;;
  esac
  shift
done

# DEBUG:
# echo $institution
# echo $type
# echo $value
outfile=`echo "./test_data/${institution}_${type}_${value}.txt" | tr A-Z a-z`
echo Generating $outfile
psql cuny_curriculum -Xqtc "select requirement_text \
from requirement_blocks
where institution ~* '$institution'
and block_type ~* '$type'
and block_value ~* '$value'
and period_stop = '99999999'"  | sed s/\ *+$// |sed s/\\\\r// > $outfile
