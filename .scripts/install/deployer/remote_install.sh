#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ${0} remote_machine(ssh format)"
    exit 1
fi

scp -r $HOME/.scripts/install/deployer $1:~/
ssh $1 ~/deployer/yadm_start.sh
