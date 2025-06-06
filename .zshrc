# Debugging start time - comment this when not debugging
# zmodload zsh/zprof

## These two were suggested as options that could help in fixing performance issues
# ZSH_DISABLE_COMPFIX=true
# DISABLE_UNTRACKED_FILES_DIRTY="true"



# Sourcing specific config file
source $HOME/.config/zsh/config.zsh

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Adding ~/.local/bin to path
export PATH=$HOME/.local/bin:$PATH

# Adding custom npm path
export PATH=~/.npm-global/bin:$PATH

# Adding tmux smart session manager plugin
export PATH=$HOME/.tmux/plugins/t-smart-tmux-session-manager/bin:$PATH





# Path to your oh-my-zsh installation.
export ZSH=$HOME/.oh-my-zsh

# Setting custom plugins and themes location
export ZSH_CUSTOM=$HOME/zsh_custom

# Set name of the theme to load. Optionally, if you set this to "random"
# it'll load a random theme each time that oh-my-zsh is loaded.
# See https://github.com/robbyrussell/oh-my-zsh/wiki/Themes
#ZSH_THEME="robbyrussell"
ZSH_THEME="spaceship"
# Should be used for RaspiZW (Config needs to be automatic but I won't invest in that now)
# ZSH_THEME="ys"

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion. Case
# sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-syntax-highlighting zsh-autosuggestions)
# Should be used for RaspiZW (Config needs to be automatic but I won't invest in that now)
# plugins=(git)

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# ssh
# export SSH_KEY_PATH="~/.ssh/rsa_id"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# Nvim path should be set in config file
    if [ -f $NVIM_PATH ]; then
    alias vim=${NVIM_PATH}
    export GIT_EDITOR=${NVIM_PATH}
    # Exporting editor
    export VISUAL=${NVIM_PATH}
    export EDITOR="$VISUAL"
elif command -v vim > /dev/null 2>&1; then
    VIM_PATH="$(command -v vim)"
    alias vim=${VIM_PATH}
    export GIT_EDITOR=${VIM_PATH}
    # Exporting editor
    export VISUAL=${VIM_PATH}
    export EDITOR="$VISUAL"
fi

# Adding scripts dir
if [[ ! "$PATH" == *$HOME/.scripts* ]]; then
  export PATH="$PATH:$HOME/.scripts"
fi

# Setting colors for tmux
if [ 'find /lib/terminfo /usr/share/terminfo -name "*256*" | grep xterm-256color' ]; then
    export TERM='xterm-256color'
# else
#     export TERM='xterm-color'
fi

# display how long all tasks over 10 seconds take
export REPORTTIME=10

# Disable zsh double rm verification
setopt rm_star_silent

# This should be temporary, should just load all zsh in this dir after dealing with the prompt
source $HOME/.config/zsh/aliases.zsh

# Sourcing prompt options
source $HOME/.config/zsh/prompt.zsh

# Sourcing keybindings
source $HOME/.config/zsh/keybindings.zsh



# Fzf is a fuzzy searcher written in go
# export FZF_DEFAULT_COMMAND='ag -U --hidden --ignore .git -g ""'
export FZF_DEFAULT_COMMAND='ag --hidden --ignore .git -l -g ""'

# Setting binds to scroll preview
export FZF_DEFAULT_OPTS='--bind ctrl-f:preview-page-down,ctrl-b:preview-page-up'

# To apply the command to CTRL-T as well
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"

# Find also dot directories in ALT-C
export FZF_ALT_C_COMMAND='find -L . -mindepth 1  -path "*/\\.*" -fstype "sysfs" -o -fstype "devfs" -o -fstype "devtmpfs" \
    -o -fstype "proc" -prune -o -type d -print 2> /dev/null | cut -b3-'
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# Tmuxinator auto completion
# source $HOME/.bin/

# Integrate Marker
export MARKER_KEY_MARK="\C-b"

if [[ "$OSTYPE" == "darwin"* ]]; then
    export MARKER_KEY_GET="\C-@"
fi

export MARKER_KEY_NEXT_PLACEHOLDER="\C-s"
[[ -s "$HOME/.local/share/marker/marker.sh" ]] && source "$HOME/.local/share/marker/marker.sh"

# tabtab source for serverless package
# uninstall by removing these lines or running `tabtab uninstall serverless`
[[ -f /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/serverless.zsh ]] && . /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/serverless.zsh
# tabtab source for sls package
# uninstall by removing these lines or running `tabtab uninstall sls`
[[ -f /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/sls.zsh ]] && . /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/sls.zsh
# tabtab source for slss package
# uninstall by removing these lines or running `tabtab uninstall slss`
[[ -f /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/slss.zsh ]] && . /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/slss.zsh


export JIRA_DEFAULT_ACTION=dashboard


# export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

export GEM_HOME="$HOME/.gem"


export JIRA_URL="https://stepsme.atlassian.net/"
export PATH="/Users/user/git-fuzzy/bin:$PATH"

export NVM_DIR="$HOME/.nvm"
# [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
# Loads nvm only if needed
alias nvm="unalias nvm; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"; nvm $@"



if [[ "$OSTYPE" == "darwin"* ]]; then
    export PATH=$HOME/Library/Python/3.11/bin:$PATH
    export PATH="/usr/local/opt/mongodb-community@4.2/bin:$PATH"
fi

# Git fuzzy configuration
export PATH="$HOME/git-fuzzy/bin:$PATH"

export GF_SNAPSHOT_DIRECTORY='./git-fuzzy-snapshots'

#source /usr/local/opt/chruby/share/chruby/chruby.sh
if [[ "$OSTYPE" == "darwin"* ]]; then
    eval "$(rbenv init -)"
fi

eval "$(zoxide init zsh)"

# Currently not using starship
# eval "$(starship init zsh)"


#### Debugging start time - comment this when not debugging
# zprof
# zmodload -u zsh/zprof

#### Use `time zsh -i -c exit to measure start time


if (command -v atuin >/dev/null 2>&1); then
  . "$HOME/.atuin/bin/env"
  eval "$(atuin init zsh  --disable-up-arrow)"
fi
