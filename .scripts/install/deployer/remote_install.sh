#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ${0} username address"
    exit 1
fi

scp -r $HOME/.scripts/install/deployer $1@$2:/home/$1/
ssh $1@$2 /home/$1/deployer/yadm_start.sh
