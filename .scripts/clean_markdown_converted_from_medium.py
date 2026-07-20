#!/usr/bin/env python3
"""RETIRED 2026-07-20 — superseded by ~/.scripts/save_medium_article.py

This tool cleaned pandoc-converted Medium HTML, but its markdown scrub had a
data-destroying bug: `re.sub(r'{.*?}', '', ...)` stripped every {placeholder}
out of code samples (f-strings, dict/JSON literals) — turning
`f"product:{product_id}"` into `f"product:"`, valid-looking code that is quietly
wrong. Because it ran over the whole file with no code-fence protection, it
silently corrupted the code in every note it touched. See the vault note
'Orchestrating Our Agents SDLC on Temporal ...' investigation and
~/.claude memory 'reference-medium-importer' for the full write-up.

Use `save_medium_article.py` instead — it extracts with trafilatura, fences code
blocks so scrubbers can't reach them, preserves links, and has a completeness
gate that refuses to write a note that lost part of its source.

This stub intentionally refuses to run so the old scrub can never corrupt a note
again. (Its only caller was prepare_for_obsidian.sh, itself part of the retired
manual workflow.)
"""
import sys

sys.exit(
    "clean_markdown_converted_from_medium.py is RETIRED (it silently gutted code "
    "in every note). Use ~/.scripts/save_medium_article.py instead."
)
