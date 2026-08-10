#!/usr/bin/env python3
"""
balls.py — engine for the daily flow (see: vault note "Productivity System Design").

Clusters the live Claude Code fleet into "balls" (commitments), ranks them by how
starved they are, and manages the day's highlight.

Source of truth for the highlight is ~/mc/highlight.json, NOT the daily note.
The daily note is mirrored into when it exists, but nothing depends on Obsidian
being open or Periodic Notes having run.

Subcommands:
  list            balls with next actions, ranked most-starved first
  suggest         the 2-3 balls that best fit as today's highlight
  set  <text>     record today's highlight (--ball N to tag it)
  get             print today's highlight (exit 1 if none set / stale)
  started         mark the highlight as started (silences the nudge)
  snapshot        write today's fleet snapshot to ~/mc/
  daydiff         what closed / opened since the day's first snapshot
"""

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
MC = os.path.join(HOME, "mc")
VAULT = os.path.join(HOME, "Projects/ObsidianVaults/Aviad")
DAILY = os.path.join(VAULT, "Daily")
BALLS_CFG = os.path.join(MC, "balls.json")
HIGHLIGHT = os.path.join(MC, "highlight.json")
MC_BIN = os.path.join(HOME, ".local/bin/mc")


def today():
    return dt.date.today().isoformat()


# ---------------------------------------------------------------- fleet

AGE_UNKNOWN = 999999  # mc sentinel: no readable transcript timestamp


