#!/usr/bin/env bash
# claude-rehydrate.sh — after a reboot, re-open all Claude Code sessions that
# were captured by claude-session-map.py (~/.claude-restore.tsv).
#
# DESIGN (deliberately safe): it does NOT inject into the panes that
# tmux-resurrect restored. Instead it builds *fresh, isolated* tmux sessions —
# one per original session, named "<orig>-restore" — and launches each
# `claude --resume <id>` in its own window there. That way nothing can clobber
# or conflict with the restored layout, and if anything looks wrong you just
# `tmux kill-session -t <orig>-restore` and try again. Reversible by design.
#
# Usage:
#   claude-rehydrate.sh [path-to-tsv]        # default ~/.claude-restore.tsv
#   SUFFIX=copy claude-rehydrate.sh          # name sessions "<orig>-copy"
set -u

TSV="${1:-$HOME/.claude-restore.tsv}"
SUFFIX="${SUFFIX:-restore}"

[ -f "$TSV" ] || { echo "No map at $TSV — run claude-session-map.py BEFORE rebooting."; exit 1; }
command -v tmux >/dev/null 2>&1 || { echo "tmux not found"; exit 1; }

sanitize() { printf '%s' "$1" | tr -c 'A-Za-z0-9._ -' '_' | cut -c1-40; }

declare -A state   # orig -> restore-session-name, or "SKIP"
opened=0; skipped=0; pickers=0

while IFS=$'\t' read -r addr cwd target method title; do
  [ -n "${addr:-}" ] || continue
  orig="${addr%%:*}"
  sess="${orig}-${SUFFIX}"
  wname="$(sanitize "$title")"; [ -n "$wname" ] || wname="claude"

  if [ -n "$target" ] && [ "$target" != "PICK" ]; then
    cmd="claude --resume $target"
  else
    cmd="claude --resume"          # unresolved -> interactive picker
    wname="PICK_${wname}"; pickers=$((pickers+1))
  fi

  # first row for this original session: create the restore session (detached)
  if [ -z "${state[$orig]:-}" ]; then
    if tmux has-session -t "=$sess" 2>/dev/null; then
      echo "! '$sess' already exists — skipping (kill it first to redo)"
      state[$orig]="SKIP"
    elif [ -n "${DRY_RUN:-}" ]; then
      echo "[dry] new-session $sess  (cwd=$cwd)  win='$wname'  ->  $cmd"
      state[$orig]="$sess"; opened=$((opened+1)); continue
    else
      win=$(tmux new-session -d -s "$sess" -c "$cwd" -n "$wname" -P -F '#{window_id}')
      tmux send-keys -t "$win" "$cmd" Enter
      state[$orig]="$sess"; opened=$((opened+1))
      continue
    fi
  fi

  if [ "${state[$orig]}" = "SKIP" ]; then skipped=$((skipped+1)); continue; fi

  if [ -n "${DRY_RUN:-}" ]; then
    echo "[dry] new-window in ${state[$orig]}  (cwd=$cwd)  win='$wname'  ->  $cmd"
    opened=$((opened+1)); continue
  fi
  win=$(tmux new-window -t "${state[$orig]}" -c "$cwd" -n "$wname" -P -F '#{window_id}')
  tmux send-keys -t "$win" "$cmd" Enter
  opened=$((opened+1))
done < "$TSV"

echo
echo "Re-opened $opened claude window(s); skipped $skipped; $pickers need a manual pick (PICK_* windows)."
echo "Restore sessions:"
for o in "${!state[@]}"; do [ "${state[$o]}" != "SKIP" ] && echo "  tmux attach -t ${state[$o]}"; done | sort
echo
echo "Tip: ${opened} claude TUIs launch at once — heavy. To do a subset, trim ~/.claude-restore.tsv first."
