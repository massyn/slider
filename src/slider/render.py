"""Render a loaded deck to a single HTML page using a theme's Jinja templates.

A theme is a folder holding base.html (the page shell, colours and
navigation) plus one <layout>.html per slide layout.
"""

import logging
from pathlib import Path
from typing import Any

import markdown
from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    TemplateNotFound,
    select_autoescape,
)
from markupsafe import Markup

from slider.deck import DeckError

logger = logging.getLogger(__name__)

MARKDOWN_EXTENSIONS = ["tables", "fenced_code", "attr_list"]


def render_deck(
    deck: dict[str, Any], themes_dir: Path, theme: str | None = None
) -> str:
    """Render every slide with its layout template, then wrap them in base.html.

    A theme is self-contained: every template is read from its own folder.
    """
    theme = theme or deck["deck"].get("theme", "default")
    theme_dir = themes_dir / theme
    if not theme_dir.is_dir():
        raise DeckError(f"Theme '{theme}' not found in {themes_dir}")

    env = Environment(
        loader=FileSystemLoader(theme_dir),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = lambda text: Markup(
        markdown.markdown(str(text), extensions=MARKDOWN_EXTENSIONS)
    )

    slides = []
    for slide in deck["slides"]:
        try:
            html = env.get_template(f"{slide['layout']}.html").render(
                slide=slide, deck=deck["deck"]
            )
        except TemplateNotFound as e:
            raise DeckError(
                f"Slide {slide['number']}: theme '{theme}' has no layout '{slide['layout']}'"
            ) from e
        except TemplateError as e:
            raise DeckError(f"Slide {slide['number']} ({slide['layout']}): {e}") from e
        slides.append(
            {
                "layout": slide["layout"],
                "voice": slide.get("voice", ""),
                "html": Markup(html),
            }
        )

    logger.info("Rendered %d slides with theme '%s'", len(slides), theme)
    return env.get_template("base.html").render(deck=deck["deck"], slides=slides)
