#!/bin/bash
wget https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/Hack/Regular/complete/Hack%20Regular%20Nerd%20Font%20Complete%20Mono.ttf
mkdir -p $HOME/.local/share/fonts/
mv "Hack Regular Nerd Font Complete Mono.ttf" $HOME/.local/share/fonts/
fc-cache -s; mkfontscale $HOME/.local/share/fonts; mkfontdir $HOME/.local/share/fonts
#fc-cache -vf  $HOME/.local/share/fonts

