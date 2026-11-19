from pathlib import Path

import pytest

from slider.deck import DeckError, load_deck, parse_deck
from slider.render import render_deck

THEMES = Path(__file__).parent.parent / "src" / "slider" / "themes"
SAMPLE = Path(__file__).parent.parent / "examples" / "preso"


THEME_NAMES = sorted(p.name for p in THEMES.iterdir() if p.is_dir())


@pytest.mark.parametrize("theme", THEME_NAMES)
def test_every_theme_renders_the_sample_deck(theme):
    deck = load_deck(SAMPLE)
    html = render_deck(deck, THEMES, theme)
    assert html.count('<section class="slide ') == len(deck["slides"])
    assert "layout-columns" in html and "layout-title" in html
    assert "window.slider" in html  # the navigation script the video capture needs


def test_a_theme_can_override_a_single_layout():
    deck = parse_deck("# Hello\n\n# Next\n\ntext\n")
    assert 'class="cursor"' in render_deck(deck, THEMES, "terminal")
    assert 'class="cursor"' not in render_deck(deck, THEMES, "light")


def test_body_markdown_is_rendered():
    html = render_deck(parse_deck("# T\n\n* a **bold** point\n"), THEMES)
    assert "<li>a <strong>bold</strong> point</li>" in html


def test_voice_is_carried_on_the_slide_and_not_shown_as_content():
    html = render_deck(parse_deck("# T\n\n<!-- voice: say this -->\n"), THEMES)
    assert 'data-voice="say this"' in html
    assert "<!--" not in html.split("<main")[1]


def test_titles_are_escaped():
    html = render_deck(parse_deck("# <script>x</script>\n"), THEMES)
    assert "&lt;script&gt;x&lt;/script&gt;" in html


def test_unknown_layout_names_the_slide():
    deck = parse_deck("# A\n\n# B {: layout=nope }\n")
    with pytest.raises(
        DeckError, match="Slide 2: theme 'default' has no layout 'nope'"
    ):
        render_deck(deck, THEMES)


def test_unknown_theme_is_rejected():
    deck = parse_deck("---\ntheme: missing\n---\n# A\n")
    with pytest.raises(DeckError, match="Theme 'missing' not found"):
        render_deck(deck, THEMES)


MERMAID_DECK = "# D\n\n```mermaid\ngraph TD; A-->B\n```\n"
CODE_DECK = "# C\n\n```python\nx = 1\n```\n"


def test_mermaid_block_becomes_a_diagram_and_loads_mermaid():
    html = render_deck(parse_deck(MERMAID_DECK), THEMES)
    assert '<pre class="mermaid">graph TD; A--&gt;B' in html
    assert "mermaid.min.js" in html and "language-mermaid" not in html
    assert "highlight.min.js" not in html


def test_code_block_loads_the_highlighter_but_not_mermaid():
    html = render_deck(parse_deck(CODE_DECK), THEMES)
    assert '<pre><code class="language-python">' in html
    assert "highlight.min.js" in html and "mermaid.min.js" not in html


def test_a_plain_deck_loads_no_scripts_from_the_network():
    assert "cdn.jsdelivr.net" not in render_deck(parse_deck("# T\n\n* a\n"), THEMES)


@pytest.mark.parametrize(
    "theme, dark",
    [("default", True), ("dark", True), ("terminal", True), ("light", False)],
)
def test_code_and_diagram_styles_follow_the_theme(theme, dark):
    html = render_deck(parse_deck(CODE_DECK + "\n" + MERMAID_DECK), THEMES, theme)
    assert ("github-dark.min.css" in html) == dark
    assert ('theme: "dark"' in html) == dark
