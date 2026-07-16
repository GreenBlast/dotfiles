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
import time
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

# Transient fetch retry (trafilatura.fetch_url returns None on any failure).
FETCH_ATTEMPTS = 3
FETCH_BACKOFF_SECONDS = 1.5

# The freedium mirror is noticeably flakier than the origin: it intermittently
# returns nothing, or a tiny placeholder page that extracts to an empty body.
# Give it more tries, and judge success by the extracted body, not just a 200.
MIRROR_ATTEMPTS = 5

# A real article header lives in the first handful of lines. We only look for
# the title/subtitle header anchor within this many leading lines so a subtitle
# phrase that recurs deep in the prose can't be mistaken for the header.
HEADER_SEARCH_LINES = 40

# Completeness gate. readability silently returns only its single highest-scoring
# container, which on a long Medium post can be half the article (see
# extract_article_html). Nothing used to check the output against the input, so a
# note could be written that dropped 12 of 26 sections and still report success.
# We now compare the extracted body against the headings actually present in the
# page's article container and refuse to write if too many went missing.
MAX_MISSING_HEADINGS_RATIO = 0.15
# Below this many source headings there isn't enough signal to judge; skip the gate.
MIN_HEADINGS_FOR_GATE = 4

# ────────────────────────── /CONFIG ───────────────────────────

ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|#^\[\]()]')
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


FENCE_SPLIT = re.compile(r"(?s)(```.*?```)")

# Strip a stray raw HTML tag, but ONLY a real one: `</?tagname ...>` on a single
# line. The obvious `<[^>]+>` is a trap — `[^>]` matches newlines, so a lone `<`
# in the prose or in a code sample (`SET key <value>`) swallows everything up to
# the next `>` anywhere later in the document, headings and all. That silently ate
# 14k chars and 19 sections out of a Redis article full of `<placeholder>` syntax.
STRAY_TAG = re.compile(r"</?[a-zA-Z][^>\n]*>")


def split_code_fences(md: str):
    """Yield (is_code, segment) pairs so callers can transform prose without
    disturbing fenced code (headings/comments inside code must stay verbatim).
    """
    for part in FENCE_SPLIT.split(md):
        if part.startswith("```") and part.endswith("```"):
            yield True, part
        elif part:
            yield False, part


def dedupe_consecutive_code_blocks(md: str) -> str:
    """freedium renders every code block twice — once for the light theme and
    once for the dark theme (`dark:hidden` / `dark:block`). Once styling
    attributes are stripped these collapse into two identical fenced blocks
    separated only by blank lines; keep just the first of each such pair.
    """
    result: list[str] = []
    last_code = None          # normalized text of the previous emitted code block
    pending: list[str] = []   # buffered (whitespace-only) text since that block
    for is_code, part in split_code_fences(md):
        if is_code:
            if part.strip() == last_code and all(not p.strip() for p in pending):
                pending = []  # drop the duplicate and the blank separator
                continue
            result.extend(pending)
            pending = []
            result.append(part)
            last_code = part.strip()
        else:
            pending.append(part)
            if part.strip():  # real prose breaks the light/dark adjacency
                last_code = None
                result.extend(pending)
                pending = []
    result.extend(pending)
    return "".join(result)


# Tailwind/div boilerplate that pandoc emits from freedium's code-block wrappers
# (`<div class="relative">`, empty copy `<button>`, `dark:hidden` spans). These
# survive even after attribute stripping in odd cases, so scrub them defensively.
ARTIFACT_LINE = re.compile(
    r"^\s*(?::: ?\S.*|\[\]\[\].*|\S*dark:(?:hidden|block)\S*\s*)$",
    flags=re.MULTILINE,
)


def polish_body(md: str) -> str:
    # Clean prose and code separately: the tag/brace/artifact scrubbing below
    # would otherwise mangle code (a dict literal `{...}`, an `a < b` comparison)
    # if applied inside fenced blocks.
    out = []
    for is_code, seg in split_code_fences(md):
        if is_code:
            # Normalize pandoc's fence info string (``` {tabindex="0"} -> ```,
            # ``` python -> ```python) so blocks render plainly in Obsidian and
            # duplicate light/dark copies compare equal for the deduper.
            seg = re.sub(r"^``` *\{[^}]*\}", "```", seg)
            seg = re.sub(r"^``` +(\w)", r"```\1", seg)
            seg = re.sub(r"^```text$", "```", seg, flags=re.MULTILINE)
            out.append(seg)
            continue
        seg = STRAY_TAG.sub("", seg)  # strip raw HTML tags (e.g. bare <div>)
        seg = re.sub(r":::.*?}|\[\[·\].*?\]\{.*?\}|\{.*?\}|\[\]\[\]\[\]|:::", "", seg)
        seg = ARTIFACT_LINE.sub("", seg)
        # Drop Medium image accessibility placeholder lines
        seg = re.sub(r"^\s*\[Press enter or click to view image in full size\]\s*$\n?", "", seg, flags=re.MULTILINE)
        # Drop standalone colon-only lines (pandoc artifact)
        seg = re.sub(r"^\s*:+\s*$\n?", "", seg, flags=re.MULTILINE)
        out.append(seg)
    # With the <div> wrappers gone, duplicate code blocks are now separated only
    # by blank lines, so the deduper can collapse them.
    md = dedupe_consecutive_code_blocks("".join(out))
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    return md.strip()


