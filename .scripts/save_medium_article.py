#!/Users/user/.scripts/.venvs/medium-saver/bin/python
"""
Save a Medium article (or any readable web article) into the Obsidian vault.

Usage:
  save_medium_article.py                       # newest *.html in ~/Downloads
  save_medium_article.py path/to/file.html
  save_medium_article.py --url https://...     # fetch directly (e.g. freedium mirror)
"""

import argparse
import datetime as dt
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

import trafilatura
from readability import Document
from lxml import html as lxml_html

# ─────────────────────────── CONFIG ───────────────────────────
# Tweak these to match your vault layout and preferences.

# Mirror used to bypass paywalls. Script appends the original article URL to
# this base. Swap to any other readability mirror if you prefer.
# Examples: "https://freedium.cfd/", "https://scribe.rip/"
MIRROR_BASE = "https://freedium-mirror.cfd/"

# Vault location and naming.
VAULT = Path("/Users/user/Projects/ObsidianVaults/Aviad")
VAULT_NAME = "Aviad"  # Obsidian vault name as registered (for obsidian://open URIs)
ARTICLES_DIR = VAULT / "Main" / "Knowledge" / "ArticlesSummaries"

# MOC (Map of Contents) link insertion. New article links are placed just above
# the line that exactly matches MOC_ANCHOR.
MOC_PATH = ARTICLES_DIR / "Articles Summaries MOC.md"
MOC_ANCHOR = "## YouTube videos"

# Source folder for the no-arg case (newest HTML wins).
DOWNLOADS = Path.home() / "Downloads"

# Paywall detection: HTML markers that trigger an automatic mirror reroute.
PAYWALL_MARKERS = (
    '"isAccessibleForFree":false',
    'Member-only story',
    'member-only-tag',
)
# Length safety net: if extracted body is shorter than this, retry via mirror.
MIN_BODY_CHARS = 500

# ────────────────────────── /CONFIG ───────────────────────────

ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|#^\[\]]')
APOSTROPHE_CHARS = re.compile(r"[’'`]")
DASH_CHARS = re.compile(r"[—–]")
WHITESPACE_RUN = re.compile(r"\s+")


def sanitize_title_for_filename(title: str) -> str:
    t = DASH_CHARS.sub("-", title)
    t = APOSTROPHE_CHARS.sub("", t)
    t = ILLEGAL_FILENAME_CHARS.sub("", t)
    t = t.replace(",", "").replace(".", "")
    t = WHITESPACE_RUN.sub(" ", t).strip()
    return t


def polish_body(md: str) -> str:
    md = re.sub(r"<[^>]+>", "", md)  # strip raw HTML tags
    md = re.sub(r":::.*?}|\[\[·\].*?\]\{.*?\}|\{.*?\}|\[\]\[\]\[\]|:::", "", md)
    # Drop Medium image accessibility placeholder lines
    md = re.sub(r"^\s*\[Press enter or click to view image in full size\]\s*$\n?", "", md, flags=re.MULTILINE)
    # Drop standalone colon-only lines (pandoc artifact)
    md = re.sub(r"^\s*:+\s*$\n?", "", md, flags=re.MULTILINE)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    return md.strip()


