#!/usr/bin/env bash
# Daily concierge respawn: stop the concierge's claude and relaunch it fresh, so
# it lands at the top of the Claude app's session list instead of sinking under
# the ~60 fleet sessions. Losing its context is cheap: ~/mc/concierge/STATUS.md
# is the durable memory, and the old transcript stays resumable by uuid.
#
# Usage: concierge-respawn.sh "Concierge Mac"   (or "Concierge devbox")
# Scheduled by launchd (Mac, com.aviad.concierge-respawn) / systemd user timer
# (devbox, concierge-respawn.timer). Never creates the tmux session itself: under
# systemd a tmux server started here would be reaped with the job's cgroup.
set -uo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

name="${1:?usage: concierge-respawn.sh \"Concierge <host>\"}"
log="$HOME/mc/log/concierge-respawn.log"
mkdir -p "$(dirname "$log")"
say() { echo "$(date '+%F %T') $*" | tee -a "$log"; }
tm() { tmux -L mc "$@"; }
url_in_pane() { tm capture-pane -p -J -S -200 -t concierge | grep -oE 'claude\.ai/code/session_[A-Za-z0-9]+' | tail -1; }

tm has-session -t =concierge 2>/dev/null \
  || { say "no 'concierge' session on tmux -L mc; run 'mc concierge --launch --name \"$name\"' by hand"; exit 1; }

# Leave it alone if it's mid-reply or was used in the last 30 minutes.
if tm capture-pane -p -t concierge | grep -q 'esc to interrupt'; then
  say "concierge is mid-turn; skipping today"; exit 0
fi
# "Used" = the newest timestamped entry, not the file's mtime: the mtime gets
# bumped with no new conversation (skipped 2026-10-05 and 10-06 while idle 2 days).
newest_entry_epoch() {
  local f ts e newest=0
  while IFS= read -r f; do
    ts=$(tail -n 400 "$f" | grep -oE '"timestamp":"[^"]+"' | tail -1 | cut -d'"' -f4)
    [[ -n "$ts" ]] || continue
    e=$(date -u -d "$ts" +%s 2>/dev/null || date -j -u -f '%Y-%m-%dT%H:%M:%S' "${ts%%.*}" +%s 2>/dev/null) || continue
    (( e > newest )) && newest=$e
  done < <(find "$@" -name '*.jsonl' -mmin -30 2>/dev/null)
  echo "$newest"
}
if (( $(date +%s) - $(newest_entry_epoch "$HOME"/.claude/projects/*mc-concierge*) < 1800 )); then
  say "concierge used in the last 30 min; skipping today"; exit 0
fi

# The claude's process title is its version string, so find it by argv among the
# pane shell's children (a helper zsh sits there too).
pane_pid=$(tm display -p -t concierge '#{pane_pid}')
cpid=""
for c in $(pgrep -P "$pane_pid"); do
  ps -o args= -p "$c" | grep -qE '(^|/)claude( |$)' && cpid=$c
done
old_url=$(url_in_pane)

# Stop the running claude FIRST: `mc concierge --launch` only types into the
# pane, so with claude alive the launch line would land as a prompt.
if [[ -n "$cpid" ]]; then
  kill "$cpid"
  for _ in $(seq 1 20); do kill -0 "$cpid" 2>/dev/null || break; sleep 1; done
  if kill -0 "$cpid" 2>/dev/null; then kill -9 "$cpid"; sleep 1; fi
fi
cmd=$(tm display -p -t concierge '#{pane_current_command}')
case "$cmd" in
  zsh|-zsh|bash|-bash|sh) ;;
  *) say "pane still running '$cmd' after stopping pid ${cpid:-none}; not relaunching"; exit 1 ;;
esac

mc concierge --launch --name "$name" >/dev/null

# Remote Control prints the session URL once connected; wait for a new one.
for _ in $(seq 1 90); do
  new_url=$(url_in_pane)
  if [[ -n "$new_url" && "$new_url" != "$old_url" ]]; then
    say "respawned \"$name\" (old pid ${cpid:-none}); Remote Control active"; exit 0
  fi
  sleep 1
done
say "relaunched \"$name\" but no new Remote Control session after 90s; check 'mc attach concierge'"
exit 1