ELLIPSIS_TAIL = re.compile(r"(?:…|\.\.\.)\s*$")

# trafilatura tuning: favor_recall keeps borderline blocks (intros, short
# sections, the closing links list) that the default precision mode discards.
#
# include_links MUST stay True. With links off, trafilatura returns the anchor TEXT
# and drops the href — so a "Further reading" section degrades into a list of titles
# pointing nowhere, and every inline citation in the prose loses its source. The
# vault's whole point is keeping the real URL.
TRAFILATURA_OPTS = dict(
    include_formatting=True,
    include_links=True,
    include_images=False,
    include_tables=True,
    favor_recall=True,
)


def text_len(fragment_html: str) -> int:
    """Visible-text length of an HTML fragment (markup-insensitive, so it can
    compare two extractors that keep very different amounts of markup)."""
    if not fragment_html:
        return 0
    try:
        tree = lxml_html.fragment_fromstring(fragment_html, create_parent="div")
    except Exception:
        return len(fragment_html)
    return len(" ".join(tree.text_content().split()))


def extract_article_html(html: str) -> str | None:
    """Return the article body as HTML, preferring trafilatura over readability.

    readability scores DOM containers and returns only the single highest-scoring
    one. On a long Medium post whose body is split across nested divs it happily
    returns the densest child and silently discards everything above it — it kept
    13 of 26 sections on the Temporal article, dropping the entire first half.
    trafilatura keeps the whole body.

    readability is still a useful fallback (it handles some non-Medium layouts
    trafilatura declines to parse), so run both and keep whichever recovered more
    text. That way a regression in either one degrades instead of truncating.
    """
    traf = trafilatura.extract(html, output_format="html", **TRAFILATURA_OPTS)
    try:
        read = Document(html).summary(html_partial=True)
    except Exception:
        read = None

    traf_len, read_len = text_len(traf), text_len(read)
    if traf_len >= read_len:
        return traf or read
    # readability winning by a wide margin usually means trafilatura bailed out;
    # a narrow win is noise, so keep trafilatura unless readability is clearly richer.
    print(
        f"trafilatura extracted {traf_len} chars vs readability's {read_len} — using readability",
        file=sys.stderr,
    )
    return read


def heading_texts(node_html: str) -> list[str]:
    """Normalized h1-h3 texts from an HTML fragment."""
    try:
        tree = lxml_html.fragment_fromstring(node_html, create_parent="div")
    except Exception:
        return []
    return [normalize_heading(h.text_content()) for h in tree.xpath(".//h1|.//h2|.//h3")]


HEADING_NOISE = re.compile(r"[^\w\s]")


def normalize_heading(s: str) -> str:
    return " ".join(HEADING_NOISE.sub(" ", s.lower()).split())


def source_headings(html: str) -> list[str]:
    """Headings inside the page's main article container — the ground truth the
    completeness gate checks the extracted body against."""
    try:
        tree = lxml_html.fromstring(html)
    except Exception:
        return []
    for xpath in ("//article", "//main"):
        nodes = tree.xpath(xpath)
        if nodes:
            node = max(nodes, key=lambda n: len(n.text_content()))
            heads = [normalize_heading(h.text_content())
                     for h in node.xpath(".//h1|.//h2|.//h3")]
            return [h for h in heads if h]
    return []


