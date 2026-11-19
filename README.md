# slider

Slideshows as code. Write slides in Markdown, then get an HTML presentation, a narrated MP4 or a PowerPoint file from the same source.

## Install

```bash
make install                             # builds .venv, installs slider and Chromium
```

Chromium is only needed for `--format video`.

## Use

`python run.py` builds `.venv` on first run, then starts `python -m slider`. `./run.sh` does the same from a POSIX shell.

```bash
python run.py examples/preso                  # examples/preso.html, open it and present
python run.py examples/preso -f video         # examples/preso.mp4, narrated with edge-tts
python run.py examples/preso -f pptx          # examples/preso.pptx, for PowerPoint or Google Slides
python run.py examples/preso -t terminal      # use another theme
```

`examples/preso/` is a sample deck. Pass a folder of Markdown files (stitched together in name order) or a single file.

## Writing a deck

```markdown
---
title: My Talk
theme: light
---

# Welcome

## A short tagline

<!-- voice: Welcome. Today I'll show you how this works. -->

# Key points

* Every `# Heading` starts a new slide
* A `## Heading` straight after it is the subtitle

---

A slide with no title, started by a line of three dashes.

# Before and after {: layout=columns }

### Before

* Manual decks

### After

* Decks from Markdown
```

- `# Heading` starts a slide. `---` after a blank line starts one without a title.
- `## Heading` straight after the title is the subtitle.
- `<!-- voice: ... -->` is narration: never shown, spoken in order in the video, and kept as speaker notes in PowerPoint.
- `{: layout=columns }` on the title line turns each `###` section into a column.
- Front matter (first file only) sets `title`, `theme` and `voice` (`enabled`, `speaker`, `rate`).

## Themes

| Theme | Look |
|---|---|
| `default` | Dark blue stage with a blue and violet accent |
| `light` | The same layouts on white |
| `terminal` | Green on black, monospaced, with its own title layout |

A theme is a self-contained folder under `src/slider/themes/`: its page template, layouts and navigation script all live together, so it can be copied anywhere. `light` differs from `default` only in its colours, and `terminal` also has its own title layout.

To make your own, copy an existing theme into a folder of your choosing (this repo or not):

```bash
python run.py --new-theme acme --base terminal --themes-dir ~/github/slider-themes
python run.py my-deck -t acme --themes-dir ~/github/slider-themes
```

The copy needs nothing from this repo. Set `SLIDER_THEMES_DIR` in `.env` to avoid repeating `--themes-dir`.

## Configuration

Video options (resolution, voice, pacing, audio cache, ffmpeg) are environment variables. See `.env.example`.

## Working on slider with Claude Code

The repo carries two skills in `.claude/skills/`: `build-slide-deck` (writing decks) and `build-theme` (writing themes).

```bash
make test      # pytest
make lint      # ruff
make format    # black
```

## Not supported yet

Images, `.md.j2` templating, and step-by-step reveal. The PowerPoint export uses PowerPoint's stock 4:3 layouts, so a theme's look is not carried over.
