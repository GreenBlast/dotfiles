#!/bin/bash
# Appends the lines to make bashrc search for the color support and add it if exists
# If the lines already in bashrc, they will not be added

append_line() {
  set -e

  local update line file pat lno
  update="$1"
  line="$2"
  file="$3"
  pat="${4:-}"

  echo "Update $file:"
  echo "  - $line"
  [ -f "$file" ] || touch "$file"
  if [ $# -lt 4 ]; then
    lno=$(\ag -Q "$line" "$file" | sed 's/:.*//' | tr '\n' ' ')
  else
    lno=$(\ag -Q "$pat" "$file" | sed 's/:.*//' | tr '\n' ' ')
  fi
  if [ -n "$lno" ]; then
    echo "    - Already exists: line #$lno"
  else
    if [ $update -eq 1 ]; then
      echo >> "$file"
      echo "$line" >> "$file"
      echo "    + Added"
    else
      echo "    ~ Skipped"
    fi
  fi
  echo
  set +e
}

dest="${HOME}/.bashrc"
line="\
if [ 'find /lib/terminfo /usr/share/terminfo -name \"*256*\" | grep xterm-256color' ]; then
    export TERM='xterm-256color'
else
    export TERM='xterm-color'
fi"

append_line 1 "$line" "$dest"
