import pytest

from slider.errors import DeckError
from slider.slides import split_slides


def test_h1_starts_a_slide_and_is_its_title():
    slides = split_slides("# One\n\ntext\n\n# Two\n\nmore\n")
    assert [s["title"] for s in slides] == ["One", "Two"]
    assert [s["number"] for s in slides] == [1, 2]
    assert slides[0]["body"] == "text"


def test_title_with_only_a_subtitle_is_a_title_slide():
    (slide,) = split_slides("# Welcome\n\n## A tagline\n")
    assert (slide["layout"], slide["subtitle"], slide["body"]) == (
        "title",
        "A tagline",
        "",
    )


def test_title_alone_is_a_title_slide():
    assert split_slides("# Thanks\n")[0]["layout"] == "title"


def test_later_h2_is_content_not_a_subtitle():
    (slide,) = split_slides("# Title\n\n## Sub\n\ntext\n\n## Another\n\nmore\n")
    assert slide["subtitle"] == "Sub"
    assert slide["layout"] == "content"
    assert slide["body"] == "text\n\n## Another\n\nmore"


def test_h2_after_other_content_is_not_a_subtitle():
    (slide,) = split_slides("# Title\n\nintro\n\n## Heading\n")
    assert slide["subtitle"] == ""
    assert "## Heading" in slide["body"]


def test_triple_dash_after_a_blank_line_starts_an_untitled_slide():
    slides = split_slides("# One\n\ntext\n\n---\n\nuntitled\n")
    assert [s["title"] for s in slides] == ["One", ""]
    assert slides[1]["body"] == "untitled"


def test_setext_underline_is_not_a_slide_break():
    (slide,) = split_slides("# One\n\nSub heading\n---\n\ntext\n")
    assert "Sub heading\n---" in slide["body"]


def test_headings_and_breaks_inside_code_fences_are_left_alone():
    text = "# One\n\n```bash\n# a comment\n\n---\n```\n\n~~~\n# also code\n~~~\n"
    (slide,) = split_slides(text)
    assert "# a comment" in slide["body"] and "# also code" in slide["body"]


def test_voice_notes_are_removed_and_kept_in_order():
    (slide,) = split_slides(
        "# One\n\n<!-- voice: first\nline -->\n\ntext\n\n<!-- voice: second -->\n"
    )
    assert slide["voice"] == "first line\n\nsecond"
    assert slide["body"] == "text"


def test_voice_comment_inside_a_code_fence_is_kept():
    (slide,) = split_slides("# One\n\n```html\n<!-- voice: no -->\n```\n")
    assert slide["voice"] == ""
    assert "<!-- voice: no -->" in slide["body"]


def test_voice_between_title_and_subtitle_does_not_hide_the_subtitle():
    (slide,) = split_slides("# One\n<!-- voice: hi -->\n## Sub\n")
    assert slide["subtitle"] == "Sub"


def test_layout_attribute_is_read_from_the_title_line():
    (slide,) = split_slides(
        "# Two up {: layout=columns }\n\n### A\n\na\n\n### B\n\nb\n"
    )
    assert slide["title"] == "Two up"
    assert slide["layout"] == "columns"
    assert slide["columns"] == [
        {"heading": "A", "body": "a"},
        {"heading": "B", "body": "b"},
    ]


def test_text_above_the_first_column_is_kept_as_an_intro():
    (slide,) = split_slides("# T {: layout=columns }\n\nintro\n\n### A\n\na\n")
    assert slide["body"] == "intro"


@pytest.mark.parametrize(
    "text, message",
    [
        ("# T {: layout=columns }\n\nno sections\n", "needs ### sections"),
        ("# T {: colour=red }\n", "unknown attribute 'colour'"),
        ("# One\n\n---\n\n<!-- voice: alone -->\n", "Slide 2: nothing but narration"),
    ],
)
def test_invalid_slides_are_rejected(text, message):
    with pytest.raises(DeckError, match=message):
        split_slides(text)


def test_blank_input_has_no_slides():
    assert split_slides("\n\n   \n") == []
