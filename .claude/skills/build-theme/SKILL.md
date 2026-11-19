---
name: build-theme
description: Create or change a slider theme, the folder of Jinja2 and CSS that styles an HTML slide deck and the video captured from it. Use whenever adding a theme, restyling slides, adding a slide layout, or debugging a theme that will not render or film, even if the user just says "make it look different" or "add a layout".
---

# Building a theme

A theme is a folder under `src/slider/themes/` (or under `SLIDER_THEMES_DIR` / `--themes-dir`). Create one with `--new-theme` (see "Starting a new theme"). Select it with `theme: mytheme` in the deck's front matter, or `-t mytheme`.

## How themes are put together

A theme is **self-contained**: the renderer reads every template from the theme's own folder and from nowhere else. Nothing is inherited from another folder, so a theme can be copied anywhere and still works.

```
src/slider/themes/
  default/
    base.html         the file the renderer loads; extends stage.html
    stage.html        the page: shell, all the CSS, every slide, navigation
    title.html        one file per layout; the file name is the layout name
    content.html
    columns.html
    slider.js         navigation script, included by stage.html
  light/              the same files, with base.html swapping the colours
  dark/ professional/ academic/ vanilla/   likewise: colours and fonts in base.html
  terminal/           the same files, with its own title.html and fonts
```

`base.html` is the file the renderer loads. The usual theme is only this:

```jinja
{% extends "stage.html" %}
{% block theme_css %}
  :root { --stage: #fff; --text: #1d2433; --accent: #2f6fed; }
{% endblock %}
```

`theme_css` is emitted at the end of the page's `<style>`, so it overrides the theme's own CSS. The colour and font variables to override are at the top of the theme's `stage.html`: `--bg`, `--stage`, `--text`, `--muted`, `--accent`, `--accent-2`, `--strong`, `--font`, `--mono`, `--speed`.

To change how a layout is built, edit that layout's file in the theme folder (as `terminal/title.html` does). A theme may also replace `stage.html` altogether, as long as it meets the contract below.

## Starting a new theme

Create one from an existing theme with `--new-theme`. It copies the base theme's folder, nothing else.

```bash
python run.py --new-theme acme                       # copy of `default`, into src/slider/themes/
python run.py --new-theme acme --base terminal       # start from another theme
python run.py --new-theme acme --themes-dir ~/github/slider-themes   # create it outside this repo
```

- The destination is `--themes-dir` (or `SLIDER_THEMES_DIR`), so a theme for another project or brand is created straight into its own folder, usually its own repo. The folder is created if it does not exist.
- `--base` is looked up in the destination folder first, then in the bundled themes, so a custom theme can be the base for the next one.
- It refuses to overwrite an existing theme and rejects names that contain a path separator.
- Then edit the copy: usually the colour variables in `theme_css` in `base.html`, sometimes a layout file.

## Themes kept outside this repo

Keep custom themes in their own folder (or repo), not in `src/slider/themes/`. Create them there with `--new-theme ... --themes-dir <folder>`, then use them the same way:

```bash
python run.py my-deck -t acme --themes-dir ~/github/slider-themes
```

or set it once in `.env`: `SLIDER_THEMES_DIR=C:/Users/you/github/slider-themes`, then `theme: acme` in the deck's front matter or `-t acme` is enough. Use a full path in `.env`: `~` is not expanded there.

- **The themes folder replaces the bundled one, it does not add to it.** With `--themes-dir` set, the bundled themes (`default`, `light`, `dark`, `professional`, `academic`, `vanilla`, `terminal`) are not available (`-t light` fails with "not found") unless you copy one in: `--new-theme light --base light --themes-dir <folder>`.
- **A copy is a snapshot.** When slider's own templates change (new layouts, fixes), nothing reaches existing copies. Keep your changes small and in `theme_css` so they are easy to re-apply to a fresh copy.
- The repo's `tests/test_render.py` only covers the bundled themes. Check an external theme by rendering a deck with it (the sample is `examples/preso`) and, for the video contract, with `-f video`.
- Assets must be self-contained in the page (inline CSS, data URIs): the output must still work from a `file://` URL, away from your themes folder.

## What each template receives

Jinja2 is configured with **StrictUndefined** (a misspelt variable is an error naming the slide), HTML autoescape, and `trim_blocks` / `lstrip_blocks`.

**Layout templates** (`title.html`, `content.html`, `columns.html`) render one slide's inner HTML. Variables: `slide` and `deck`.

