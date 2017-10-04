#!/bin/sh

if [ -x "$(command -v compton)" ]; then
    compton -f
fi
