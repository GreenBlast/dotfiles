#!/bin/sh

if [ "$#" -ne 2 ]; then
    echo "Usage: ${0} session_name window_name"
    exit 1
fi

unset TMUX
tmux \
    new-session 'cowsay moo' \; \
    split-window "bash --rcfile <(echo '. ~/.bashrc; tmux set status off; tmux link-window -s ${1}:${2} -t 1 -k')"