def sweep():
    """Run `mc next --all --tsv` and return list of session dicts."""
    try:
        out = subprocess.run(
            [MC_BIN, "next", "--all", "--tsv"],
            capture_output=True, text=True, timeout=120, check=True,
        ).stdout
    except FileNotFoundError:
        sys.exit(f"balls.py: mc binary not found at {MC_BIN}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"balls.py: mc failed ({e.returncode}): {e.stderr[:300]}")
    except subprocess.TimeoutExpired:
        sys.exit("balls.py: mc timed out after 120s")
    rows = list(csv.DictReader(out.splitlines(), delimiter="\t"))
    for r in rows:
        try:
            r["agemin"] = int(r.get("agemin") or 0)
        except ValueError:
            r["agemin"] = 0
    return rows


def snapshot_path(date=None, suffix=""):
    return os.path.join(MC, f"fleet-snapshot-{date or today()}{suffix}.tsv")


def write_snapshot(path=None):
    path = path or snapshot_path()
    out = subprocess.run(
        [MC_BIN, "next", "--all", "--tsv"], capture_output=True, text=True, check=True
    ).stdout
    with open(path, "w") as f:
        f.write(out)
    return path


def load_snapshot(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        try:
            r["agemin"] = int(r.get("agemin") or 0)
        except ValueError:
            r["agemin"] = 0
    return rows


# ---------------------------------------------------------------- balls

def load_balls():
    with open(BALLS_CFG) as f:
        return json.load(f)["balls"]


_KW_CACHE = {}


def kw_match(keyword, title):
    """Word-boundary match, not bare substring.

    Plain `in` produced real misfiles on 2026-08-04: 'egress' matched
    "regression", 'merge' matched "emergency". Boundaries are non-alphanumeric,
    so multi-word and hyphenated keywords ('cost-explorer', 'map pin') still work.
    """
    rx = _KW_CACHE.get(keyword)
    if rx is None:
        rx = _KW_CACHE[keyword] = re.compile(
            r"(?<![a-z0-9])" + re.escape(keyword.strip()) + r"s?(?![a-z0-9])")
    return bool(rx.search(title))


def assign(rows, balls):
    """Assign each session to the first matching ball. Returns (by_id, unmatched)."""
    by_id = {b["id"]: {"ball": b, "sessions": []} for b in balls}
    unmatched = []
    for r in rows:
        title = (r.get("title") or "").lower()
        for b in balls:
            if any(kw_match(k, title) for k in b["keywords"]):
                by_id[b["id"]]["sessions"].append(r)
                break
        else:
            unmatched.append(r)
    return by_id, unmatched


def fmt_age(mins):
    m = int(mins)
    if m >= 1440:
        return f"{m // 1440}d"
    if m >= 60:
        return f"{m // 60}h"
    return f"{m}m"


def clean_label(s):
    s = " ".join((s or "").replace("⏸", "").replace("⚙", "").split())
    for p in ("working — was:", "Next action:", "Next action is",
              "Next steps:", "Next up is", "next action is", "Next action"):
        if s.startswith(p):
            s = s[len(p):].strip(" :")
    return s


def ball_rows(by_id):
    """One summary row per ball, sorted most-starved first."""
    out = []
    for bid, d in by_id.items():
        s = d["sessions"]
        b = d["ball"]
        if s:
            # AGE_UNKNOWN (999999) is mc's sentinel for "no readable transcript
            # timestamp" (bin/mc:492,651) — NOT an age. mc already neutralises it
            # in fleet_sort ("so a pane with no transcript is never a false
            # extreme", bin/mc:760); this script must do the same or a session
            # with no transcript reads as 694 days old and drags its whole ball
            # to the top of the starved-first sort. Observed flapping on 5
            # sessions, 2026-08-09.
            dated = [x for x in s if x["agemin"] < AGE_UNKNOWN]
            undated = len(s) - len(dated)
            fresh = min((x["agemin"] for x in dated), default=None)
            # Signal hierarchy: pinned > snoozed > starred.
            # `pinned` is set deliberately by hand and is the only real
            # statement of priority; `starred` tracks whatever was touched
            # recently and is far noisier (23 of 56 on 2026-08-04 vs 4 pinned).
            # So a pinned session's next action wins over the merely-freshest.
            pinned_s = [x for x in s if x.get("pinned") == "1"]
            snoozed_s = [x for x in s if (x.get("snoozed") or "-") != "-"]
            # prefer a DATED session when choosing whose action to show, so the
            # headline action isn't picked by a sentinel sorting to "freshest".
            pool = [x for x in (pinned_s or s) if x["agemin"] < AGE_UNKNOWN] or (pinned_s or s)
            hottest = min(pool, key=lambda x: x["agemin"])
            action = clean_label(hottest.get("label"))
            starred = sum(1 for x in s if x.get("starred") == "1")
            # cold = untouched for 3+ days. A ball can look fed because one
            # tangential session was touched today while the substance rots.
            # Undated sessions are neither cold nor fresh — they are unknown.
            cold = sum(1 for x in dated if x["agemin"] >= 3 * 1440)
            npin, nsnooze = len(pinned_s), len(snoozed_s)
        else:
            undated = 0
            fresh = None
            # no live session: fall back to the next action configured in
            # balls.json, since these balls never surface from the fleet
            action = b.get("next_action") or "— no live session, no configured next action —"
            starred = 0
            cold = 0
            npin = nsnooze = 0
        out.append({
            "id": bid, "name": b["name"], "domain": b["domain"],
            "note": b.get("note", ""), "n": len(s), "starred": starred,
            "fresh_min": fresh, "action": action, "cold": cold,
            "pinned": npin, "snoozed": nsnooze, "undated": undated,
        })
    # pinned balls first (a deliberate statement of priority), then
    # no-session balls, then by freshest-session age descending
    out.sort(key=lambda r: (-r["pinned"], r["fresh_min"] is not None, -(r["fresh_min"] or 0)))
    return out


def _print_ball(r):
    if r["fresh_min"] is None:
        # distinguish "no sessions at all" from "sessions exist, ages unknown"
        mark, age = ("❔", "   ?") if r["n"] else ("🔴", "  --")
    elif r["fresh_min"] >= 3 * 1440:
        mark, age = "🟠", fmt_age(r["fresh_min"]).rjust(4)
    else:
        mark, age = "  ", fmt_age(r["fresh_min"]).rjust(4)
    star = f" ★{r['starred']}" if r["starred"] else ""
    cold = f", {r['cold']} cold" if r["cold"] else ""
    zzz = f", {r['snoozed']} snoozed" if r["snoozed"] else ""
    unk = f", {r['undated']} undated" if r.get("undated") else ""
    note = f"  [{r['note']}]" if r["note"] else ""
    pin = f"📌{r['pinned']} " if r["pinned"] else ""
    print(f"{mark} {age}  {pin}#{r['id']:<2} {r['name']}  ({r['n']} sessions{star}{cold}{zzz}{unk}){note}")
    print(f"          → {r['action'][:110]}")


def cmd_list(args):
    rows = sweep()
    balls = load_balls()
    by_id, unmatched = assign(rows, balls)
    summary = ball_rows(by_id)

    want = getattr(args, "domain", None)
    if want:
        summary = [r for r in summary if r["domain"] == want]

    print(f"BALLS — {len(rows)} live sessions, {today()}")
    print("Ranked most-starved first. 🔴 = nothing live on it.")

    # Work and personal are SEPARATE ladders (Aviad, 2026-08-09): they get
    # different time allocation, so ranking them against each other in one
    # list permanently buries personal behind anything with a counterparty.
    if want:
        print()
        for r in summary:
            _print_ball(r)
    else:
        for dom, label in (("work", "WORK"), ("personal", "PERSONAL")):
            group = [r for r in summary if r["domain"] == dom]
            if not group:
                continue
            starved = sum(1 for r in group if r["fresh_min"] is None)
            print(f"\n─── {label} ({len(group)} balls, {starved} starved) " + "─" * (28 - len(label)))
            for r in group:
                _print_ball(r)
    if unmatched and args.verbose:
        print(f"\nUnmatched sessions ({len(unmatched)}) — consider adding keywords to balls.json:")
        for r in sorted(unmatched, key=lambda x: -x["agemin"]):
            age = "    ?" if r["agemin"] >= AGE_UNKNOWN else fmt_age(r["agemin"])
            print(f"    {age:>5}  {r['title'][:64]}")
    elif unmatched:
        print(f"\n({len(unmatched)} sessions matched no ball — run with -v to see them)")


def cmd_suggest(args):
    rows = sweep()
    by_id, _ = assign(rows, load_balls())
    summary = ball_rows(by_id)
    pinned_first = [r for r in summary if r["pinned"]]
    if pinned_first:
        print("PINNED — you marked these by hand, so they outrank staleness:\n")
        for r in pinned_first:
            print(f"  📌 #{r['id']} {r['name']}  ({r['pinned']} pinned session(s))")
            print(f"     → {r['action'][:110]}\n")
        print("-" * 60 + "\n")
    print("Otherwise — most starved first.\n")
    print("Rule: external deadline or a blocked person wins outright; otherwise the")
    print("most starved ball that fits today's slots. Pick a NEXT ACTION, not a ball.\n")
    for r in summary[:3]:
        age = "no live session" if r["fresh_min"] is None else f"freshest {fmt_age(r['fresh_min'])} old"
        print(f"  #{r['id']} {r['name']}  ({r['domain']}, {age})")
        print(f"     → {r['action'][:110]}\n")
    print('Sanity check: "which of these would annoy me most in a month if it still hadn\'t moved?"')


# ---------------------------------------------------------------- highlight

def read_highlight():
    if not os.path.exists(HIGHLIGHT):
        return None
    try:
        with open(HIGHLIGHT) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def daily_note_path(date=None):
    return os.path.join(DAILY, f"{date or today()}.md")


def mirror_to_daily_note(text, ball=None):
    """Best-effort mirror into the daily note. Never creates the note (Templater
    can clobber agent-created notes); returns a status string."""
    p = daily_note_path()
    if not os.path.exists(p):
        return "daily note does not exist yet — not created (Templater safety)"
    with open(p) as f:
        body = f.read()
    line = f"- [ ] **{text}**"
    if ball:
        line += f"  — ball #{ball}"
    if "## Daily highlight" in body:
        # replace the first unchecked placeholder under the heading, else append
        pat = re.compile(r"(## Daily highlight\n)(.*?)(?=\n## |\Z)", re.S)
        m = pat.search(body)
        seg = m.group(2)
        if line.split("**")[1] in seg:
            return "already present in daily note"
        seg = seg.rstrip() + "\n" + line + "\n"
        body = body[:m.start(2)] + seg + body[m.end(2):]
    else:
        anchor = "## Evening log"
        block = f"## Daily highlight\n\n{line}\n\n"
        body = body.replace(anchor, block + anchor, 1) if anchor in body else body.rstrip() + "\n\n" + block
    with open(p, "w") as f:
        f.write(body)
    return "mirrored into daily note"


def cmd_set(args):
    text = " ".join(args.text).strip()
    if not text:
        sys.exit("balls.py set: refusing to record an empty highlight")
    data = {
        "date": today(),
        "text": text,
        "ball": args.ball,
        "set_at": dt.datetime.now().isoformat(timespec="seconds"),
        "started": False,
    }
    with open(HIGHLIGHT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"Highlight for {today()}: {text}")
    if args.ball:
        print(f"  ball #{args.ball}")
    print(f"  {mirror_to_daily_note(text, args.ball)}")
    print(f"  16:00 nudge will fire unless you run: balls.py started")


def cmd_get(args):
    h = read_highlight()
    if not h:
        sys.exit(1)
    if h.get("date") != today():
        sys.exit(1)
    if args.quiet_if_started and h.get("started"):
        sys.exit(1)
    print(h["text"])


def cmd_started(args):
    h = read_highlight()
    if not h or h.get("date") != today():
        sys.exit("balls.py: no highlight set for today")
    h["started"] = True
    h["started_at"] = dt.datetime.now().isoformat(timespec="seconds")
    with open(HIGHLIGHT, "w") as f:
        json.dump(h, f, indent=1)
    print(f"Marked started: {h['text']}")


# ---------------------------------------------------------------- day diff

def cmd_snapshot(args):
    # first snapshot of the day keeps the plain name; later ones get a time suffix
    base = snapshot_path()
    path = base if not os.path.exists(base) else snapshot_path(
        suffix="-" + dt.datetime.now().strftime("%H%M"))
    print(write_snapshot(path))


def real_uuid(r):
    u = (r.get("uuid") or "").strip()
    return u if u and u != "-" else None


def reconcile(base, now):
    """Return (closed, opened) reconciling two snapshots.

    Two traps, both hit in real data on 2026-08-04:
      1. `mc` emits uuid='-' for sessions it cannot resolve yet. Keying on uuid
         alone collapses every such row into one bucket.
      2. A session's uuid can *resolve between snapshots* ('-' then real). Any
         key that mixes the two makes one session look closed AND opened.

    So: match on uuid where both sides have one, then fall back to title for
    whatever is left over.
    """
    b_by_uuid = {}
    for r in now:
        u = real_uuid(r)
        if u:
            b_by_uuid[u] = r

    closed, matched_now = [], set()
    leftover_base = []
    for r in base:
        u = real_uuid(r)
        if u and u in b_by_uuid:
            matched_now.add(id(b_by_uuid[u]))
        else:
            leftover_base.append(r)

    # second pass: title match against still-unmatched current sessions
    remaining = [r for r in now if id(r) not in matched_now]
    by_title = {}
    for r in remaining:
        by_title.setdefault(r.get("title", ""), []).append(r)
    for r in leftover_base:
        bucket = by_title.get(r.get("title", ""))
        if bucket:
            matched_now.add(id(bucket.pop()))
        else:
            closed.append(r)

    opened = [r for r in now if id(r) not in matched_now]
    return closed, opened


def cmd_daydiff(args):
    base = load_snapshot(snapshot_path())
    if base is None:
        sys.exit(f"balls.py: no morning snapshot at {snapshot_path()} — run `balls.py snapshot` at day start")
    now = sweep()
    a, b = base, now
    closed, opened = reconcile(base, now)
    balls = load_balls()

    def ball_of(r):
        t = (r.get("title") or "").lower()
        for x in balls:
            if any(k in t for k in x["keywords"]):
                return f"#{x['id']}"
        return "—"

    print(f"DAY DIFF {today()}   {len(a)} → {len(b)}   closed={len(closed)} opened={len(opened)}\n")
    print("CLOSED:")
    for r in sorted(closed, key=lambda r: r.get("domain", "")):
        print(f"  {ball_of(r):>3} {r.get('domain',''):<9} {r.get('title','')[:60]}")
    print("\nOPENED:")
    for r in sorted(opened, key=lambda r: r.get("domain", "")):
        print(f"  {ball_of(r):>3} {r.get('domain',''):<9} {r.get('title','')[:60]}")
    h = read_highlight()
    print()
    if h and h.get("date") == today():
        print(f"HIGHLIGHT: {h['text']}")
        print(f"  started: {'YES' if h.get('started') else 'NO  <-- record why in the evening log'}")
    else:
        print("HIGHLIGHT: none was set today.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list"); p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--domain", choices=["work", "personal"], help="show only one ladder")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("suggest"); p.set_defaults(fn=cmd_suggest)
    p = sub.add_parser("set"); p.add_argument("text", nargs="+"); p.add_argument("--ball", type=int); p.set_defaults(fn=cmd_set)
    p = sub.add_parser("get"); p.add_argument("--quiet-if-started", action="store_true"); p.set_defaults(fn=cmd_get)
    p = sub.add_parser("started"); p.set_defaults(fn=cmd_started)
    p = sub.add_parser("snapshot"); p.set_defaults(fn=cmd_snapshot)
    p = sub.add_parser("daydiff"); p.set_defaults(fn=cmd_daydiff)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
