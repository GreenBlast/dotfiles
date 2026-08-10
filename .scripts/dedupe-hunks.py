#!/usr/bin/env python3
"""Collapse byte-identical hunks in a unified diff. No model, no network.

A hunk's signature is its sequence of +/- lines (context ignored). Within a file,
the first hunk of each signature is printed in full; later duplicates collapse to
a single counted line. Secrets in changed lines are masked by default.

    ./dedupe-hunks.py < some.diff
    git diff | ./dedupe-hunks.py --no-redact
"""
import re
import sys

SECRET = re.compile(
    r'\b(token|apikey|api_key|password|passwd|secret|private_key)\b(\s*[:=]\s*)(\S+)',
    re.IGNORECASE,
)


def redact(line):
    return SECRET.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", line)


def main():
    do_redact = "--no-redact" not in sys.argv
    lines = sys.stdin.read().splitlines()

    out, seen = [], {}
    file_hdr, hunk, in_hunk = [], [], False

    def flush():
        """Emit the buffered hunk, or a one-line note if we've seen its shape."""
        if not hunk:
            return
        sig = "\n".join(l for l in hunk if l[:1] in "+-" and l[:3] not in ("+++", "---"))
        if not sig:                      # context-only hunk: always keep
            out.extend(hunk)
            return
        key = (tuple(file_hdr), sig)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 1:
            out.extend(hunk)
        else:
            out.append(f"@@ ... identical to the hunk above (occurrence {seen[key]}) @@")

    for line in lines:
        if line.startswith("diff --git"):
            flush()
            hunk, in_hunk = [], False
            file_hdr = [line]
            out.append(line)
        elif not in_hunk and line.startswith(("--- ", "+++ ", "index ", "new file", "deleted file", "similarity ", "rename ")):
            file_hdr.append(line)
            out.append(line)
        elif line.startswith("@@"):
            flush()
            hunk, in_hunk = [line], True
        elif in_hunk:
            # Redact every line inside a hunk, not just changed ones — a secret is just
            # as exposed sitting in the context around someone else's edit.
            hunk.append(redact(line) if do_redact else line)
        else:
            out.append(line)
    flush()

    # Replace runs of collapse-notes with one summary line.
    final, i = [], 0
    note = re.compile(r"^@@ \.\.\. identical to the hunk above \(occurrence (\d+)\) @@$")
    while i < len(final_src := out):
        m = note.match(final_src[i])
        if not m:
            final.append(final_src[i]); i += 1; continue
        j = i
        while j < len(final_src) and note.match(final_src[j]):
            j += 1
        final.append(f"@@ ... {j - i} further identical hunk(s) omitted @@")
        i = j

    print("\n".join(final))


if __name__ == "__main__":
    main()
