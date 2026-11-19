"""Command line entry point: render a Markdown deck to HTML, a narrated video or PowerPoint."""

import argparse
import logging
import os
from pathlib import Path

from slider.deck import DeckError, load_deck
from slider.newtheme import create_theme
from slider.pptx_export import export_pptx
from slider.render import render_deck
from slider.video import VideoError, VideoSettings, make_video

logger = logging.getLogger("slider")

SUFFIXES = {"html": ".html", "video": ".mp4", "pptx": ".pptx"}


def main() -> int:
    logging.basicConfig(
        level=os.getenv("SLIDER_LOG_LEVEL", "INFO"), format="%(levelname)s %(message)s"
    )
    default_themes = Path(__file__).parent / "themes"

    parser = argparse.ArgumentParser(description="Render a Markdown slide deck.")
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        help="a Markdown file, or a folder of them in slide order",
    )
    parser.add_argument(
        "-f", "--format", choices=SUFFIXES, default="html", help="output type"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output file (default: <source>.html, .mp4 or .pptx)",
    )
    parser.add_argument("-t", "--theme", help="theme name (overrides deck.theme)")
    parser.add_argument(
        "--themes-dir",
        type=Path,
        default=Path(os.getenv("SLIDER_THEMES_DIR", default_themes)),
        help="folder containing themes",
    )
    parser.add_argument(
        "--new-theme",
        metavar="NAME",
        help="create theme NAME in --themes-dir as a copy of --base, instead of rendering",
    )
    parser.add_argument(
        "--base",
        default="default",
        help="theme copied by --new-theme (default: %(default)s)",
    )
    args = parser.parse_args()

    if args.new_theme:
        try:
            create_theme(args.new_theme, args.base, args.themes_dir, default_themes)
        except (DeckError, OSError):
            logger.exception("Failed to create theme %s", args.new_theme)
            return 1
        return 0
    if args.source is None:
        parser.error("a source is required unless --new-theme is given")

    name = args.source.stem if args.source.is_file() else args.source.name
    output = args.output or args.source.with_name(name + SUFFIXES[args.format])
    try:
        deck = load_deck(args.source)
        if args.format == "pptx":
            export_pptx(deck, output)
        else:
            html = render_deck(deck, args.themes_dir, args.theme)
            if args.format == "video":
                make_video(html, deck["deck"], output, VideoSettings())
            else:
                output.write_text(html, encoding="utf-8")
    except (DeckError, VideoError, OSError):
        logger.exception("Failed to render %s", args.source)
        return 1
    logger.info("Wrote %s", output)
    return 0
