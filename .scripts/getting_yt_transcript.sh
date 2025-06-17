#!/bin/bash
VideoURL="$1"
LANG="en"
TranscriptFile="$(mktemp)"
yt-dlp --quiet --no-warnings --write-auto-sub --sub-lang $LANG --skip-download --sub-format vtt -o "$TranscriptFile" "$VideoURL"
TranscriptFile="$TranscriptFile.$LANG.vtt"
cat $TranscriptFile
rm $TranscriptFile