def trim_body_head(body: str, title: str, subtitle: str | None) -> str:
    """Drop the article header block (title H1, byline, image caption) so the
    body starts at the first paragraph of prose. Anchors on the subtitle line
    when available, otherwise the title line.
    """
    lines = body.split("\n")

    def find_anchor(needle: str) -> int | None:
        n = needle.strip()
        if not n:
            return None
        for i, line in enumerate(lines):
            if n in line:
                return i
        return None

    anchor = find_anchor(subtitle) if subtitle else None
    if anchor is None:
        anchor = find_anchor(title)
    if anchor is None:
        return body

    rest = lines[anchor + 1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    return "\n".join(rest)


def looks_paywalled(html: str) -> bool:
    return any(marker in html for marker in PAYWALL_MARKERS)


def via_mirror(url: str) -> str:
    return MIRROR_BASE + url


def strip_mirror_prefix(url: str) -> str:
    if url.startswith(MIRROR_BASE):
        return url[len(MIRROR_BASE):]
    return url


GENERIC_MIRROR_TITLES = {"freedium", "untitled article", "untitled", ""}


def find_article_title_in_body(body: str, subtitle: str | None) -> str | None:
    """Return the H1 closest above the subtitle line, otherwise the first H1.
    Falls back to None if no H1 exists.
    """
    lines = body.split("\n")
    h1_indexes = [i for i, l in enumerate(lines) if l.startswith("# ") and l[2:].strip()]
    if not h1_indexes:
        return None

    subtitle_idx = None
    if subtitle:
        needle = subtitle.strip()
        for i, line in enumerate(lines):
            if needle and needle in line:
                subtitle_idx = i
                break

    if subtitle_idx is not None:
        above = [i for i in h1_indexes if i < subtitle_idx]
        chosen = above[-1] if above else h1_indexes[0]
    else:
        chosen = h1_indexes[0]
    return lines[chosen][2:].strip()


def normalize_heading_levels(body: str) -> str:
    """If the body has no H2s but multiple H3+, shift every heading up one
    level. Compensates for mirrors/pandoc that wrap the article in an extra
    section level.
    """
    h2_count = len(re.findall(r"(?m)^##\s", body))
    h3_count = len(re.findall(r"(?m)^###\s", body))
    if h2_count == 0 and h3_count >= 2:
        body = re.sub(r"(?m)^(#{2,})(\s)", lambda m: m.group(1)[1:] + m.group(2), body)
    return body


def fetch_url(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        sys.exit(f"Failed to fetch URL: {url}")
    return downloaded


def load_html(args) -> tuple[str, str | None]:
    """Returns (html_or_url_content, source_url_or_none).
    The source URL we hand on never includes the mirror prefix.
    """
    if args.url:
        if args.url.startswith(MIRROR_BASE):
            return fetch_url(args.url), strip_mirror_prefix(args.url)
        html = fetch_url(args.url)
        if looks_paywalled(html):
            mirror_url = via_mirror(args.url)
            print(f"Paywall detected — refetching via mirror: {mirror_url}", file=sys.stderr)
            html = fetch_url(mirror_url)
        return html, args.url

    if args.file:
        path = Path(args.file).expanduser()
    else:
        candidates = sorted(DOWNLOADS.glob("*.html"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            sys.exit(f"No *.html files found in {DOWNLOADS}")
        path = candidates[-1]
        print(f"Using newest HTML in Downloads: {path.name}")

    if not path.is_file():
        sys.exit(f"File not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace"), None


def html_to_markdown(article_html: str) -> str:
    result = subprocess.run(
        ["pandoc", "-f", "html", "-t", "markdown-raw_html+backtick_code_blocks", "--wrap", "none"],
        input=article_html,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def strip_figures(article_html: str) -> str:
    """Remove <figure>, <img>, and <picture> from the readability HTML so image
    captions don't leak into the markdown body."""
    try:
        tree = lxml_html.fragment_fromstring(article_html, create_parent="div")
    except Exception:
        return article_html
    for tag in ("figure", "img", "picture", "svg"):
        for el in tree.iter(tag):
            el.getparent().remove(el)
    return lxml_html.tostring(tree, encoding="unicode")


def extract(html: str, fallback_url: str | None):
    doc = Document(html)
    article_html = doc.summary(html_partial=True)
    if not article_html:
        sys.exit("readability could not extract article content")

    article_html = strip_figures(article_html)
    body_md = html_to_markdown(article_html)

    meta = trafilatura.extract_metadata(html)
    meta_title = meta.title if meta and meta.title else None
    sitename = meta.sitename if meta and meta.sitename else None

    # On freedium the og:title is "Freedium" but the article title leaks into
    # og:site_name as "Real Title | by Author". Prefer that when og:title is
    # the generic mirror name.
    if (not meta_title or meta_title.strip().lower() in GENERIC_MIRROR_TITLES) and sitename:
        candidate = re.split(r"\s+\|\s+by\s+", sitename, maxsplit=1)[0].strip()
        if candidate and candidate.lower() not in GENERIC_MIRROR_TITLES:
            meta_title = candidate

    title = meta_title or doc.short_title() or "Untitled Article"
    url = (meta.url if meta else None) or fallback_url
    description = meta.description if meta else None  # subtitle, when present

    return title, url, description, body_md.strip()


def build_note(title: str, url: str | None, subtitle: str | None, body: str) -> str:
    now = dt.datetime.now().astimezone()
    stamp = now.strftime("%Y-%m-%d %H:%M:%S%z")
    stamp = stamp[:-2] + ":" + stamp[-2:]  # +0300 -> +03:00

    lines = [
        "---",
        f"title: {title}",
        "aliases:",
        "tags:",
        "  - claude-created",
        f"created: {stamp}",
        f"updated: {stamp}",
        "---",
        "",
    ]
    if url:
        lines += [url, ""]
    lines += [f"# {title}", ""]
    if subtitle:
        lines += [f"## {subtitle}", ""]
    lines += [body, ""]
    return "\n".join(lines)


def insert_into_moc(filename_stem: str) -> None:
    text = MOC_PATH.read_text(encoding="utf-8")
    lines = text.split("\n")

    anchor_idx = next((i for i, l in enumerate(lines) if l.strip() == MOC_ANCHOR), None)
    if anchor_idx is None:
        sys.exit(f"Could not find {MOC_ANCHOR!r} anchor in the MOC")

    insert_at = anchor_idx
    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1

    link = f"[[{filename_stem}]]"
    if link in text:
        print(f"MOC already contains {link}, skipping insert")
        return

    lines.insert(insert_at, link)
    MOC_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Inserted {link} into MOC")


def open_in_obsidian(filename_stem: str) -> None:
    rel = f"Main/Knowledge/ArticlesSummaries/{filename_stem}.md"
    uri = f"obsidian://open?vault={urllib.parse.quote(VAULT_NAME)}&file={urllib.parse.quote(rel)}"
    subprocess.run(["open", uri], check=False)


def main():
    parser = argparse.ArgumentParser(description="Save a Medium article into the Obsidian vault.")
    parser.add_argument("file", nargs="?", help="HTML file path (defaults to newest in ~/Downloads)")
    parser.add_argument("--url", help="Fetch from a URL instead of a saved file (e.g. freedium mirror)")
    args = parser.parse_args()

    html, fallback_url = load_html(args)
    title, url, subtitle, body = extract(html, fallback_url)

    # Length safety net: if URL fetch returned a suspiciously short body and we
    # haven't already gone through the mirror, retry there.
    if (
        args.url
        and not args.url.startswith(MIRROR_BASE)
        and len(body) < MIN_BODY_CHARS
    ):
        mirror_url = via_mirror(args.url)
        print(
            f"Body suspiciously short ({len(body)} chars) — retrying via mirror: {mirror_url}",
            file=sys.stderr,
        )
        html = fetch_url(mirror_url)
        title, url, subtitle, body = extract(html, args.url)

    body = polish_body(body)

    # If page metadata gave us a generic mirror title, recover the real title
    # from the body's H1 (preferring the H1 that sits just above the subtitle).
    if title.strip().lower() in GENERIC_MIRROR_TITLES:
        recovered = find_article_title_in_body(body, subtitle)
        if recovered:
            title = recovered

    body = trim_body_head(body, title, subtitle)
    body = normalize_heading_levels(body)

    filename_stem = sanitize_title_for_filename(title)
    if not filename_stem:
        sys.exit("Title sanitized to empty string; aborting")

    out_path = ARTICLES_DIR / f"{filename_stem}.md"
    if out_path.exists():
        sys.exit(f"Note already exists: {out_path}")

    note = build_note(title, url, subtitle, body)
    out_path.write_text(note, encoding="utf-8")
    print(f"Wrote {out_path}")

    insert_into_moc(filename_stem)
    open_in_obsidian(filename_stem)


if __name__ == "__main__":
    main()
