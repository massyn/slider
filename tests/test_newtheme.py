from pathlib import Path

import pytest

from slider.deck import DeckError, load_deck
from slider.newtheme import create_theme
from slider.render import render_deck

BUNDLED = Path(__file__).parent.parent / "src" / "slider" / "themes"
SAMPLE = Path(__file__).parent.parent / "examples" / "preso"


def test_new_theme_is_a_complete_copy_that_renders_on_its_own(tmp_path):
    target = create_theme("acme", "terminal", tmp_path, BUNDLED)
    assert sorted(p.name for p in target.iterdir()) == sorted(
        p.name for p in (BUNDLED / "terminal").iterdir()
    )
    assert [p.name for p in tmp_path.iterdir()] == ["acme"]

    deck = load_deck(SAMPLE)
    html = render_deck(deck, tmp_path, "acme")
    assert html.count('<section class="slide ') == len(deck["slides"])
    assert 'class="cursor"' in html


def test_a_custom_theme_can_be_the_base(tmp_path):
    create_theme("one", "light", tmp_path, BUNDLED)
    (tmp_path / "one" / "base.html").write_text("custom")
    create_theme("two", "one", tmp_path, BUNDLED)
    assert (tmp_path / "two" / "base.html").read_text() == "custom"


@pytest.mark.parametrize("name", ["", "..", "../x", "a/b"])
def test_invalid_names_are_rejected(tmp_path, name):
    with pytest.raises(DeckError, match="not a valid theme name"):
        create_theme(name, "default", tmp_path, BUNDLED)


def test_existing_theme_is_never_overwritten(tmp_path):
    create_theme("acme", "default", tmp_path, BUNDLED)
    with pytest.raises(DeckError, match="already exists"):
        create_theme("acme", "light", tmp_path, BUNDLED)


def test_unknown_base_is_rejected(tmp_path):
    with pytest.raises(DeckError, match="Base theme 'missing'"):
        create_theme("acme", "missing", tmp_path, BUNDLED)
    assert not (tmp_path / "acme").exists()
