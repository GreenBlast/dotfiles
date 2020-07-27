#!/bin/sh

cd $HOME
vcsh encrypt clone git@bitbucket.org:greenfighter/encrypt.git
vcsh encrypt config user.name "GreenBlast"
vcsh encrypt config user.email "greenfighter@gmail.com"
vcsh encrypt config --local status.showUntrackedFiles no

