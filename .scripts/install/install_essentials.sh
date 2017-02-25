#!/bin/bash
echo "Adding repos"
sudo add-apt-repository -y ppa:neovim-ppa/stable

echo "Updating"
#sudo apt-get update

echo "Installing"
# Installing neovim
sudo apt-get -y install zsh tmux neovim python-dev python-pip python3-dev python3-pip

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
  vim '+PlugUpdate' '+PlugClean!' '+PlugUpdate' '+qall'
fi
