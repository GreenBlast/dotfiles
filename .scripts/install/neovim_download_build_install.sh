#!/bin/bash

if [ "$(id -u)" != "0" ]; then
    RUN_AS_ROOT='sudo'
else
    RUN_AS_ROOT=''
fi

echo "Install packages for building"
RUN_AS_ROOT apt -y install git libtool libtool-bin autoconf automake cmake g++ pkg-config unzip

echo "Git clone nevim"


echo "Building neovim, this should take a lot of time"

echo "Installing neovim"

