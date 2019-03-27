#!/bin/bash

if [ "$(id -u)" != "0" ]; then
    RUN_AS_ROOT='sudo'
else
    RUN_AS_ROOT=''
fi

# ncdu - Ncurses interface du
# htop - Improved top
# vim - Legendary text editor
# tig - Cool git interface
# clang - C language framework
# iptraf - Monitor IP traffic
# exuberant-ctags - Ctags for C language
# ipython - Python shell
# xclip - Clipboard utility
# xsel - Clipboard utility
# ranger - Files manager and browser
# arandr - xrandr GUI utility, handle graphical screen configuration
# lxappearance - GUI gtk theme edit utility
# scrot - Command line screen capture utility
# taskwarrior - Task management
# libxml2-utils - xmllint
# HTTPie - a CLI, cURL-like tool for humans. <http://httpie.org>
# jq - commandline JSON processor

$RUN_AS_ROOT apt-get -y install htop vim tig ncdu clang iptraf exuberant-ctags ipython xclip xsel ranger arandr lxappearance scrot taskwarrior libxml2-utils httpie jq

# Add maybe later:
# bmon - bandwidth monitor
# slurm - network load monitor

source ~/.scripts/install/install_cht.sh


