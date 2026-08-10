#!/bin/bash
# highlight-nudge.sh — the 16:00 checkpoint of the daily flow.
#
# Reads today's highlight from ~/mc/highlight.json (via balls.py) and pushes a
# notification if it has NOT been marked started. Silent otherwise.
#
# Deliberately standalone: it does NOT touch the Fleet Chief of Staff, whose
# low-noise decision/blocker behaviour stays exactly as it is.
#
# Channels:
#   1. macOS notification  — always, no configuration needed
#   2. ntfy                — only if NTFY_TOPIC is set in ~/mc/highlight-nudge.conf
#
# Exit 0 always: a nudge failing must never surface as a launchd error loop.

set -uo pipefail

CONF="$HOME/mc/highlight-nudge.conf"
LOG="$HOME/mc/.highlight-nudge.log"
NTFY_SERVER="https://ntfy-home.aviad.cloud"
NTFY_TOPIC=""

[ -f "$CONF" ] && . "$CONF"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >>"$LOG"; }

# Weekdays only (Israeli week: Sun-Thu). date +%u -> 1=Mon .. 7=Sun
dow=$(date +%u)
if [ "$dow" = "5" ] || [ "$dow" = "6" ]; then
    log "skip: Fri/Sat"
    exit 0
fi

# --quiet-if-started exits non-zero when started, or when no highlight is set
# for today, or when the stored highlight is stale. Any of those = stay silent.
if ! HL=$(python3 "$HOME/.scripts/balls.py" get --quiet-if-started 2>>"$LOG"); then
    log "skip: no unstarted highlight for today"
    exit 0
fi

TITLE="16:00 checkpoint"
BODY="Not started yet: ${HL}

Switch to it now — no negotiation."

# 1. macOS notification (always)
/usr/bin/osascript -e "display notification \"${HL//\"/\\\"}\" with title \"$TITLE\" sound name \"Submarine\"" \
    >>"$LOG" 2>&1 || log "warn: osascript failed"

# 2. ntfy (opt-in)
if [ -n "$NTFY_TOPIC" ]; then
    /usr/bin/curl -fsS -m 15 \
        -H "Title: $TITLE" \
        -H "Priority: high" \
        -H "Tags: dart" \
        -d "$BODY" \
        "$NTFY_SERVER/$NTFY_TOPIC" >>"$LOG" 2>&1 || log "warn: ntfy push failed"
fi

log "nudged: $HL"
exit 0
