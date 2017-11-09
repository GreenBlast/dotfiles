#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ${0} process_string poll_time_in_seconds"
    exit 1
fi

LIST_PROCESSES="$(pgrep $1)"
if [ -n "$LIST_PROCESSES" ]
then
    echo "Watching processes:"
    echo "${LIST_PROCESSES}"
else
    echo "No processes that contains this string"
    exit 1
fi

for procs in $LIST_PROCESSES; do
    echo "USER , PID,COMMAND ,%CPU, VSZ" > "${1}_${procs}.csv"
done

echo "Press [CTRL+C] to stop..."
while [ -n "$LIST_PROCESSES" ]
do
    for procs in $LIST_PROCESSES; do
        DATA=$(ps -p $procs --no-headers -o %U,%p,%c,%C,%z)
        echo $DATA >> "${1}_${procs}.csv"
    done
    sleep $2
done
