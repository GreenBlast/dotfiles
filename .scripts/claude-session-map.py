#!/usr/bin/env python3
"""
Capture a deterministic map of live tmux panes -> Claude Code sessions.

Run this BEFORE a reboot. It writes:
  ~/.claude-restore.tsv        machine-readable: addr<TAB>cwd<TAB>resume_target<TAB>method<TAB>title
  (stdout)                     human-readable summary

Resolution strategy, per pane (ground truth, validated against disk):
  1. the pane's live `claude` argv has `--resume <uuid>` AND that <uuid>.jsonl
     still exists on disk                                     -> use <uuid>
     (a non-UUID slug, or a UUID whose file is gone because the session forked
      on resume / was compacted, is NOT trusted — fall through.)
  2. else match the live pane title (== the running session's ai-title /
     custom-title) to a session in ~/.claude/projects/<encoded-cwd>/*.jsonl,
     newest wins; also try a slug launch-arg as a title  -> use that UUID
  3. else UNRESOLVED (manual pick from `claude --resume` picker)

After reboot, tmux-resurrect restores the layout/cwds; feed this map to
claude-rehydrate.sh to re-launch each session in its pane.
"""
import json, os, re, subprocess, sys
from datetime import datetime
from glob import glob

HOME = os.path.expanduser("~")
PROJ = os.path.join(HOME, ".claude", "projects")
TSV = os.path.join(HOME, ".claude-restore.tsv")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

# 1) tmux panes ------------------------------------------------------------
panes = []
fmt = "#{pane_pid}\t#{session_name}:#{window_index}.#{pane_index}\t#{pane_current_path}\t#{pane_title}"
for line in sh(f"tmux list-panes -a -F '{fmt}'").splitlines():
    parts = line.split("\t")
    if len(parts) != 4:
        continue
    pane_pid, addr, cwd, title = parts
    panes.append({"pane_pid": int(pane_pid), "addr": addr, "cwd": cwd, "title": title})

# 2) process tree ----------------------------------------------------------
pid_ppid, pid_cmd = {}, {}
for line in sh("ps -axo pid=,ppid=,command=").splitlines():
    m = re.match(r"\s*(\d+)\s+(\d+)\s+(.*)", line)
    if not m:
        continue
    pid, ppid, cmd = int(m.group(1)), int(m.group(2)), m.group(3)
    pid_ppid[pid] = ppid
    pid_cmd[pid] = cmd

children = {}
for pid, ppid in pid_ppid.items():
    children.setdefault(ppid, []).append(pid)

def descendants(root):
    out, stack = [], list(children.get(root, []))
    while stack:
        p = stack.pop()
        out.append(p)
        stack.extend(children.get(p, []))
    return out

def is_interactive_claude(cmd):
    base = cmd.strip()
    if "daemon run" in base or "--bg-pty-host" in base or "--bg-spare" in base:
        return False
    return bool(re.match(r"(/\S*/)?claude(\s|$)", base)) and "versions/" not in base

def resume_arg(cmd):
    m = re.search(r"\s(?:--resume|-r)\s+(\S+)", cmd)
    return m.group(1) if m else None

for p in panes:
    p["claude_cmd"] = None
    p["resume_name"] = None
    for d in descendants(p["pane_pid"]):
        c = pid_cmd.get(d, "")
        if is_interactive_claude(c):
            p["claude_cmd"] = c
            p["resume_name"] = resume_arg(c)
            break

# 3) title -> sessionId index per project dir ------------------------------
def encode_cwd(cwd):
    return re.sub(r"[/.]", "-", cwd)

def session_exists(sid, cwd=None):
    # prefer the cwd's own project dir, but accept the session living anywhere
    if cwd and os.path.isfile(os.path.join(PROJ, encode_cwd(cwd), sid + ".jsonl")):
        return True
    return bool(glob(os.path.join(PROJ, "*", sid + ".jsonl")))

def title_map_for(cwd):
    d = os.path.join(PROJ, encode_cwd(cwd))
    res = {}
    if not os.path.isdir(d):
        return res
    for f in glob(os.path.join(d, "*.jsonl")):
        sid = os.path.basename(f)[:-6]
        mtime = os.path.getmtime(f)
        last_ai = last_custom = None
        try:
            with open(f, "rb") as fh:
                for raw in fh:
                    if b'"ai-title"' in raw or b'"custom-title"' in raw:
                        try:
                            o = json.loads(raw)
                        except Exception:
                            continue
                        if o.get("type") == "ai-title" and o.get("aiTitle"):
                            last_ai = o["aiTitle"]
                        elif o.get("type") == "custom-title" and o.get("customTitle"):
                            last_custom = o["customTitle"]
        except Exception:
            continue
        # Index only the session's CURRENT displayed title (a user custom-title
        # overrides the ai-title), so a session formerly named X never shadows
        # the one actually named X now.
        t = last_custom or last_ai
        if t:
            prev = res.get(t)
            if prev is None or mtime > prev[1]:
                res[t] = (sid, mtime)
    return res

