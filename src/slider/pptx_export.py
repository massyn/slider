"""Build a PowerPoint file from a loaded deck.

Each slide becomes a real slide on a stock PowerPoint layout (title, title and content,
title only), with the narration as its speaker notes. The theme's styling is not carried
over: restyle the result in PowerPoint's Slide Master, or import it into Google Slides.
"""

import logging
from pathlib import Path
from typing import Any

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.slide import Slide
from pptx.text.text import TextFrame
from pptx.util import Inches, Pt

from slider.errors import DeckError
from slider.pptx_text import Para, Run, markdown_paragraphs

logger = logging.getLogger(__name__)

# Positions in the default PowerPoint template's layouts
LAYOUT_TITLE, LAYOUT_CONTENT, LAYOUT_TITLE_ONLY = 0, 1, 5

CODE_FONT = "Consolas"
CONTENT_PT = 24  # body text in the content placeholder
COLUMN_PT = 20  # body text in a column
BULLET_STEP = 342900  # EMU: how far each list level is indented in a text box


def export_pptx(deck: dict[str, Any], output: Path) -> None:
    """Write `deck` (as returned by load_deck) to `output` as a .pptx file."""
    prs = Presentation()
    for data in deck["slides"]:
        builder = _BUILDERS.get(data["layout"])
        if builder is None:
            raise DeckError(
                f"Slide {data['number']}: the pptx export has no layout {data['layout']!r}"
                f" (use {', '.join(_BUILDERS)})"
            )
        slide = builder(prs, data)
        if data["voice"]:
            slide.notes_slide.notes_text_frame.text = data["voice"]

    settings = deck["deck"]
    prs.core_properties.title = str(settings.get("title", ""))
    prs.core_properties.author = str(settings.get("author", ""))
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    logger.info("Exported %d slides", len(deck["slides"]))


def _title_slide(prs: Presentation, data: dict[str, Any]) -> Slide:
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE])
    slide.shapes.title.text = data["title"]
    subtitle = slide.placeholders[1]
    if data["subtitle"]:
        subtitle.text = data["subtitle"]
    else:
        _drop(subtitle)
    return slide


def _content_slide(prs: Presentation, data: dict[str, Any]) -> Slide:
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_CONTENT])
    _set_title(slide, data)
    paras = markdown_paragraphs(data["body"])
    if data["subtitle"]:
        paras.insert(0, Para([Run(data["subtitle"], italic=True)]))
    body = slide.placeholders[1]
    if paras:
        _fill(body.text_frame, paras, CONTENT_PT, in_placeholder=True)
    else:
        _drop(body)
    return slide


def _columns_slide(prs: Presentation, data: dict[str, Any]) -> Slide:
    slide = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TITLE_ONLY])
    _set_title(slide, data)

    margin = Inches(0.5)
    width = prs.slide_width - 2 * margin
    top = Inches(1.75)
    if data["body"]:
        intro = slide.shapes.add_textbox(margin, top, width, Inches(0.9))
        _fill(
            intro.text_frame,
            markdown_paragraphs(data["body"]),
            COLUMN_PT,
            in_placeholder=False,
        )
        top += Inches(1.0)

    columns = data["columns"]
    gap = Inches(0.3)
    column_width = (width - gap * (len(columns) - 1)) // len(columns)
    for i, column in enumerate(columns):
        box = slide.shapes.add_textbox(
            margin + i * (column_width + gap),
            top,
            column_width,
            prs.slide_height - top - margin,
        )
        paras = [Para([Run(column["heading"], bold=True)])]
        paras += markdown_paragraphs(column["body"])
        _fill(box.text_frame, paras, COLUMN_PT, in_placeholder=False)
    return slide


_BUILDERS = {
    "title": _title_slide,
    "content": _content_slide,
    "columns": _columns_slide,
}


def _set_title(slide: Slide, data: dict[str, Any]) -> None:
    """Fill the title placeholder, or remove it from an untitled slide."""
    if data["title"]:
        slide.shapes.title.text = data["title"]
    else:
        _drop(slide.shapes.title)


def _drop(shape) -> None:
    """Remove an unused placeholder so PowerPoint doesn't show its prompt text."""
    shape._element.getparent().remove(shape._element)


def _fill(frame: TextFrame, paras: list[Para], size: int, in_placeholder: bool) -> None:
    """Write `paras` into `frame`. A placeholder brings its own bullets, a text box doesn't."""
    frame.word_wrap = True
    for i, para in enumerate(paras):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        _set_bullet(p, para, in_placeholder)
        if in_placeholder:
            p.level = min(para.level, 8)
        run_size = round(size * 2 / 3) if para.code else size - 4 * para.level
        for run in para.runs:
            r = p.add_run()
            r.text = run.text
            r.font.size = Pt(max(run_size, 10))
            if run.bold:
                r.font.bold = True
            if run.italic:
                r.font.italic = True
            if run.code or para.code:
                r.font.name = CODE_FONT
            if run.href:
                r.hyperlink.address = run.href


def _set_bullet(p, para: Para, in_placeholder: bool) -> None:
    pPr = p._p.get_or_add_pPr()
    if not para.list_kind:
        pPr.set("marL", "0")
        pPr.set("indent", "0")
        etree.SubElement(pPr, qn("a:buNone"))
        return
    if not in_placeholder:
        pPr.set("marL", str(BULLET_STEP * (para.level + 1)))
        pPr.set("indent", str(-BULLET_STEP))
    if para.list_kind == "ol":
        etree.SubElement(pPr, qn("a:buAutoNum")).set("type", "arabicPeriod")
    elif not in_placeholder:
        etree.SubElement(pPr, qn("a:buChar")).set("char", "•")
