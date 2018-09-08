#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ${0} username address"
    exit 1
fi

if [ "$1" == "root" ]; then
    scp -r $HOME/.scripts/install/deployer $1@$2:/$1/deployer
    ssh $1@$2 /$1/deployer/yadm_start.sh
else
    scp -r $HOME/.scripts/install/deployer $1@$2:/home/$1/deployer
    ssh $1@$2 /home/$1/deployer/yadm_start.sh
fi

