"""Turn a slide's Markdown into the paragraphs and runs a PowerPoint text frame holds.

The Markdown is converted to HTML first, then walked once. Lists keep their kind and depth,
bold, italic, inline code and links become run formatting, code blocks become one monospaced
paragraph per line, and tables are flattened to one paragraph per row. Anything else is
kept as plain text.
"""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

import markdown

from slider.render import MARKDOWN_EXTENSIONS


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    href: str | None = None


@dataclass
class Para:
    runs: list[Run] = field(default_factory=list)
    list_kind: str = ""  # "ul", "ol", or "" for a plain paragraph
    level: int = 0  # list depth, from 0
    code: bool = False


def markdown_paragraphs(text: str) -> list[Para]:
    """The paragraphs of `text`, in order."""
    collector = _Collector()
    collector.feed(markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS))
    collector.close()
    return collector.finish()


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.paras: list[Para] = []
        self.current: Para | None = None
        self.lists: list[str] = []
        self.li_depth = 0
        self.bold = self.italic = self.code = 0
        self.links: list[str] = []
        self.pre: list[str] | None = None

    def finish(self) -> list[Para]:
        self._close()
        return self.paras

    def _open(self, **kwargs) -> None:
        self._close()
        self.current = Para(**kwargs)

    def _close(self) -> None:
        if self.current and self.current.runs:
            last = self.current.runs[-1]
            last.text = last.text.rstrip()
            self.paras.append(self.current)
        self.current = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("ul", "ol"):
            self.lists.append(tag)
        elif tag == "li":
            self.li_depth += 1
            self._open(
                list_kind=self.lists[-1] if self.lists else "ul",
                level=max(len(self.lists) - 1, 0),
            )
        elif tag == "p":
            # A loose list item wraps its text in <p>: keep it in the item's paragraph.
            if not (self.li_depth and self.current is not None):
                self._open()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._open()
            self.bold += 1
        elif tag == "br" and self.current is not None:
            self._open(level=self.current.level)
        elif tag == "pre":
            self._close()
            self.pre = []
        elif tag == "tr":
            self._open()
        elif tag in ("td", "th") and self.current and self.current.runs:
            if not self.current.runs[-1].text.endswith(" "):
                self.current.runs.append(Run(" "))
            self.current.runs.append(Run("| "))
        elif tag in ("strong", "b"):
            self.bold += 1
        elif tag in ("em", "i"):
            self.italic += 1
        elif tag == "code" and self.pre is None:
            self.code += 1
        elif tag == "a":
            self.links.append(dict(attrs).get("href") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("ul", "ol") and self.lists:
            self.lists.pop()
        elif tag == "li":
            self.li_depth = max(self.li_depth - 1, 0)
            self._close()
        elif tag == "p" and not self.li_depth:
            self._close()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.bold -= 1
            self._close()
        elif tag == "pre" and self.pre is not None:
            for line in "".join(self.pre).rstrip("\n").split("\n"):
                self.paras.append(Para([Run(line, code=True)], code=True))
            self.pre = None
        elif tag == "tr":
            self._close()
        elif tag in ("strong", "b"):
            self.bold -= 1
        elif tag in ("em", "i"):
            self.italic -= 1
        elif tag == "code" and self.pre is None:
            self.code -= 1
        elif tag == "a" and self.links:
            self.links.pop()

    def handle_data(self, data: str) -> None:
        if self.pre is not None:
            self.pre.append(data)
            return
        text = re.sub(r"\s+", " ", data)
        if self.current is None:
            if not text.strip():
                return
            self._open()
        if not self.current.runs:
            text = text.lstrip()
        if text:
            self.current.runs.append(
                Run(
                    text,
                    bold=self.bold > 0,
                    italic=self.italic > 0,
                    code=self.code > 0,
                    href=(self.links[-1] or None) if self.links else None,
                )
            )
