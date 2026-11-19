import pytest

from slider.deck import DeckError, find_markdown_files, load_deck, parse_deck


def test_front_matter_gives_deck_settings():
    deck = parse_deck("---\ntitle: Talk\ntheme: dark\n---\n\n# One\n")
    assert deck["deck"] == {"title": "Talk", "theme": "dark"}
    assert [s["title"] for s in deck["slides"]] == ["One"]


def test_title_defaults_to_the_first_slide_title():
    assert parse_deck("# One\n\n# Two\n")["deck"] == {"title": "One"}


def test_leading_triple_dash_without_front_matter_is_a_slide_break():
    deck = parse_deck("---\n\nuntitled\n\n# One\n")
    assert [s["title"] for s in deck["slides"]] == ["", "One"]


@pytest.mark.parametrize(
    "text, message",
    [
        ("---\n- a\n- b\n---\n# One\n", "must be a mapping"),
        ("---\nkey: [oops\n---\n# One\n", "Invalid front matter"),
        ("   \n", "No slides found"),
    ],
)
def test_invalid_decks_are_rejected(text, message):
    with pytest.raises(DeckError, match=message):
        parse_deck(text)


def test_folder_files_are_stitched_in_name_order_skipping_underscored(tmp_path):
    (tmp_path / "02_b.md").write_text("# Second\n", encoding="utf-8")
    (tmp_path / "01_a.md").write_text("---\ntitle: T\n---\n# First\n", encoding="utf-8")
    (tmp_path / "_notes.md").write_text("# Hidden\n", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("# Not markdown\n", encoding="utf-8")

    deck = load_deck(tmp_path)

    assert [s["title"] for s in deck["slides"]] == ["First", "Second"]
    assert deck["deck"]["title"] == "T"


def test_single_file_is_a_deck(tmp_path):
    path = tmp_path / "talk.md"
    path.write_text("# Only\n", encoding="utf-8")
    assert find_markdown_files(path) == [path]


def test_missing_and_empty_sources_are_rejected(tmp_path):
    with pytest.raises(DeckError, match="not a file or a folder"):
        find_markdown_files(tmp_path / "nope")
    with pytest.raises(DeckError, match="No Markdown files"):
        find_markdown_files(tmp_path)