def check_completeness(body: str, html: str, title: str, subtitle: str | None) -> None:
    """Mechanical gate: refuse to write a note that dropped chunks of its source.

    The extractor's claim to have parsed the article is an input, not the verdict.
    Compare what we produced against the headings the page actually has.
    """
    # The title and subtitle are headings on the page but live in the frontmatter
    # and the H1/H2 that build_note adds, not in `body`. Counting them as missing
    # would inflate the ratio and, on a short article, fail a perfectly good note.
    header = {normalize_heading(title)}
    if subtitle:
        header.add(normalize_heading(ELLIPSIS_TAIL.sub("", subtitle)))

    src = [h for h in source_headings(html)
           if not any(h.startswith(x) or x.startswith(h) for x in header if x)]
    if len(src) < MIN_HEADINGS_FOR_GATE:
        return  # not enough structure in the source to judge; nothing to assert
    haystack = normalize_heading(body)
    missing = [h for h in src if h not in haystack]
    ratio = len(missing) / len(src)
    # Require both a bad ratio and a meaningful count, so one stray heading on a
    # short article can't trip the gate.
    if ratio > MAX_MISSING_HEADINGS_RATIO and len(missing) >= 3:
        preview = "\n".join(f"    - {h}" for h in missing[:12])
        more = f"\n    ... and {len(missing) - 12} more" if len(missing) > 12 else ""
        sys.exit(
            f"Refusing to write — extraction dropped {len(missing)} of {len(src)} "
            f"source sections ({ratio:.0%}):\n{preview}{more}\n"
            "The body extractor lost part of the article. Do not trust the note; "
            "re-run, and if it persists the page layout needs a look."
        )
    if missing:
        print(
            f"Note: {len(missing)}/{len(src)} source headings not found in the body "
            f"(under the {MAX_MISSING_HEADINGS_RATIO:.0%} gate): {missing}",
            file=sys.stderr,
        )


def trim_body_head(body: str, title: str, subtitle: str | None) -> str:
    """Drop the article header block (title H1, byline, image caption) so the
    body starts at the first paragraph of prose. Anchors on the subtitle line
    when available, otherwise the title line.
    """
    lines = body.split("\n")

    def find_anchor(needle: str) -> int | None:
        # og:description truncates the subtitle with an ellipsis ("Here is
        # everything…"), which never matches the body's full sentence. Match on
        # the part before the ellipsis instead, or the subtitle heading survives
        # into the body and gets duplicated against build_note's own copy.
        n = ELLIPSIS_TAIL.sub("", needle).strip()
        if not n:
            return None
        # Only the leading lines are the header. A subtitle/title phrase that
        # recurs deeper in the prose (freedium echoes it, and authors restate
        # their thesis) must NOT be treated as the header, or we'd drop the
        # entire article body and keep only its tail.
        for i, line in enumerate(lines[:HEADER_SEARCH_LINES]):
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


PAYWALL_JSON_RE = re.compile(r'"isAccessibleForFree"\s*:\s*(?:false|"false"|0)', re.IGNORECASE)


def looks_paywalled(html: str) -> bool:
    if PAYWALL_JSON_RE.search(html):
        return True
    return any(marker in html for marker in PAYWALL_MARKERS)


def via_mirror(url: str) -> str:
    return MIRROR_BASE + url


def strip_mirror_prefix(url: str) -> str:
    if url.startswith(MIRROR_BASE):
        return url[len(MIRROR_BASE):]
    return url


GENERIC_MIRROR_TITLES = {"freedium", "untitled article", "untitled", ""}

BYLINE_SUFFIX = re.compile(r"\s+\|\s+by\s+.*$", re.IGNORECASE)


def strip_byline_suffix(title: str) -> str:
    """Drop ' | by Author...' (and anything after) — Medium puts the author in
    og:title, not just og:site_name."""
    return BYLINE_SUFFIX.sub("", title).strip()


def yaml_quote(value: str) -> str:
    """Quote a string for safe use as a YAML scalar value."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def find_article_title_in_body(body: str, subtitle: str | None) -> str | None:
    """Return the H1 closest above the subtitle line, otherwise the first H1.
    Falls back to None if no H1 exists.
    """
    lines = body.split("\n")
    in_code = False
    code_line = [False] * len(lines)
    for i, l in enumerate(lines):
        if l.lstrip().startswith("```"):
            in_code = not in_code
        code_line[i] = in_code
    h1_indexes = [
        i for i, l in enumerate(lines)
        if l.startswith("# ") and l[2:].strip() and not code_line[i]
    ]
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
    section level. Headings inside fenced code blocks (e.g. a `#### OUTPUT ####`
    comment banner) are left untouched.
    """
    prose = "".join(seg for is_code, seg in split_code_fences(body) if not is_code)
    h2_count = len(re.findall(r"(?m)^##\s", prose))
    h3_count = len(re.findall(r"(?m)^###\s", prose))
    if h2_count == 0 and h3_count >= 2:
        shift = lambda m: m.group(1)[1:] + m.group(2)
        body = "".join(
            seg if is_code else re.sub(r"(?m)^(#{2,})(\s)", shift, seg)
            for is_code, seg in split_code_fences(body)
        )
    return body


