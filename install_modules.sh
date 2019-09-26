#! /bin/bash

FILE=./obli.txt
if [ -f "$FILE" ]; then
    input=$FILE
    while IFS= read -r line
    do
        ccheck=${line:0:1}
        if [[ $ccheck != '#' ]] && [[ ! -z "${ccheck// }" ]] 
        then
            cd modules
            git clone $line 
            cd ..
        fi
    done < "$input"
else 
    echo "ERROR: This script must be run in a valid obli dispatcher directory"
fi
