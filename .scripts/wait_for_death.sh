#!/bin/sh

if [ $(kill -0 $1) ]; then
    echo "Process $1 doesn't exist."
    exit 1
fi

while kill -0 $1; do
    sleep 1
done

echo "Process $1 finished at $(date +"%F %T")."