tmaps = {}
for p in panes:
    if p["claude_cmd"] and p["cwd"] not in tmaps:
        tmaps[p["cwd"]] = title_map_for(p["cwd"])

def clean_title(t):
    return re.sub(r"^[^\w֐-׿]+", "", t).strip()

# 4) resolve + emit --------------------------------------------------------
def wkey(addr):
    m = re.match(r"(.*):(\d+)\.(\d+)", addr)
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else (addr, 0, 0)

rows = []
for p in panes:
    if not p["claude_cmd"]:
        continue
    title = clean_title(p["title"])
    tmap = tmaps.get(p["cwd"], {})
    rn = p["resume_name"]
    target, method = "", "UNRESOLVED"
    # 1) Trust the launch arg ONLY when it's a real UUID still present on disk.
    if rn and UUID_RE.match(rn) and session_exists(rn, p["cwd"]):
        target, method = rn, "argv-uuid"
    else:
        # 2) Live pane title == the running session's ai-title — ground truth
        #    for what is actually open in this pane. Resolve a slug arg too.
        hit = tmap.get(title)
        if not hit and rn and not UUID_RE.match(rn):
            hit = tmap.get(rn)
        if hit:
            target, method = hit[0], "title-match"
    rows.append((p["addr"], p["cwd"], title, target, method))

rows.sort(key=lambda r: wkey(r[0]))

QUIET = "--quiet" in sys.argv or not sys.stdout.isatty()
ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
matched = sum(1 for r in rows if r[4] != "UNRESOLVED")

# Empty-guard: if tmux isn't running or has no claude panes (e.g. a periodic
# timer fires at boot before tmux starts), do NOT overwrite the existing map —
# a stale map beats an empty one.
if not rows:
    print(f"{ts}  no live claude panes found — existing map kept, not overwritten")
    sys.exit(0)

# "PICK" sentinel for unresolved: never write an empty field, else bash
# `read` with tab-IFS coalesces the gap and shifts columns.
content = "".join(
    f"{addr}\t{cwd}\t{target or 'PICK'}\t{method}\t{title}\n"
    for addr, cwd, title, target, method in rows
)
# Atomic write so a killed run never leaves a half-written map.
tmp = TSV + ".tmp"
with open(tmp, "w") as fh:
    fh.write(content)
os.replace(tmp, TSV)

# Bounded, de-duplicated history. The zero-guard above stops an *empty* capture
# from clobbering a good map, but not a *partial* one (e.g. after a reboot you
# open one session before running rehydrate). Keeping the last N distinct maps
# means the full pre-reboot map is always recoverable from the history dir.
try:
    hist = os.path.join(HOME, ".claude-restore-history")
    os.makedirs(hist, exist_ok=True)
    past = sorted(glob(os.path.join(hist, "*.tsv")))
    last = open(past[-1]).read() if past else None
    if content != last:
        stamp = ts.replace(":", "").replace(" ", "-")
        with open(os.path.join(hist, stamp + ".tsv"), "w") as fh:
            fh.write(content)
        for old in sorted(glob(os.path.join(hist, "*.tsv")))[:-250]:
            os.remove(old)
except Exception:
    pass

if QUIET:
    print(f"{ts}  {len(rows)} panes, {matched} resolved, "
          f"{len(rows)-matched} unresolved -> {TSV}")
    sys.exit(0)

print(f"# {len(rows)} live claude panes — {matched} resolved, {len(rows)-matched} unresolved")
print(f"# written: {TSV}\n")
cur = None
for addr, cwd, title, target, method in rows:
    if cwd != cur:
        print(f"\n## {cwd}")
        cur = cwd
    cmd = f"claude --resume {target}" if target else "claude --resume   # pick from picker"
    flag = "" if method != "UNRESOLVED" else "   <-- UNRESOLVED"
    print(f"  [{addr}] {title}{flag}")
    print(f"        {cmd}   ({method})")
