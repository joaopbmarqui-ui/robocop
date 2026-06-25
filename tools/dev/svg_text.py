"""Extract decoded, whitespace-normalized text from a Textual SVG screenshot.

Textual's SVG export renders each styled run as a ``<text>`` element and encodes
spaces as ``&#160;`` (non-breaking space). Substring checks against the raw SVG
therefore miss any phrase that contains a space. ``svg_to_text`` flattens the
text nodes and normalizes whitespace so callers can assert on plain phrases.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

_TEXT_NODE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)


def svg_to_text(svg: str) -> str:
    parts = [html.unescape(match) for match in _TEXT_NODE.findall(svg)]
    joined = " ".join(parts).replace("\xa0", " ")
    return re.sub(r"\s+", " ", joined).strip()


def svg_file_to_text(path: str | Path) -> str:
    return svg_to_text(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    for arg in sys.argv[1:]:
        print(f"==== {arg} ====")
        print(svg_file_to_text(arg)[:1600])
        print()
