#!/bin/sh

unset TMUX
tmux \
    new-session 'cowsay moo' \; \
    split-window "bash --rcfile <(echo '. ~/.bashrc; tmux set status off; tmux link-window -s ${1}:${2} -t 1 -k')"
    #new-session \; \
    #new-session 'tmux set status off' \; \
#tmux new 'tmux set status off \; \
    #link-window -s $1:$2 -t 1 -k

