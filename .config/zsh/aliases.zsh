# Setting nvim
#alias vim=/usr/bin/nvim

# Setting yadm
alias yadm=~/.local/bin/yadm

alias yst='yadm status'
alias yau='yadm add -u'
alias yaa='yadm add --all'
alias yc='yadm commit -v'
alias yp='yadm push'
alias yl='yadm pull'
alias ydf='yadm difftool'
alias ydfs='yadm difftool --staged'
alias ysuri='yadm submodule update --recursive --init'
alias gdf='git difftool'
alias gdfs='git difftool --staged'
alias gcod='git checkout .'
alias gmd='git merge develop'

# Reload zsh config
alias reload!='RELOAD=1 source ~/.zshrc'

# Detect which `ls` flavor is in use
if ls --color > /dev/null 2>&1; then # GNU `ls`
    colorflag="--color"
else # OS X `ls`
    colorflag="-G"
fi

# Filesystem aliases
alias ..='cd ..'
alias ...='cd ../..'
alias ....="cd ../../.."
alias .....="cd ../../../.."

alias l="ls -lah ${colorflag}"
alias la="ls -AF ${colorflag}"
alias ll="ls -lFh ${colorflag}"
alias lld="ls -l | grep ^d"
alias rmf="rm -rf"

# Helpers
alias grep='grep --color=auto'
alias df='df -h' # disk free, in Gigabytes, not bytes
alias du='du -h -c' # calculate disk usage for a folder

# IP addresses
alias ipo="dig +short myip.opendns.com @resolver1.opendns.com"
alias localip="ipconfig getifaddr en1"
alias ips="ifconfig -a | perl -nle'/(\d+\.\d+\.\d+\.\d+)/ && print $1'"

# View HTTP traffic
alias sniff="sudo ngrep -d 'en1' -t '^(GET|POST) ' 'tcp and port 80'"
alias httpdump="sudo tcpdump -i en1 -n -s 0 -w - | grep -a -o -E \"Host\: .*|GET \/.*\""

# Trim new lines and copy to clipboard
alias trimcopy="tr -d '\n' | pbcopy"

# Recursively delete `.DS_Store` files
alias cleanup="find . -name '*.DS_Store' -type f -ls -delete"

# File size
alias fs="stat -f \"%z bytes\""

# Faster vim
alias v="vim -p"

# ROT13-encode text. Works for decoding, too! ;)
#alias rot13='tr a-zA-Z n-za-mN-ZA-M'

# Empty the Trash on all mounted volumes and the main HDD
#alias emptytrash="sudo rm -rfv /Volumes/*/.Trashes; rm -rfv ~/.Trash"

# Stuff I never really use but cannot delete either because of http://xkcd.com/530/
#alias stfu="osascript -e 'set volume output muted true'"
#alias pumpitup="osascript -e 'set volume 10'"

# Settings alias for task
alias t='task'
alias in='task add +in'
alias tin='task +in'
alias ts='task sync'
alias tsg='cd ~/.task;task sync;gp;popd'
alias tsu='task summary'
alias tsus='task summary | sort -r -k 4,4'
alias toldaily='task +PENDING +@daily -@dafyomi due.before:-1h desc.hasnt:Issue desc.hasnt:duolingo +YEAR'

tickle () {
    deadline=$1
    shift
    in +tickle wait:$deadline $@
}
alias tick=tickle

alias think='tickle +1d'

alias nex='task +next'
alias som='task +someday'
alias tcod='task context daily'
alias tcor='task context reg'
alias tcow='task context warframe'
# Nofar is supposed to be almost as no context but without farday tags
alias tcon='task context nofar'

# Circle ci configs
alias cicv='cd "$(git rev-parse --show-toplevel)"&&circleci config validate;popd'
#alias cicl='cd "$(git rev-parse --show-toplevel)"&&circleci config process .circleci/config.yml > process.yml&&circleci local execute -c process.yml;popd'
function cicl() {
    cd "$(git rev-parse --show-toplevel)"&&circleci config process .circleci/config.yml > process.yml&&circleci local execute -c process.yml --job $1;popd
}

unalias gd
preview="git diff $@ --color=always -- {-1}"
if command -v bat &> /dev/null; then
    preview="bat {-1} --diff --color=always"
fi

if command -v fzf &> /dev/null; then
    gd () {
        root=$(git rev-parse --show-toplevel)
        if [ -n "$root" ]; then
            pushd "$root"
            git diff $@ --name-only | fzf -m --ansi --preview $preview
            popd
        fi
    }
fi



function gcmd() {
    git checkout develop
    git pull
    git checkout $1
    git pull
    git merge develop
}


# Setting local aliases
source $HOME/.config/zsh/local_aliases.zsh
# source $HOME/.config/zsh/aliases.zsh.shadow


# Pocket cli add
alias pa=' pocket-cli add --url'
