# Setting nvim
#alias vim=/usr/bin/nvim

# Setting yadm
alias yadm=~/.local/bin/yadm

alias yst='yadm status'
alias ya='yadm add'
alias yau='yadm add -u'
alias yaa='yadm add --all'
alias yapa='yadm add --patch'      # stage hunk by hunk — $HOME drifts on its own
alias yc='yadm commit -v'
alias ycm='yadm commit -m'
alias yp='yadm push'
alias yl='yadm pull'
alias ylg='yadm log --oneline --decorate --graph'
# NB: yd / ydf / ydfn are yt-dlp (see below), so yadm diff avoids the yd* prefix
alias ydi='yadm diff'
alias ydis='yadm diff --staged'
# alias ydf='yadm difftool'
alias ydfs='yadm difftool --staged'
alias ysuri='yadm submodule update --recursive --init'

# yadm-specific — no git equivalent
# Subshell with GIT_DIR/GIT_WORK_TREE set, so plain `git` (and git TUIs) target
# dotfiles. NOTE: yadm starts zsh with -f, so ~/.zshrc is skipped and the g*
# aliases are NOT available in here — that is what the y* mirrors above are for.
# Takes a command as ONE string: ye 'git log --oneline | head'
alias ye='yadm enter'
alias yalt='yadm alt'              # re-link alternates (##os.Darwin, ##class.Home, ##default)
alias ylist='yadm list -a'         # every tracked file
alias ybs='yadm bootstrap'
alias gdf='git difftool'
alias gdfs='git difftool --staged'
alias gcod='git checkout .'
alias gmd='git merge develop'

# Worktrunk (wt) worktree shortcuts
alias wts='wt switch'             # switch to a worktree (interactive picker if no arg)
alias wtsc='wt switch --create'   # create a new branch + worktree, then switch to it
alias wtsx='wt switch --create -x claude'  # create worktree and launch Claude Code in it
alias wtl='wt list'               # list worktrees and their status
alias wtr='wt remove'             # remove worktree (deletes branch if merged)
alias wtm='wt merge'              # squash+rebase, fast-forward target, remove worktree

# Mission Control (mc) shortcuts — ~/Projects/mission-control
# Fleet: the attention queue over the by-hand claude panes (default tmux socket)
alias mcn='mc next'               # priority queue, top 12
alias mcna='mc next --all'        # ...plus everything below the cut
alias mcns='mc next --starred'    # only the curated priority set
alias mcnw='mc next --work'       # work panes only
alias mcnp='mc next --personal'   # personal panes only
alias mcg='mc go'                 # jump to a pane (ref = n | %id | session:win)
alias mcf='mc fleet'              # raw census: every claude pane + %id + age + bucket
alias mcs='mc stats'              # backlog counts + trend vs 1d/7d + sparkline
alias mcz='mc snooze'             # hide a pane until 3h | 18:00 | evening | tomorrow
alias mcst='mc star'              # add to the priority set (bare = list)
alias mcus='mc unstar'
# Initiatives: the dedicated `tmux -L mc` sessions
alias mcl='mc ls'                 # sessions + pending gate counts
alias mca='mc attach'             # attach to an initiative session
alias mcgt='mc gates'             # gates awaiting approve/deny
alias mcc='mc concierge --launch' # start the concierge (Remote Control -> Claude app)

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
# alias pa=' pocket-cli add --url'

function  pat() {
    # pocket-cli add --tags="train reading" --url "$1"
    . ~/.scripts/verify_hoarder_cli.sh 
    verify_hoarder_cli_key_and_address
    hoarder --api-key "${HOARDER_KEY}" --server-addr "${HOARDER_ADDRESS}" bookmarks add --link "$1" --tag-name "train reading"
}

function  pav() {
    # pocket-cli add --tags="videos" --url "$1"
    . ~/.scripts/verify_hoarder_cli.sh 
    verify_hoarder_cli_key_and_address
    hoarder --api-key "${HOARDER_KEY}" --server-addr "${HOARDER_ADDRESS}" bookmarks add --link "$1" --tag-name "videos"
}

