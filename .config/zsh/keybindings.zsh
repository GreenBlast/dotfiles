# git
function git_prepare() {
    if [ -n "$BUFFER" ];
        then
            BUFFER="git commit -m \"$BUFFER\""
    fi

    if [ -z "$BUFFER" ];
        then
            BUFFER="git commit -v"
    fi

    zle accept-line
}
zle -N git_prepare
bindkey "^g" git_prepare

# yadm
function yadm_prepare() {
    if [ -n "$BUFFER" ];
        then
            BUFFER="yadm commit -m \"$BUFFER\""
    fi

    if [ -z "$BUFFER" ];
        then
            BUFFER="yadm commit -v"
    fi

    zle accept-line
}
zle -N yadm_prepare
bindkey "^y" yadm_prepare
