"""Load a slide deck from a Markdown file, or a folder of them, into dicts for rendering.

A folder's `.md` files are stitched together in name order (files starting with `_` are
skipped). Optional YAML front matter at the very top of the first file holds deck settings:
title, theme and voice.
"""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from slider.errors import DeckError
from slider.slides import split_slides

logger = logging.getLogger(__name__)

__all__ = ["DeckError", "find_markdown_files", "load_deck", "parse_deck"]

_FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


def find_markdown_files(path: Path) -> list[Path]:
    """The Markdown files that make up the deck, in slide order."""
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise DeckError(f"{path} is not a file or a folder")
    files = sorted(p for p in path.rglob("*.md") if not p.name.startswith("_"))
    if not files:
        raise DeckError(f"No Markdown files found in {path}")
    return files


def load_deck(path: Path) -> dict[str, Any]:
    """Read a deck from a Markdown file or folder: {"deck": {...}, "slides": [...]}."""
    try:
        texts = [f.read_text(encoding="utf-8") for f in find_markdown_files(path)]
    except (OSError, UnicodeDecodeError) as e:
        raise DeckError(f"Cannot read deck {path}: {e}") from e
    return parse_deck("\n\n".join(texts))


def parse_deck(text: str) -> dict[str, Any]:
    """Split the stitched Markdown into settings (front matter) and slides."""
    settings: dict[str, Any] = {}
    if match := _FRONT_MATTER.match(text):
        try:
            settings = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as e:
            raise DeckError(f"Invalid front matter: {e}") from e
        if not isinstance(settings, dict):
            raise DeckError("Front matter must be a mapping of settings")
        text = text[match.end() :]

    slides = split_slides(text)
    if not slides:
        raise DeckError("No slides found")
    if "title" not in settings:
        settings["title"] = next((s["title"] for s in slides if s["title"]), "Slides")
    logger.info("Loaded deck with %d slides", len(slides))
    return {"deck": settings, "slides": slides}