function apat() {
  # Split the input string on newlines and spaces
  urls=("${(f)@}")

  . ~/.scripts/verify_hoarder_cli.sh 
  verify_hoarder_cli_key_and_address
  # Loop through each URL and execute curl
  for url in "${urls[@]}"; do
      hoarder --api-key "${HOARDER_KEY}" --server-addr "${HOARDER_ADDRESS}" bookmarks add --link "$1" --tag-name "train reading"
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
alias ydf="yt-dlp -S 'vcodec:h264,fps,res:720,acodec:m4a' --js-runtimes node"
alias ydfn="yt-dlp -S 'vcodec:h264,fps,res:720,acodec:m4a' --no-playlist --js-runtimes node"
# alias ydf="yt-dlp -f '232+233' --merge-output-format mp4"
# alias ydf="yt-dlp -f 22"
# alias ydfa="yt-dlp -f 'bestvideo[height<=720]+bestaudio[ext=m4a]/best[height<=720]' --merge-output-format mp4"

alias rss="~/.scripts/get_youtube_rss.py "

alias lzg='lazygit'
alias lzd='lazydocker'

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


ytchat() {
    emulate -L zsh
    setopt local_options null_glob
    local d=$(mktemp -d -t ytchat.XXXXXX)
    local title=$(yt-dlp --write-auto-sub --skip-download --sub-langs ".*-orig,en" --sub-format vtt \
      --print "%(title)s" --no-simulate -o "$d/sub.%(ext)s" "$1" 2>/dev/null)
    local tmp="$d/transcript.txt"
    local vtts=("$d"/*-orig.vtt)
    if (( ${#vtts[@]} == 0 )); then
      vtts=("$d"/*.vtt)
    fi
    if (( ${#vtts[@]} == 0 )); then
      echo "ytchat: no subtitles found for $1" >&2
      return 1
    fi
    cat "${vtts[@]}" \
      | sed -E -e 's/<v ([^>]*)>/[\1]: /g' \
               -e 's/<[^>]*>//g' \
               -e 's/&gt;/>/g; s/&lt;/</g; s/&amp;/\&/g; s/&#39;/'\''/g; s/&quot;/"/g' \
               -e '/^(WEBVTT|Kind:|Language:|[0-9:.]+ -->|$)/d' \
               -e 's/^[[:space:]]+//; s/[[:space:]]+$//' \
      | awk 'NF && !seen[$0]++' > "$tmp"
    if [[ ! -s "$tmp" ]]; then
      echo "ytchat: empty transcript for $1" >&2
      return 1
    fi
    claude --add-dir "$d" -- "Video title: ${title}. Video URL: $1. Read the YouTube transcript at $tmp (>> = speaker change, [Name] = identified speaker). Summarize in 5 bullets plus 3 takeaways. I'll ask follow-ups."
}

ytchatl() {
    emulate -L zsh
    setopt local_options null_glob
    local d=$(mktemp -d -t ytchat.XXXXXX)
    local title=$(yt-dlp --write-auto-sub --skip-download --sub-langs ".*-orig,en" --sub-format vtt \
      --print "%(title)s" --no-simulate -o "$d/sub.%(ext)s" "$1" 2>/dev/null)
    local tmp="$d/transcript.txt"
    local vtts=("$d"/*-orig.vtt)
    if (( ${#vtts[@]} == 0 )); then
      vtts=("$d"/*.vtt)
    fi
    if (( ${#vtts[@]} == 0 )); then
      echo "ytchatl: no subtitles found for $1" >&2
      return 1
    fi
    cat "${vtts[@]}" \
      | sed -E -e 's/<v ([^>]*)>/[\1]: /g' \
               -e 's/<[^>]*>//g' \
               -e 's/&gt;/>/g; s/&lt;/</g; s/&amp;/\&/g; s/&#39;/'\''/g; s/&quot;/"/g' \
               -e '/^(WEBVTT|Kind:|Language:|[0-9:.]+ -->|$)/d' \
               -e 's/^[[:space:]]+//; s/[[:space:]]+$//' \
      | awk 'NF && !seen[$0]++' > "$tmp"
    if [[ ! -s "$tmp" ]]; then
      echo "ytchatl: empty transcript for $1" >&2
      return 1
    fi
    claude --add-dir "$d" --model 'claude-opus-4-7[1m]' -- "Video title: ${title}. Video URL: $1. Read the YouTube transcript at $tmp (>> = speaker change, [Name] = identified speaker). Summarize in 5 bullets plus 3 takeaways. I'll ask follow-ups."
}

