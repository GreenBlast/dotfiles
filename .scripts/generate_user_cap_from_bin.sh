#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: ${0} binary_file output_file DLT_USER_HEADER_TYPE(147-162)"
    exit 1
fi
od -Ax -tx1 -v $1 | text2pcap -l $3 - $2