def try_fetch_url(url: str) -> str | None:
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return downloaded
        if attempt < FETCH_ATTEMPTS:
            delay = FETCH_BACKOFF_SECONDS * attempt
            print(
                f"Fetch attempt {attempt}/{FETCH_ATTEMPTS} returned nothing — retrying in {delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)
    return None


def fetch_url(url: str) -> str:
    html = try_fetch_url(url)
    if html is None:
        sys.exit(f"Failed to fetch URL after {FETCH_ATTEMPTS} attempts: {url}")
    return html


def fetch_mirror_until_good(original_url: str):
    """Fetch + extract through the mirror, retrying because the mirror
    intermittently returns nothing or a thin placeholder page. Returns
    (html, (title, url, subtitle, body)) for the best attempt. The body is the
    raw extracted markdown (pre-polish); success is judged on its length and a
    non-generic title rather than on a mere HTTP 200.
    """
    mirror_url = via_mirror(original_url)
    best = None  # (html, extract_tuple) with the longest body seen so far
    for attempt in range(1, MIRROR_ATTEMPTS + 1):
        html = trafilatura.fetch_url(mirror_url)
        if html:
            result = extract(html, original_url)
            title, _url, _subtitle, body = result
            if len(body) >= MIN_BODY_CHARS and title.strip().lower() not in GENERIC_MIRROR_TITLES:
                return html, result
            if best is None or len(body) > len(best[1][3]):
                best = (html, result)
        if attempt < MIRROR_ATTEMPTS:
            reason = "returned nothing" if not html else "returned a placeholder/thin page"
            delay = FETCH_BACKOFF_SECONDS * attempt
            print(
                f"Mirror attempt {attempt}/{MIRROR_ATTEMPTS} {reason} — retrying in {delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)
    if best is not None and len(best[1][3]) >= MIN_BODY_CHARS:
        return best
    sys.exit(
        f"Mirror never returned a usable article after {MIRROR_ATTEMPTS} attempts: {mirror_url}\n"
        "The mirror is intermittently flaky — re-running in a moment usually works."
    )


def load_html(args) -> tuple[str, str | None]:
    """Returns (html_or_url_content, source_url_or_none).
    The source URL we hand on never includes the mirror prefix.
    """
    if args.url:
        if args.url.startswith(MIRROR_BASE):
            return fetch_url(args.url), strip_mirror_prefix(args.url)
        # Just load the origin here; main() decides whether to reroute through
        # the mirror (paywall, thin extraction, or — as below — no response at
        # all, since Medium simply refuses some posts) so the retry/quality
        # logic lives in one place. None means "origin gave us nothing".
        return try_fetch_url(args.url), args.url

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


def clean_article_html(article_html: str) -> str:
    """Strip noise from the readability HTML before the markdown conversion:

    * <figure>/<img>/<picture>/<svg> so image captions don't leak in;
    * <button> (freedium's code copy buttons) so empty `[][]` links don't leak;
    * <style>/<script>/<noscript> in case any survived readability;
    * class/style/data-* attributes so Tailwind wrappers like
      `<div class="relative">` and `dark:hidden` spans don't become
      `:: relative` / `dark:hidden` pandoc artifacts.
    """
    try:
        tree = lxml_html.fragment_fromstring(article_html, create_parent="div")
    except Exception:
        return article_html
    for tag in ("figure", "img", "picture", "svg", "button", "style", "script", "noscript"):
        for el in list(tree.iter(tag)):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)

    # Remember each code block's language before the class purge below eats it.
    langs = {el: code_language(el) for el in tree.iter("pre")}

    for el in tree.iter():
        for attr in list(el.attrib):
            if attr in ("class", "style") or attr.startswith("data-"):
                del el.attrib[attr]

    # Re-stamp a class on every <pre>. pandoc only emits a ``` fence for a code
    # block that carries attributes — bare <pre> becomes an indented block, which
    # split_code_fences cannot see, which means the prose scrubbers in polish_body
    # run straight over the code and mangle it (`<value>`, `{"json": 1}`).
    # A class is what buys the fence, and the fence is what protects the code.
    for el, lang in langs.items():
        el.set("class", lang or "text")

    return lxml_html.tostring(tree, encoding="unicode")


LANG_CLASS = re.compile(r"(?:language|lang|highlight|brush)[-:]([\w+#]+)", re.IGNORECASE)


def code_language(pre_el) -> str | None:
    """Best-effort language for a <pre>, from its own or its <code> child's class."""
    for el in (pre_el, *pre_el.iter("code")):
        m = LANG_CLASS.search(el.get("class", "") or "")
        if m:
            return m.group(1).lower()
    return None


def extract(html: str, fallback_url: str | None):
    """Extract (title, url, subtitle, raw_body_md) from a page. On extraction
    failure it returns an empty body rather than exiting, so callers (the mirror
    retry loop, the final write gate) can decide what to do."""
    doc = Document(html)
    article_html = extract_article_html(html)
    # Mirror placeholder pages extract to a near-empty fragment; treat as a miss.
    if not article_html or len(article_html) < 200:
        return "Untitled Article", fallback_url, None, ""

    article_html = clean_article_html(article_html)
    try:
        body_md = html_to_markdown(article_html)
    except subprocess.CalledProcessError:
        return "Untitled Article", fallback_url, None, ""

    meta = trafilatura.extract_metadata(html)
    meta_title = meta.title if meta and meta.title else None
    sitename = meta.sitename if meta and meta.sitename else None

    # On freedium the og:title is "Freedium" but the article title leaks into
    # og:site_name as "Real Title | by Author". Prefer that when og:title is
    # the generic mirror name.
    if (not meta_title or meta_title.strip().lower() in GENERIC_MIRROR_TITLES) and sitename:
        candidate = strip_byline_suffix(sitename)
        if candidate and candidate.lower() not in GENERIC_MIRROR_TITLES:
            meta_title = candidate

    title = meta_title or doc.short_title() or "Untitled Article"
    title = strip_byline_suffix(title)
    url = (meta.url if meta else None) or fallback_url
    description = meta.description if meta else None  # subtitle, when present

    return title, url, description, body_md.strip()


def build_note(title: str, url: str | None, subtitle: str | None, body: str) -> str:
    now = dt.datetime.now().astimezone()
    stamp = now.strftime("%Y-%m-%d %H:%M:%S%z")
    stamp = stamp[:-2] + ":" + stamp[-2:]  # +0300 -> +03:00

    lines = [
        "---",
        f"title: {yaml_quote(title)}",
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
    from_origin = bool(args.url) and not args.url.startswith(MIRROR_BASE)

    if html is None:
        # Only load_html's origin path can hand back None.
        print(f"origin returned nothing — fetching via mirror: {via_mirror(args.url)}",
              file=sys.stderr)
        html, (title, url, subtitle, body) = fetch_mirror_until_good(args.url)
    else:
        title, url, subtitle, body = extract(html, fallback_url)

        # Reroute through the mirror when the origin is paywalled, or when the
        # extraction came back thin/generic (a paywall preview or a fetch hiccup).
        # The mirror helper retries until it gets a real article body.
        if from_origin and (
            looks_paywalled(html)
            or len(body) < MIN_BODY_CHARS
            or title.strip().lower() in GENERIC_MIRROR_TITLES
        ):
            reason = (
                "paywall detected"
                if looks_paywalled(html)
                else f"thin extraction ({len(body)} chars)"
            )
            print(f"{reason} — fetching via mirror: {via_mirror(args.url)}", file=sys.stderr)
            html, (title, url, subtitle, body) = fetch_mirror_until_good(args.url)

    body = polish_body(body)

    # If page metadata gave us a generic mirror title, recover the real title
    # from the body's H1 (preferring the H1 that sits just above the subtitle).
    if title.strip().lower() in GENERIC_MIRROR_TITLES:
        recovered = find_article_title_in_body(body, subtitle)
        if recovered:
            title = recovered

    body = trim_body_head(body, title, subtitle)
    body = normalize_heading_levels(body)

    # Mechanical gate: verify the body against the source rather than trusting
    # that the extractor did its job. `html` here is whichever page the body was
    # actually built from (origin or mirror), so the comparison is like for like.
    check_completeness(body, html, title, subtitle)

    # Final quality gate: never write a note from a paywall preview, a mirror
    # placeholder, or a botched extraction. Fail loudly so a re-run is obvious.
    if title.strip().lower() in GENERIC_MIRROR_TITLES or len(body) < MIN_BODY_CHARS:
        sys.exit(
            f"Refusing to write — extraction looks incomplete "
            f"(title={title!r}, body={len(body)} chars). "
            "The source may be paywalled or the mirror flaky; try re-running."
        )

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
