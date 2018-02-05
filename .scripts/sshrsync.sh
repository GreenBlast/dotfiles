#!/bin/bash

rsync -aHAXxvP --numeric-ids --delete -e "ssh -T -o Compression=no -x" $1 $2
