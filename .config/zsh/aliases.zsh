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
# alias ydf='yadm difftool'
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


if command -v exa &> /dev/null; then
    alias l="exa -lah"
    alias ll="exa -lFh"
    alias lld="exa -l | grep ^d"
else
    alias l="ls -lah ${colorflag}"
    alias la="ls -AF ${colorflag}"
    alias ll="ls -lFh ${colorflag}"
    alias lld="ls -l | grep ^d"
fi

if command -v eza &> /dev/null; then
    alias l="eza -lah"
    alias ll="eza -lFh"
    alias lld="eza -l | grep ^d"
else
    alias l="ls -lah ${colorflag}"
    alias la="ls -AF ${colorflag}"
    alias ll="ls -lFh ${colorflag}"
    alias lld="ls -l | grep ^d"
fi

if command -v bat &> /dev/null; then
    alias cat="bat"
fi


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

function  pat() {
    pocket-cli add --tags="train reading" --url "$1"
    . ~/.scripts/verify_hoarder_cli.sh 
    verify_hoarder_cli_key_and_address
    hoarder --api-key "${HOARDER_KEY}" --server-addr "${HOARDER_ADDRESS}" bookmarks add --link "$1" --tag-name "train reading"
}

function  pav() {
    pocket-cli add --tags="videos" --url "$1"
    . ~/.scripts/verify_hoarder_cli.sh 
    verify_hoarder_cli_key_and_address
    hoarder --api-key "${HOARDER_KEY}" --server-addr "${HOARDER_ADDRESS}" bookmarks add --link "$1" --tag-name "videos"
}

function apat() {
  # Split the input string on newlines and spaces
  urls=("${(f)@}")

  # Loop through each URL and execute curl
  for url in "${urls[@]}"; do
      pocket-cli add --tags="train reading" --url "$url"
  done

}


# Navigate to branches using FZF "!checkout_fzf()
function cof() { git branch | fzf | xargs git checkout; }
# Add files using FZF "!add_fzf()
function af() { git status -s | awk '{print $2}' | fzf -m | xargs git add; }
# Add files using FZF and immediately commit them "!add_fzf_amend()
function afmend() { git status -s | awk '{print $2}' | fzf -m | xargs git add && git commit --amend; }
# Restore files (like removing multiple files from the staging area)  "!restore_fzf()
function ref()  { git status -s | awk '{print $2}' | fzf -m | xargs git restore --staged; }
# Delete untracked files using FZF "!delete_untracked()
function rmfu() { git ls-files --exclude-standard --other | fzf -m | xargs rm; }


alias yd=yt-dlp
alias ydf="yt-dlp -f 22"
alias ydfa="yt-dlp -f 'bestvideo[height<=720]+bestaudio[ext=m4a]/best[height<=720]' --merge-output-format mp4"
alias rss="~/.scripts/get_youtube_rss.py "

# Nerd fonts
installNerdFonts () {
 mkdir -p ~/Development
 cd ~/Development

 if [ ! -d "./nerd-fonts" ] ; then
   git clone --depth 1 https://github.com/ryanoasis/nerd-fonts.git
 fi

 cd nerd-fonts

 ./install.sh SpaceMono
}

# Fabric shortcuts
function fysum() {
  fabric -y $1 --stream --pattern summarize
}

function fysumb() {
  fabric -y $1 --stream --pattern summarize -m=gpt-4o-mini
}
