#!/bin/sh

/bin/sleep 10

. /home/pi/.profile

/usr/bin/tmux -f /home/pi/.tmux.empty.conf new-session -d ENTER location of script here

