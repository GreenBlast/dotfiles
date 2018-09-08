#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ${0} username address"
    exit 1
fi

#TODO need to delete deployer files
ssh $1@$2 '$HOME/.local/bin/yadm checkout clean'
ssh $1@$2 'rm -rf "$HOME/.yadm"'
