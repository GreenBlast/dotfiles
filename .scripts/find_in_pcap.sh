#!/bin/bash

comm=$@

IFS=$'\n';

for i in $(find . -type f -name "*cap*"); do
    temp=$(tshark -r $i -Y   $comm 2>/dev/null)
    if [ -n "$temp" ]; then
        echo "found result in file $i"
    fi
done