| `slide.` | Holds |
|---|---|
| `number` | 1-based position |
| `layout` | The layout name |
| `title`, `subtitle` | Plain text, `""` when absent. Autoescaped |
| `body` | Markdown source. Pipe it through `\| md`. For `columns`, this is the text above the first column |
| `columns` | List of `{heading, body}` for the `columns` layout, otherwise empty |
| `voice` | Narration. Do not show it |

`deck` is the front matter mapping (`deck.title`, and so on). Use `deck.get('x', default)` for optional keys.

**The page template** (`base.html`, or `stage.html`) renders the whole page. Variables: `deck`, `slides`, `has_code` and `has_mermaid`, where each entry has `layout`, `voice` and `html` (the rendered layout template, already safe to output).

Filter available in every template: `md`, which renders Markdown to HTML (tables, fenced code and attr_list enabled). It is safe to output as is.

## Code highlighting and diagrams

`stage.html` loads highlight.js when the deck has a code block (`has_code`) and Mermaid when it has a diagram (`has_mermaid`), both from a CDN. A fenced ` ```mermaid ` block reaches the template as `<pre class="mermaid">`, which Mermaid replaces with an SVG. A theme extending `stage.html` gets this for free, and picks the light or dark look by overriding two blocks in `base.html`:

```jinja
{% block hljs_stylesheet %}<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.12.0/styles/github-dark.min.css">{% endblock %}
{% block mermaid_theme %}dark{% endblock %}
```

`default`, `dark` and `terminal` do this; the rest keep the light defaults (`github` and `default`). The video build waits for every `pre.mermaid` to gain `data-processed`, so a theme with its own page template must keep that class and let Mermaid process it.

## The contract that video capture and navigation rely on

Keep all of this or `--format video` fails with "Theme does not expose window.slider.show". Extending `stage.html` keeps it for free.

1. Every slide is an element with class `slide`, in order, carrying `data-voice="{{ slide.voice | trim }}"`.
2. `window.slider.show(slideIndex, step)` is defined: it shows slide `slideIndex` (0-based) fully settled. `step` is the number of `.step` items revealed on it; the shipped themes have none.
3. Optional reveal items have class `step` and optional `data-voice`. Capture reads them if present.
4. `.counter` and `.progress` exist if you keep `slider.js` (it writes to them).
5. If you write your own script, keep the keys, click and swipe behaviour of `slider.js` as shipped.

Capture is taken at 1920x1080 by default (`SLIDER_VIDEO_WIDTH` / `HEIGHT`) in headless Chromium after injecting a style that switches off all `transition` and `animation`. So:

- Animations are fine for the live page. They are removed for stills (the terminal theme's blinking cursor shows as a solid block).
- Size text relative to the stage, not the window. The stage is 16:9 with `container-type: size` and `font-size: 4cqh`, so everything scales with `em`. Follow that and the video matches the browser.
- The page must work from a `file://` URL and offline. No build step, no web server, no external fonts or scripts unless you accept video capture needing the network.

## Adding a layout

1. Add `<name>.html` to the theme folder. A layout is per theme: add it to each theme that should offer it.
2. A deck uses it with `# Title {: layout=name }`.
3. Add CSS for `.layout-<name>`: the page puts that class on each slide's section. Put it in the theme's `theme_css` block or its `stage.html`.
4. The slide splitter only fills `columns` for the `columns` layout. A new layout gets `title`, `subtitle`, `body` and `voice`. If it needs the content split in a new way, that is a change to `slides.py`, with tests, not a theme change.
5. A missing template fails with `Slide N: theme 'x' has no layout 'y'`.

The PowerPoint export ignores themes and only knows `title`, `content` and `columns`.

## Testing a theme

```bash
python run.py examples/preso -t mytheme -o .cache/try.html
python run.py examples/preso -t mytheme -f video -o .cache/try.mp4   # proves the contract holds
# add --themes-dir <folder> for a theme kept outside the repo
python -m pytest -q
```

`tests/test_render.py` renders the sample `examples/preso/` deck with every folder in `src/slider/themes/` that does not start with `_`, so a new theme is covered automatically. Open the HTML and look at a title slide, a content slide and a columns slide: tests cannot tell you it looks right.

## Checklist

1. `base.html` exists in the theme folder and extends `stage.html` (or provides the whole contract itself).
2. A template exists for `title`, `content` and `columns`, in the theme folder.
3. Text sizes are in `em` against the stage, not `px` against the window.
4. The page works opened straight from disk.
5. The video build runs for a short deck.
