#!/bin/zsh

    YADM=$HOME/.local/bin/yadm

# Check yadm command
if [ ! -f $YADM ]; then
    echo 'No yadm command'
    exit 1
fi

$YADM gitconfig diff.tool vimdiff
$YADM gitconfig difftool.prompt true
$YADM gitconfig difftool.vimdiff.cmd 'nvim -d "$LOCAL" "$REMOTE"'
$YADM gitconfig merge.tool vimmerge
$YADM gitconfig mergetool.prompt true
$YADM gitconfig mergetool.vimmerge.cmd 'nvim -d $BASE $LOCAL $REMOTE $MERGED -c "$wincmd w" -c "wincmd J"'

