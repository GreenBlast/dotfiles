#!/bin/bash
echo "Adding repos"
if [ "$(id -u)" != "0" ]; then
    RUN_AS_ROOT='sudo'
else
    RUN_AS_ROOT=''
fi

$RUN_AS_ROOT apt-get -y install software-properties-common
$RUN_AS_ROOT add-apt-repository -y ppa:neovim-ppa/stable

echo "Updating"
$RUN_AS_ROOT apt-get update

echo "Installing"
# Installing neovim
$RUN_AS_ROOT apt-get -y install zsh tmux python-dev python-pip python3-dev python3-pip silversearcher-ag neovim

echo "Pip installing"
pip2 install --user neovim
pip3 install --user neovim


echo "Install fzf"
source ~/.fzf/install  --key-bindings --completion --no-update-rc

echo "Install vim plug"
curl -fLo ~/.config/nvim/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# installing vim plugins
if command -v vim >/dev/null 2>&1; then
  echo "Bootstraping Vim"
  /usr/bin/vim '+PlugUpdate' '+PlugClean!' '+PlugUpdate' '+UpdateRemotePlugins' '+qall'
  /usr/bin/nvim '+PlugUpdate' '+PlugClean!' '+PlugUpdate' '+UpdateRemotePlugins' '+qall'
fi

echo "Adding colors to terminal"
source "./add_colors_to_terminal.sh"
