#!/usr/bin/env python3
"""Render the GitHub Pages section of README.md as an HTML fragment.

Usage: make_readme_section.py <README.md> <out.html>

README.md is the single source of truth for the prose on the published site.
Everything between the two marker comments

    <!-- github-pages:start -->
    <!-- github-pages:end -->

is rendered to HTML here and handed to make_download_page.py, which wraps it in
the page shell (title, styling, download table, footer). Both delimiters are
required, exactly once, start before end, and the section must not be empty: a
missing or mangled marker is a build failure, not a quietly shorter page.

Markdown is parsed by markdown-it-py (CommonMark preset) rather than by hand,
with the GFM table and strikethrough rules switched on because README text uses
them. Raw HTML stays disabled: README content is data, never trusted markup, so
an accidental `<script>` is rendered as text instead of running on the site.
URLs are restricted to links that cannot execute anything -- http, https,
mailto, ftp, or no scheme at all, which covers relative paths and #anchors --
so `javascript:`, `data:`, `vbscript:` and friends never reach an attribute.

Relative links and images cannot resolve on the published site (only the
generated index.html is published, no sources are), so they are rewritten to
the repository on GitHub. Set GITHUB_REPOSITORY to override the fallback.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

START = "<!-- github-pages:start -->"
END = "<!-- github-pages:end -->"

REPO = os.environ.get("GITHUB_REPOSITORY") or "SnoutFirst/cmake_template_nowasm"

#: Schemes a README link may use. Everything else -- including data:, file:,
#: javascript: and vbscript: -- is refused, so the list is an allowlist rather
#: than a denylist of currently fashionable attacks.
ALLOWED_SCHEMES = frozenset({"http", "https", "mailto", "ftp"})

_SCHEME = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*):")

#: Browsers ignore ASCII whitespace and control characters inside a scheme
#: ("java\tscript:" still runs), so they are dropped before it is looked for.
_IGNORED_IN_URL = re.compile(r"[\x00-\x20\x7f]+")


class SectionError(Exception):
    """The README does not delimit its GitHub Pages section correctly."""


def _marker_lines(text: str, marker: str) -> list[int]:
    return [
        number for number, line in enumerate(text.splitlines(), 1) if marker in line
    ]


# --- link and image URLs ----------------------------------------------------


def _is_allowed_url(url: str) -> bool:
    """True for a scheme relative URL or for one of ALLOWED_SCHEMES."""
    match = _SCHEME.match(_IGNORED_IN_URL.sub("", url))
    return match is None or match.group(1).lower() in ALLOWED_SCHEMES


def _resolve(url: str, *, image: bool = False) -> str:
    """Point a relative README URL at GitHub, pass absolute ones through."""
    if not _is_allowed_url(url):
        # The parser refuses these before they become tokens, so this is only
        # a second line of defence: neutralize rather than take a chance.
        return "#"
    if _SCHEME.match(url) or url.startswith(("#", "/")):
        return url
    path = url.lstrip("./") or url
    if image:
        return f"https://raw.githubusercontent.com/{REPO}/HEAD/{path}"
    return f"https://github.com/{REPO}/blob/HEAD/{path}"


def _rewrite_urls(tokens: list[Token]) -> None:
    """Resolve every href/src in place, before the tokens are rendered."""
    for token in tokens:
        if token.type == "link_open":
            token.attrSet("href", _resolve(token.attrGet("href") or ""))
        elif token.type == "image":
            token.attrSet("src", _resolve(token.attrGet("src") or "", image=True))
            token.attrSet("loading", "lazy")
        if token.children:
            _rewrite_urls(token.children)


def _new_parser() -> MarkdownIt:
    parser = MarkdownIt(
        "commonmark",
        # HTML5 output (no XHTML-style trailing slashes), raw HTML escaped,
        # no autolinking or typographic substitutions behind our back.
        {"html": False, "xhtmlOut": False, "linkify": False, "typographer": False},
    )
    parser.enable("table")
    parser.enable("strikethrough")
    parser.validateLink = _is_allowed_url
    return parser


PARSER = _new_parser()


def render_markdown(markdown: str) -> str:
    """Convert the extracted README section to an HTML fragment."""
    tokens = PARSER.parse(markdown)
    _rewrite_urls(tokens)
    return PARSER.renderer.render(tokens, PARSER.options, {})


# --- extraction -------------------------------------------------------------


def extract_section(text: str) -> str:
    starts = _marker_lines(text, START)
    ends = _marker_lines(text, END)

    if len(starts) != 1:
        raise SectionError(
            f"expected exactly one {START} line, found {len(starts)}"
            + (f" (lines {', '.join(map(str, starts))})" if starts else "")
        )
    if len(ends) != 1:
        raise SectionError(
            f"expected exactly one {END} line, found {len(ends)}"
            + (f" (lines {', '.join(map(str, ends))})" if ends else "")
        )
    if starts[0] > ends[0]:
        raise SectionError(
            f"{END} (line {ends[0]}) comes before {START} (line {starts[0]})"
        )

    section = "\n".join(text.splitlines()[starts[0] : ends[0] - 1])
    if not section.strip():
        raise SectionError(
            f"the section between line {starts[0]} and line {ends[0]} is empty"
        )
    return section


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    source, destination = Path(argv[1]), Path(argv[2])
    try:
        section = extract_section(source.read_text(encoding="utf-8"))
        fragment = render_markdown(section).strip() + "\n"
    except (OSError, SectionError) as error:
        print(f"{source}: {error}", file=sys.stderr)
        return 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(fragment, encoding="utf-8")
    print(f"wrote {destination} ({len(section.splitlines())} README lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
