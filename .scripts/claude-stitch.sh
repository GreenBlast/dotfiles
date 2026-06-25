#!/usr/bin/env bash
# claude-stitch.sh — after a reboot, resume each captured Claude session IN
# PLACE: directly into the same tmux pane it was in before the reboot.
#
# Contrast with claude-rehydrate.sh, which builds separate "<orig>-restore"
# sessions. This one reuses the panes tmux-resurrect brought back (empty shells
# at the right cwd), so your layout is exactly as it was — no extra sessions.
#
# Reads ~/.claude-restore.tsv (addr<TAB>cwd<TAB>target<TAB>method<TAB>title),
# written by claude-session-map.py.
#
# Safe + IDEMPOTENT (re-runnable):
#   * resolves each TSV pane address to the live pane and checks its cwd
#   * types `claude --resume <id>` ONLY into a pane that is an idle shell;
#     a pane already running Claude (or otherwise busy) is skipped, so a 2nd
#     run only fills gaps and never types into a live Claude
#   * UNRESOLVED / PICK rows are skipped (resume those by hand)
#
# Usage:
#   claude-stitch.sh [path-to-tsv]      # default ~/.claude-restore.tsv
#   DRY_RUN=1 claude-stitch.sh          # preview, change nothing
#   STAGGER=0 claude-stitch.sh          # fire all at once (default: 1s apart)
#   FORCE=1   claude-stitch.sh          # stitch even if pane cwd != captured cwd
set -u

TSV="${1:-$HOME/.claude-restore.tsv}"
STAGGER="${STAGGER:-1}"

[ -f "$TSV" ] || { echo "No map at $TSV — run claude-session-map.py BEFORE rebooting."; exit 1; }
command -v tmux >/dev/null 2>&1 || { echo "tmux not found"; exit 1; }
tmux list-sessions >/dev/null 2>&1 || { echo "no tmux server running"; exit 1; }

is_shell() { case "$1" in zsh|-zsh|bash|-bash|sh|-sh|fish|-fish) return 0;; *) return 1;; esac; }

sent=0; skipped=0; gone=0; unresolved=0; mism=0
while IFS=$'\t' read -r addr cwd target method title; do
  [ -n "${addr:-}" ] || continue

  # unresolved rows: nothing reliable to resume
  if [ -z "${target:-}" ] || [ "$target" = "PICK" ]; then
    printf 'PICK  %-22s «%s» (unresolved — resume by hand)\n' "$addr" "$title"
    unresolved=$((unresolved+1)); continue
  fi

  # address -> live pane id (stable handle); gone if the pane no longer exists
  pid=$(tmux display-message -p -t "$addr" '#{pane_id}' 2>/dev/null) || pid=""
  if [ -z "$pid" ]; then
    printf 'GONE  %-22s «%s» (pane no longer exists)\n' "$addr" "$title"
    gone=$((gone+1)); continue
  fi

  pcwd=$(tmux display-message -p -t "$pid" '#{pane_current_path}' 2>/dev/null)
  pcmd=$(tmux display-message -p -t "$pid" '#{pane_current_command}' 2>/dev/null)

  # cwd guard: protects against window-index drift pointing addr at a wrong pane
  if [ "$pcwd" != "$cwd" ] && [ -z "${FORCE:-}" ]; then
    printf 'MISM  %-22s pane cwd "%s" != captured "%s" — skipped (FORCE=1 to override)\n' "$addr" "$pcwd" "$cwd"
    mism=$((mism+1)); continue
  fi

  # idempotency guard: only stitch into an idle shell
  if ! is_shell "$pcmd"; then
    printf 'SKIP  %-22s «%s» (already running / busy: %s)\n' "$addr" "$title" "$pcmd"
    skipped=$((skipped+1)); continue
  fi

  if [ -n "${DRY_RUN:-}" ]; then
    printf '[dry] %-22s «%s»  ->  claude --resume %s\n' "$addr" "$title" "$target"
    sent=$((sent+1)); continue
  fi

  printf 'SEND  %-22s «%s»\n' "$addr" "$title"
  tmux send-keys -t "$pid" "claude --resume $target" C-m
  sent=$((sent+1))
  [ "$STAGGER" != "0" ] && sleep "$STAGGER"
done < "$TSV"

echo
echo "stitched: $sent   skipped(up/busy): $skipped   cwd-mismatch: $mism   unresolved(PICK): $unresolved   gone: $gone"
[ "$mism" -gt 0 ] && echo "note: cwd mismatches were skipped — inspect, then re-run with FORCE=1 if they're fine."
exit 0
