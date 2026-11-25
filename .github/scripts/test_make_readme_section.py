#!/usr/bin/env python3
"""Tests for make_readme_section.py.

Run them from the repository root with

    python3 -m unittest discover --start-directory .github/scripts --pattern 'test_*.py'

The GitHub Actions job "Test the page scripts" does exactly that, after
installing markdown-it-py.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import make_download_page
import make_readme_section as section_reader

README = Path(__file__).resolve().parents[2] / "README.md"


def render(markdown: str) -> str:
    """Render a snippet with the repository's parser configuration."""
    return section_reader.render_markdown(markdown)


def quiet(function, *args, **kwargs):
    """Call function with its stdout and stderr swallowed."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        return function(*args, **kwargs)


class ExtractionTests(unittest.TestCase):
    """Only the marked-up part of README.md is rendered."""

    def test_extracts_the_section_between_the_markers(self):
        text = "\n".join(
            [
                "# Title",
                "before",
                section_reader.START,
                "## Inside",
                "body",
                section_reader.END,
                "after",
            ]
        )
        self.assertEqual(
            section_reader.extract_section(text), "## Inside\nbody"
        )

    def test_missing_start_marker(self):
        text = f"# Title\nbody\n{section_reader.END}\n"
        with self.assertRaises(section_reader.SectionError) as raised:
            section_reader.extract_section(text)
        self.assertIn("expected exactly one", str(raised.exception))
        self.assertIn(section_reader.START, str(raised.exception))

    def test_missing_end_marker(self):
        text = f"{section_reader.START}\nbody\n"
        with self.assertRaises(section_reader.SectionError) as raised:
            section_reader.extract_section(text)
        self.assertIn(section_reader.END, str(raised.exception))

    def test_duplicate_start_marker(self):
        text = "\n".join(
            [section_reader.START, "a", section_reader.START, "b", section_reader.END]
        )
        with self.assertRaises(section_reader.SectionError) as raised:
            section_reader.extract_section(text)
        self.assertIn("found 2", str(raised.exception))
        self.assertIn("lines 1, 3", str(raised.exception))

    def test_duplicate_end_marker(self):
        text = "\n".join(
            [section_reader.START, "a", section_reader.END, section_reader.END]
        )
        with self.assertRaises(section_reader.SectionError) as raised:
            section_reader.extract_section(text)
        self.assertIn("found 2", str(raised.exception))

    def test_reversed_markers(self):
        text = "\n".join([section_reader.END, "a", section_reader.START])
        with self.assertRaises(section_reader.SectionError) as raised:
            section_reader.extract_section(text)
        self.assertIn("comes before", str(raised.exception))

    def test_empty_section(self):
        text = "\n".join([section_reader.START, "   ", "", section_reader.END])
        with self.assertRaises(section_reader.SectionError) as raised:
            section_reader.extract_section(text)
        self.assertIn("is empty", str(raised.exception))


class MarkdownTests(unittest.TestCase):
    """The constructs README text actually uses are rendered as HTML."""

    def test_headings(self):
        for level in range(1, 7):
            with self.subTest(level=level):
                hashes = "#" * level
                self.assertEqual(
                    render(f"{hashes} Title").strip(),
                    f"<h{level}>Title</h{level}>",
                )

    def test_paragraph(self):
        out = render("One paragraph\nthat wraps.")
        self.assertEqual(out.strip(), "<p>One paragraph\nthat wraps.</p>")

    def test_unordered_list(self):
        out = render("- one\n- two\n")
        self.assertEqual(
            out.strip(),
            "<ul>\n<li>one</li>\n<li>two</li>\n</ul>",
        )

    def test_ordered_list(self):
        out = render("1. one\n2. two\n")
        self.assertEqual(
            out.strip(),
            "<ol>\n<li>one</li>\n<li>two</li>\n</ol>",
        )

    def test_nested_list(self):
        out = render("- a\n  - b\n    - c\n- d\n")
        self.assertEqual(out.count("<ul>"), 3)
        self.assertEqual(out.count("</ul>"), 3)
        self.assertEqual(out.count("<li>"), 4)
        self.assertIn("<li>b\n<ul>", out)

    def test_list_item_continuation_line(self):
        out = render("- a long item that\n  continues here\n")
        self.assertIn("<li>a long item that\ncontinues here</li>", out)

    def test_blockquote(self):
        out = render("> quoted *text*\n")
        self.assertIn("<blockquote>", out)
        self.assertIn("<em>text</em>", out)

    def test_table(self):
        out = render("| a | b |\n| --- | --- |\n| 1 | 2 |\n")
        for expected in ("<table>", "<thead>", "<th>a</th>", "<td>1</td>", "</table>"):
            self.assertIn(expected, out)

    def test_fenced_code_block(self):
        out = render("```sh\n$ tool --name you\n<tag> *not em*\n```\n")
        self.assertIn('<pre><code class="language-sh">', out)
        # Content is literal: escaped, never parsed as Markdown.
        self.assertIn("&lt;tag&gt; *not em*", out)

    def test_fenced_code_block_without_language(self):
        out = render("```\nplain\n```\n")
        self.assertIn("<pre><code>plain\n</code></pre>", out)

    def test_inline_code(self):
        out = render("Use `--help` now.")
        self.assertIn("<code>--help</code>", out)

    def test_emphasis_and_strong(self):
        out = render("an *emphasis* and a **strong** one")
        self.assertIn("<em>emphasis</em>", out)
        self.assertIn("<strong>strong</strong>", out)

    def test_strikethrough(self):
        self.assertIn("<s>gone</s>", render("~~gone~~"))

    def test_horizontal_rule(self):
        self.assertEqual(render("---\n").strip(), "<hr>")

    def test_link_and_image(self):
        out = render("see [the docs](https://example.com/docs) and ![a shot](shot.png)")
        self.assertIn('<a href="https://example.com/docs">the docs</a>', out)
        self.assertIn("<img ", out)
        self.assertIn('alt="a shot"', out)


class UrlTests(unittest.TestCase):
    """Relative URLs point at the repository, everything else is left alone."""

    def setUp(self):
        patcher = mock.patch.object(section_reader, "REPO", "owner/project")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_relative_link_becomes_a_blob_url(self):
        self.assertEqual(
            section_reader._resolve("docs/usage.md"),
            "https://github.com/owner/project/blob/HEAD/docs/usage.md",
        )

    def test_relative_image_becomes_a_raw_url(self):
        self.assertEqual(
            section_reader._resolve("docs/shot.png", image=True),
            "https://raw.githubusercontent.com/owner/project/HEAD/docs/shot.png",
        )

    def test_leading_dot_slash_is_stripped(self):
        self.assertEqual(
            section_reader._resolve("./LICENSE"),
            "https://github.com/owner/project/blob/HEAD/LICENSE",
        )

    def test_absolute_urls_are_untouched(self):
        for url in (
            "https://example.com/a",
            "http://example.com/b",
            "mailto:x@example.com",
        ):
            with self.subTest(url=url):
                self.assertEqual(section_reader._resolve(url), url)

    def test_anchors_and_root_relative_urls_are_untouched(self):
        for url in ("#section", "/static/logo.png"):
            with self.subTest(url=url):
                self.assertEqual(section_reader._resolve(url), url)

    def test_query_strings_and_fragments_survive_rewriting(self):
        self.assertEqual(
            section_reader._resolve("docs/usage.md?plain=1#top"),
            "https://github.com/owner/project/blob/HEAD/docs/usage.md?plain=1#top",
        )

    def test_spaces_are_percent_encoded(self):
        # CommonMark needs <> around a destination that contains spaces.
        out = render("[rel](<docs/my file.md?plain=1#top>) ![i](<img/shot one.png>)")
        self.assertIn(
            'href="https://github.com/owner/project/blob/HEAD/'
            'docs/my%20file.md?plain=1#top"',
            out,
        )
        self.assertIn(
            'src="https://raw.githubusercontent.com/owner/project/HEAD/'
            'img/shot%20one.png"',
            out,
        )

    def test_images_are_loaded_lazily(self):
        self.assertIn('loading="lazy"', render("![i](shot.png)"))

    def test_fragment_only_image_source_is_untouched(self):
        self.assertEqual(section_reader._resolve("#inline", image=True), "#inline")


class SecurityTests(unittest.TestCase):
    """README text is data: no raw HTML, no executable URL schemes."""

    def test_raw_html_is_escaped(self):
        out = render("<script>alert('x')</script>")
        self.assertNotIn("<script", out)
        self.assertIn("&lt;script&gt;", out)

    def test_raw_html_link_is_escaped(self):
        out = render('<a href="https://evil.example">click</a>')
        self.assertNotIn("<a ", out)
        self.assertIn("&lt;a href=&quot;https://evil.example&quot;&gt;", out)

    def test_inline_html_tag_is_escaped(self):
        out = render("press <kbd>Ctrl</kbd> now")
        self.assertNotIn("<kbd>", out)
        self.assertIn("&lt;kbd&gt;Ctrl&lt;/kbd&gt;", out)

    def test_javascript_link_is_not_a_link(self):
        out = render("[x](javascript:alert(1))")
        self.assertNotIn("<a", out)
        self.assertNotIn("href=", out)

    def test_uppercase_javascript_link_is_not_a_link(self):
        out = render("[x](JaVaScRiPt:alert(1))")
        self.assertNotIn("href=", out)

    def test_vbscript_link_is_not_a_link(self):
        out = render("[x](vbscript:msgbox(1))")
        self.assertNotIn("href=", out)

    def test_data_url_link_is_not_a_link(self):
        out = render("[x](data:text/html,<script>alert(1)</script>)")
        self.assertNotIn("href=", out)

    def test_data_url_image_is_not_an_image(self):
        out = render("![x](data:image/png;base64,AAAA)")
        self.assertNotIn("<img", out)

    def test_scheme_allowlist(self):
        allowed = (
            "https://example.com",
            "http://example.com",
            "mailto:someone@example.com",
            "ftp://example.com/file",
            "docs/usage.md",
            "#anchor",
            "/root/relative",
        )
        for url in allowed:
            with self.subTest(url=url):
                self.assertTrue(section_reader._is_allowed_url(url))

        refused = (
            "javascript:alert(1)",
            "JaVaScRiPt:alert(1)",
            "java\tscript:alert(1)",
            "vbscript:msgbox(1)",
            "data:text/html,<script>alert(1)</script>",
            "data:image/png;base64,AAAA",
            "file:///etc/passwd",
        )
        for url in refused:
            with self.subTest(url=url):
                self.assertFalse(section_reader._is_allowed_url(url))

    def test_resolve_neutralizes_a_refused_scheme(self):
        # The parser rejects these first; _resolve must not reintroduce them.
        self.assertEqual(section_reader._resolve("javascript:alert(1)"), "#")
        self.assertEqual(section_reader._resolve("data:text/html,x", image=True), "#")


class CommandLineTests(unittest.TestCase):
    """The script keeps its interface and still feeds make_download_page.py."""

    def test_usage_error(self):
        self.assertEqual(quiet(section_reader.main, ["prog"]), 2)
        self.assertEqual(quiet(section_reader.main, ["prog", "a"]), 2)
        self.assertEqual(quiet(section_reader.main, ["prog", "a", "b", "c"]), 2)

    def test_writes_the_fragment_and_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            readme = work / "README.md"
            readme.write_text(
                "\n".join(
                    [
                        "# Heading",
                        section_reader.START,
                        "## Inside",
                        "Some **text**.",
                        section_reader.END,
                    ]
                ),
                encoding="utf-8",
            )
            output = work / "parts" / "readme.html"
            self.assertEqual(
                quiet(section_reader.main, ["prog", str(readme), str(output)]), 0
            )
            fragment = output.read_text(encoding="utf-8")
            self.assertIn("<h2>Inside</h2>", fragment)
            self.assertIn("<strong>text</strong>", fragment)
            self.assertNotIn("# Heading", fragment)
            self.assertTrue(fragment.endswith("\n"))

    def test_reports_broken_markers(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            readme = work / "README.md"
            readme.write_text("no markers here\n", encoding="utf-8")
            output = work / "readme.html"
            self.assertEqual(
                quiet(section_reader.main, ["prog", str(readme), str(output)]), 1
            )
            self.assertFalse(output.exists())

    def test_missing_input_file(self):
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / "readme.html"
            self.assertEqual(
                quiet(
                    section_reader.main,
                    ["prog", str(Path(work) / "nope.md"), str(output)],
                ),
                1,
            )

    def test_real_readme_renders(self):
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / "readme.html"
            self.assertEqual(
                quiet(section_reader.main, ["prog", str(README), str(output)]), 0
            )
            fragment = output.read_text(encoding="utf-8")
        self.assertIn("<h2>What it does</h2>", fragment)
        self.assertIn('<code class="language-sh">', fragment)
        self.assertIn("<ul>", fragment)
        self.assertNotIn("github-pages:", fragment)

    def test_fragment_is_accepted_by_make_download_page(self):
        with tempfile.TemporaryDirectory() as work:
            work = Path(work)
            fragment = work / "readme.html"
            downloads = work / "downloads"
            downloads.mkdir()
            (downloads / "cmake_template_nowasm-linux-x86_64.tar.gz").write_bytes(
                b"x" * 16
            )
            site = work / "site"

            self.assertEqual(
                quiet(section_reader.main, ["prog", str(README), str(fragment)]), 0
            )
            self.assertEqual(
                quiet(
                    make_download_page.main,
                    [
                        "prog",
                        str(downloads),
                        str(site),
                        "0123456789abcdef",
                        "main",
                        str(fragment),
                    ],
                ),
                0,
            )

            page = (site / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h2>What it does</h2>", page)
        self.assertIn("cmake_template_nowasm-linux-x86_64.tar.gz", page)
        self.assertIn("releases/download/ci-latest", page)


if __name__ == "__main__":
    unittest.main()
