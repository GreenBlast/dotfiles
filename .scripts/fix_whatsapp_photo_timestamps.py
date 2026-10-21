#!/usr/bin/env python3
"""
Fix EXIF/file timestamps on media downloaded from WhatsApp.

WhatsApp strips EXIF metadata from photos it compresses before sending, so
anything you download keeps only a filesystem mtime (usually the download/
sync time, which can be minutes, days, or months after the real moment) even
though the filename itself encodes the real capture/send time
("WhatsApp Image 2023-08-01 at 21.51.03.jpeg").

This script only touches files whose name matches that exact WhatsApp shape.
For each match it compares any existing EXIF date against the filename date:

  - no EXIF date at all         -> safe to write (this is the common case)
  - EXIF date matches filename  -> already correct, left alone
  - EXIF date conflicts         -> NOT auto-fixed (could be a forwarded photo
                                    where the real capture EXIF is correct and
                                    the filename reflects the forward/download
                                    date instead) - reported for manual review

Dry-run by default. Nothing is written until you pass --apply.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Jerusalem")

MEDIA_EXTS = {
    "image": {".jpg", ".jpeg", ".png", ".webp"},
    "video": {".mp4", ".mov", ".3gp", ".m4v"},
}
ALL_EXTS = MEDIA_EXTS["image"] | MEDIA_EXTS["video"]

# "WhatsApp Image 2023-08-01 at 21.51.03.jpeg" / "... (1).jpeg" / "WhatsApp Video ..."
NAMED_RE = re.compile(
    r"^WhatsApp (Image|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{2})\.(\d{2})\.(\d{2})"
    r"(?: \(\d+\))?\.(\w+)$"
)

# Legacy Android export: IMG-20230801-WA0007.jpg / VID-20230801-WA0003.mp4
LEGACY_RE = re.compile(r"^(IMG|VID)-(\d{4})(\d{2})(\d{2})-WA\d+\.(\w+)$")

EXIF_DATE_FMT = "%Y:%m:%d %H:%M:%S"
DATE_TAGS = ["DateTimeOriginal", "CreateDate"]  # what we read to detect conflicts


@dataclass
class Match:
    path: Path
    kind: str  # "image" | "video"
    dt: datetime  # naive local wall-clock parsed from filename
    time_confidence: str  # "exact" | "date-only"


def parse_filename(path: Path):
    name = path.name
    ext = path.suffix.lower()
    if ext not in ALL_EXTS:
        return None

    m = NAMED_RE.match(name)
    if m:
        kind_word, y, mo, d, h, mi, s, _ext = m.groups()
        dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s))
        kind = "image" if kind_word == "Image" else "video"
        return Match(path, kind, dt, "exact")

    m = LEGACY_RE.match(name)
    if m:
        prefix, y, mo, d, _ext = m.groups()
        dt = datetime(int(y), int(mo), int(d), 0, 0, 0)
        kind = "image" if prefix == "IMG" else "video"
        return Match(path, kind, dt, "date-only")

    return None


def read_existing_dates(path: Path):
    """Return dict of tag -> parsed datetime for whichever DATE_TAGS exist."""
    try:
        out = subprocess.run(
            # QuickTimeUTC: MP4/MOV dates are stored as UTC; read them back as local wall-clock
            ["exiftool", "-j", "-api", "QuickTimeUTC", "-time:all", str(path)],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(out.stdout)[0]
    except Exception as e:
        return {"_error": str(e)}

    found = {}
    for tag in DATE_TAGS:
        raw = data.get(tag)
        if not raw:
            continue
        raw = raw.split("+")[0].split("-0")[0].strip()  # strip trailing offset if present
        try:
            found[tag] = datetime.strptime(raw[:19], EXIF_DATE_FMT)
        except ValueError:
            continue
    return found


def classify(match: Match, tolerance: timedelta):
    existing = read_existing_dates(match.path)
    if "_error" in existing:
        return "ERROR", existing["_error"], existing

    if not existing:
        return "FIX", "no EXIF date present", existing

    # Compare against whichever tag exists (prefer DateTimeOriginal)
    tag = "DateTimeOriginal" if "DateTimeOriginal" in existing else next(iter(existing))
    diff = abs((existing[tag] - match.dt).total_seconds())
    if diff <= tolerance.total_seconds():
        return "OK", f"{tag} already matches filename (within {int(tolerance.total_seconds()//60)}m)", existing
    return "CONFLICT", f"{tag}={existing[tag]} differs from filename={match.dt} by {diff/60:.1f}m", existing


def build_write_args(match: Match, set_offset: bool):
    exif_str = match.dt.strftime(EXIF_DATE_FMT)
    offset = match.dt.replace(tzinfo=LOCAL_TZ).strftime("%z")
    offset = f"{offset[:3]}:{offset[3:]}"
    if match.kind == "video":
        # QuickTime dates are UTC by spec (Google Photos / Immich read them that way).
        # Writing the local wall-clock raw shifts the video +3h, so convert explicitly.
        local = f"{exif_str}{offset}"
        args = ["-api", "QuickTimeUTC", f"-AllDates={local}",
                f"-MediaCreateDate={local}", f"-MediaModifyDate={local}",
                f"-TrackCreateDate={local}", f"-TrackModifyDate={local}"]
    else:
        args = [f"-AllDates={exif_str}"]
    if set_offset and match.kind == "image":
        args += [
            f"-OffsetTimeOriginal={offset}",
            f"-OffsetTimeDigitized={offset}",
            f"-OffsetTime={offset}",
        ]
    # Also correct the filesystem timestamps (currently = download/sync time)
    args += [
        f"-FileModifyDate={exif_str}",
        f"-FileCreateDate={exif_str}",
    ]
    return args


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("directory", type=Path, help="Directory to scan")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    ap.add_argument("--apply", action="store_true", help="Actually write changes (default: dry-run only)")
    ap.add_argument("--tolerance-min", type=float, default=5,
                     help="Minutes of slack when comparing existing EXIF vs filename (default: 5)")
    ap.add_argument("--allow-conflicts", action="store_true",
                     help="Also overwrite files where existing EXIF disagrees with the filename "
                          "(dangerous: EXIF may be the correct original capture date; use only "
                          "after reviewing the CONFLICT list)")
    ap.add_argument("--keep-backups", dest="keep_backups", action="store_true", default=True,
                     help="Keep exiftool's *_original backup files (default: on)")
    ap.add_argument("--no-backups", dest="keep_backups", action="store_false",
                     help="Pass -overwrite_original to exiftool (no backup files)")
    ap.add_argument("--no-offset", dest="set_offset", action="store_false", default=True,
                     help="Skip writing OffsetTimeOriginal/OffsetTime (Asia/Jerusalem DST-aware, on by default)")
    args = ap.parse_args()

    if not args.directory.is_dir():
        print(f"Not a directory: {args.directory}", file=sys.stderr)
        sys.exit(1)

    tolerance = timedelta(minutes=args.tolerance_min)
    files = args.directory.rglob("*") if args.recursive else args.directory.glob("*")
    matches = [m for m in (parse_filename(p) for p in sorted(files) if p.is_file()) if m]

    if not matches:
        print("No files matching the WhatsApp filename shape were found.")
        return

    counts = {"FIX": 0, "OK": 0, "CONFLICT": 0, "ERROR": 0}
    conflicts = []
    to_write = []

    for m in matches:
        verdict, reason, existing = classify(m, tolerance)
        counts[verdict] += 1
        tag = "" if m.time_confidence == "exact" else "  [date-only filename, time defaulted to 00:00:00]"
        print(f"[{verdict:8}] {m.path.name}{tag}\n            -> {reason}")
        if verdict == "CONFLICT":
            conflicts.append(m)
        if verdict == "FIX" or (verdict == "CONFLICT" and args.allow_conflicts):
            to_write.append(m)

    print()
    print(f"Summary: {counts['FIX']} fixable, {counts['OK']} already correct, "
          f"{counts['CONFLICT']} conflicting, {counts['ERROR']} errors "
          f"(of {len(matches)} matched files)")

    if conflicts and not args.allow_conflicts:
        print(f"\n{len(conflicts)} file(s) have an existing EXIF date that disagrees with the "
              f"filename and were left untouched. Review them manually, or re-run with "
              f"--allow-conflicts if you're sure the filename date is the correct one.")

    if not args.apply:
        print("\nDry run only - no files were changed. Re-run with --apply to write changes.")
        return

    if not to_write:
        print("\nNothing to write.")
        return

    print(f"\nApplying changes to {len(to_write)} file(s)...")
    for m in to_write:
        write_args = build_write_args(m, args.set_offset)
        cmd = ["exiftool"] + write_args
        if not args.keep_backups:
            cmd.append("-overwrite_original")
        cmd.append(str(m.path))
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"  [{status}] {m.path.name}")
        if result.returncode != 0:
            print(f"    {result.stderr.strip()}")


if __name__ == "__main__":
    main()
