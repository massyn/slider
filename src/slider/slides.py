"""Split Markdown into slides.

The rules:
  - `# Heading` starts a slide and is its title. A line of `---` (after a blank line)
    also starts one, for a slide with no title.
  - A `## Heading` straight after the title is the subtitle. Anywhere else it is content.
  - `{: layout=columns }` at the end of the title line picks the layout. Without it a slide
    with nothing but a title (and subtitle) is a `title` slide and any other is `content`.
  - In a `columns` slide each `### Heading` section is one column.
  - `<!-- voice: ... -->` is narration: never shown, spoken in order. Use as many per slide
    as you like.

Headings, breaks and comments inside fenced code blocks are left alone.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from slider.errors import DeckError

_H1 = re.compile(r"# +(?P<text>.*?)\s*")
_H2 = re.compile(r"## +(?P<text>.*?)\s*")
_H3 = re.compile(r"### +(?P<text>.*?)\s*")
_BREAK = re.compile(r"---\s*")
_FENCE = re.compile(r" {0,3}(```+|~~~+)")
_ATTRS = re.compile(r"\s*\{:\s*(?P<attrs>[^}]*)\}\s*\Z")
_ATTR = re.compile(r"""([\w-]+)=(?:"([^"]*)"|'([^']*)'|(\S+))""")
_VOICE = re.compile(r"<!--\s*voice:\s*(.*?)\s*-->", re.DOTALL)

_KNOWN_ATTRS = {"layout"}


@dataclass
class _Chunk:
    titled: bool
    lines: list[str] = field(default_factory=list)


def _fenced(lines: list[str]) -> list[bool]:
    """For each line, whether it is part of a fenced code block (fences included)."""
    result = []
    fence = None
    for line in lines:
        match = _FENCE.match(line)
        if fence is None:
            fence = match.group(1)[0] if match else None
            result.append(fence is not None)
        else:
            result.append(True)
            if match and match.group(1)[0] == fence:
                fence = None
    return result


def split_slides(text: str) -> list[dict[str, Any]]:
    """Turn Markdown text into one dict per slide, numbered from 1."""
    lines = text.splitlines()
    chunks = [_Chunk(titled=False)]
    previous_blank = True
    for line, fenced in zip(lines, _fenced(lines), strict=True):
        if not fenced and _H1.fullmatch(line):
            chunks.append(_Chunk(titled=True, lines=[line]))
        elif not fenced and previous_blank and _BREAK.fullmatch(line):
            chunks.append(_Chunk(titled=False))
        else:
            chunks[-1].lines.append(line)
        previous_blank = not line.strip()

    slides = [c for c in chunks if c.titled or any(line.strip() for line in c.lines)]
    return [_build(chunk, number) for number, chunk in enumerate(slides, 1)]


def _build(chunk: _Chunk, number: int) -> dict[str, Any]:
    text, notes = _take_voice("\n".join(chunk.lines))
    lines = text.splitlines()

    title, attrs = "", {}
    if chunk.titled:
        title, attrs = _parse_title(lines.pop(0), number)

    subtitle = ""
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if chunk.titled and first is not None and (m := _H2.fullmatch(lines[first])):
        subtitle = m["text"]
        del lines[first]

    body = "\n".join(lines).strip()
    if not title and not subtitle and not body:
        raise DeckError(f"Slide {number}: nothing but narration")

    layout = attrs.get("layout") or ("content" if body else "title")
    slide = {
        "number": number,
        "layout": layout,
        "title": title,
        "subtitle": subtitle,
        "body": body,
        "columns": [],
        "voice": "\n\n".join(notes),
    }
    if layout == "columns":
        slide["body"], slide["columns"] = _split_columns(body, number)
    return slide


def _parse_title(line: str, number: int) -> tuple[str, dict[str, str]]:
    """The title text and its `{: key=value }` attributes."""
    text = _H1.fullmatch(line)["text"]
    attrs: dict[str, str] = {}
    if match := _ATTRS.search(text):
        for key, *quoted in _ATTR.findall(match["attrs"]):
            if key not in _KNOWN_ATTRS:
                raise DeckError(f"Slide {number}: unknown attribute {key!r}")
            attrs[key] = next((value for value in quoted if value), "")
        text = text[: match.start()]
    return text.strip(), attrs


def _take_voice(text: str) -> tuple[str, list[str]]:
    """The text without its voice comments, and the narration they held, in order."""
    fenced = _fenced(text.splitlines())
    notes: list[str] = []

    def take(match: re.Match[str]) -> str:
        if fenced[text.count("\n", 0, match.start())]:
            return match.group(0)
        if note := " ".join(match.group(1).split()):
            notes.append(note)
        return ""

    return _VOICE.sub(take, text), notes


def _split_columns(body: str, number: int) -> tuple[str, list[dict[str, str]]]:
    """The text above the first `###`, and one {heading, body} per `###` section."""
    lines = body.splitlines()
    intro: list[str] = []
    columns: list[dict[str, Any]] = []
    for line, fenced in zip(lines, _fenced(lines), strict=True):
        if not fenced and (match := _H3.fullmatch(line)):
            columns.append({"heading": match["text"], "lines": []})
        elif columns:
            columns[-1]["lines"].append(line)
        else:
            intro.append(line)
    if not columns:
        raise DeckError(f"Slide {number}: the columns layout needs ### sections")
    return "\n".join(intro).strip(), [
        {"heading": c["heading"], "body": "\n".join(c["lines"]).strip()}
        for c in columns
    ]
