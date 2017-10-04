#!/bin/bash

if [ "$(id -u)" != "0" ]; then
    RUN_AS_ROOT='sudo'
else
    RUN_AS_ROOT=''
fi

echo "Install packages for building"
$RUN_AS_ROOT apt -y install git libtool libtool-bin autoconf automake cmake g++ pkg-config unzip

echo "Git clone nevim"
mkdir -p $HOME/neovim_build/
cd $HOME/neovim_build/
git clone https://github.com/neovim/neovim.git

echo "Building neovim, this should take a lot of time"
cd neovim
$RUN_AS_ROOT make clean
$RUN_AS_ROOT make CMAKE_BUILD_TYPE=RelWithDebInfo
$RUN_AS_ROOT make install


echo "Installing neovim"
$RUN_AS_ROOT cp $HOME/neovim_build/neovim/build/bin/nvim /usr/bin/
chmod +x $HOME/neovim_build/neovim/build/bin/nvim /usr/bin/
