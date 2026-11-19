from pathlib import Path

import pytest
from pptx import Presentation

from slider.deck import DeckError, load_deck, parse_deck
from slider.pptx_export import export_pptx
from slider.pptx_text import markdown_paragraphs

SAMPLE = Path(__file__).parent.parent / "examples" / "preso"


def test_lists_keep_their_kind_and_depth():
    paras = markdown_paragraphs("* a\n    * nested\n* b\n\nsplit\n\n1. one\n2. two\n")
    assert [(p.list_kind, p.level, p.runs[0].text) for p in paras] == [
        ("ul", 0, "a"),
        ("ul", 1, "nested"),
        ("ul", 0, "b"),
        ("", 0, "split"),
        ("ol", 0, "one"),
        ("ol", 0, "two"),
    ]


def test_inline_formatting_becomes_run_formatting():
    (para,) = markdown_paragraphs("a **b** *c* `d` [e](http://x.test)\n")
    flags = [(r.text, r.bold, r.italic, r.code, r.href) for r in para.runs]
    assert flags == [
        ("a ", False, False, False, None),
        ("b", True, False, False, None),
        (" ", False, False, False, None),
        ("c", False, True, False, None),
        (" ", False, False, False, None),
        ("d", False, False, True, None),
        (" ", False, False, False, None),
        ("e", False, False, False, "http://x.test"),
    ]


def test_code_block_is_one_monospaced_paragraph_per_line():
    paras = markdown_paragraphs("```\nline one\n  line two\n```\n")
    assert [p.runs[0].text for p in paras] == ["line one", "  line two"]
    assert all(p.code and p.runs[0].code for p in paras)


def test_table_rows_are_flattened_to_paragraphs():
    paras = markdown_paragraphs("| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert ["".join(r.text for r in p.runs) for p in paras] == ["a | b", "1 | 2"]


def _export(tmp_path, text):
    out = tmp_path / "deck.pptx"
    export_pptx(parse_deck(text), out)
    return Presentation(str(out))


def test_slides_use_the_stock_layouts_and_carry_notes(tmp_path):
    prs = _export(
        tmp_path,
        "# Welcome\n\n## Tagline\n\n<!-- voice: hello there -->\n\n"
        "# Points\n\n* one\n* two\n\n"
        "# Two {: layout=columns }\n\n### L\n\nleft\n\n### R\n\nright\n",
    )
    title, content, columns = prs.slides
    assert [s.slide_layout.name for s in prs.slides] == [
        "Title Slide",
        "Title and Content",
        "Title Only",
    ]
    assert title.shapes.title.text == "Welcome"
    assert title.placeholders[1].text == "Tagline"
    assert title.notes_slide.notes_text_frame.text == "hello there"
    assert [p.text for p in content.placeholders[1].text_frame.paragraphs] == [
        "one",
        "two",
    ]
    boxes = [s.text_frame.text for s in columns.shapes if not s.is_placeholder]
    assert boxes == ["L\nleft", "R\nright"]


def test_unused_placeholders_are_removed(tmp_path):
    prs = _export(tmp_path, "# Thanks\n\n---\n\njust text\n")
    thanks, untitled = prs.slides
    assert len(thanks.placeholders) == 1
    assert [p.text for p in untitled.placeholders] == ["just text"]


def test_sample_deck_exports_and_deck_title_is_set(tmp_path):
    out = tmp_path / "preso.pptx"
    export_pptx(load_deck(SAMPLE), out)
    prs = Presentation(str(out))
    assert len(prs.slides) == 13
    assert prs.core_properties.title == "My Presentation"


def test_unknown_layout_is_rejected(tmp_path):
    with pytest.raises(DeckError, match="Slide 1: the pptx export has no layout"):
        export_pptx(parse_deck("# A {: layout=fancy }\n"), tmp_path / "x.pptx")
