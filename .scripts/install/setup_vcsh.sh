#!/bin/sh

cd $HOME
vcsh clone git@bitbucket.org:greenfighter/encrypt.git encrypt
vcsh encrypt config user.name "GreenBlast"
vcsh encrypt config user.email "greenfighter@gmail.com"
vcsh encrypt config --local status.showUntrackedFiles no

