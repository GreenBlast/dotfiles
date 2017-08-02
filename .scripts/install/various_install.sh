#!/bin/bash

if [ "$(id -u)" != "0" ]; then
    RUN_AS_ROOT='sudo'
else
    RUN_AS_ROOT=''
fi

# ncdu - Ncurses interface du
# htop - Improved top
# clang - C language framework
# iptraf - Monitor IP traffic
# exuberant-ctags - Ctags for C language
# ipython - Python shell
# xclip - Clipboard utility
# xsel - Clipboard utility


$RUN_AS_ROOT apt-get -y install htop vim ncdu clang iptraf exuberant-ctags ipython xclip xsel

# Add maybe later:
# bmon - bandwidth monitor
# slurm - network load monitor




