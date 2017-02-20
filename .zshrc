export ZSH=$HOME/.config/zsh

# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000
setopt appendhistory autocd extendedglob
unsetopt beep
bindkey -v
# End of lines configured by zsh-newuser-install
# The following lines were added by compinstall
zstyle :compinstall filename '$HOME/.zshrc'

autoload -Uz compinit
compinit
# End of lines added by compinstall


# display how long all tasks over 10 seconds take
export REPORTTIME=10

# source all .zsh files inside of the zsh/ directory
for config ($ZSH/**/*.zsh) source $config

# TODO Check how and what to add completions
for config ($ZSH/**/*completion.zsh) source $config


# TODO Should change editor later
#export EDITOR='nvim'
export EDITOR='vim'

# Adding scripts dir
export PATH=$HOME/.scripts:$PATH

# Setting colors for tmux
[ -z "$TMUX" ] && export TERM=xterm-256color-italic

# TODO should add fzf later
#https://github.com/junegunn/fzf
#[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
#export FZF_DEFAULT_COMMAND='ag -g ""'

