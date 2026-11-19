---
name: build-slide-deck
description: Write a slide deck for slider, the CLI that turns Markdown files into an HTML presentation, a narrated MP4 or a PowerPoint file. Use whenever creating or editing slides, writing narration, choosing a slide layout, or rendering a deck in this repo, even if the user just says "make a presentation" or "add a slide".
---

# Building a slide deck

A deck is a Markdown file, or a folder of them. Nothing else is needed.

## Files

- A folder's `.md` files (found recursively) are stitched together in name order, so number them: `01_intro.md`, `02_demo.md`.
- Files whose name starts with `_` are skipped. Use that for notes and drafts.
- A single `.md` file works too. Slides do not have to match files: one file can hold many slides.
- Optional YAML front matter goes at the very top of the **first** file only:

```yaml
---
title: My Presentation      # defaults to the first slide's title
author: Phil Massyn         # PowerPoint file properties only
theme: default              # default, light, dark, professional, academic, vanilla or terminal; `-t` on the command line overrides it
voice:                      # used by --format video only
  enabled: true             # false: silent video, each slide held SLIDER_HOLD seconds
  engine: edge-tts          # the only engine
  speaker: en-US-AvaMultilingualNeural   # any `edge-tts --list-voices` name
  rate: 1.0                 # 1.1 is 10% faster
---
```

## Slide rules

| Markdown | Meaning |
|---|---|
| `# Heading` | Starts a slide and is its title |
| `---` on its own line, after a blank line | Starts a slide with no title |
| `## Heading` straight after the title | The subtitle |
| `## Heading` anywhere else | An ordinary heading inside the slide |
| `### Heading` | Ordinary content, or a column (see below) |
| `<!-- voice: ... -->` | Narration: never shown, spoken in order |

- `---` directly under a line of text is a normal heading underline, not a slide break. Leave a blank line before it.
- Headings, `---` and voice comments inside fenced code blocks are left alone.
- Content is ordinary Markdown: paragraphs, lists, bold, italic, inline code, links, fenced code, tables.
- A fenced block with a language (` ```python `) is syntax highlighted. A block marked ` ```mermaid ` is drawn as a diagram. Both load their libraries from a CDN (highlight.js and Mermaid), and only when the deck uses them, so the page needs network access to show them; a deck with neither works offline.

## Layouts

Most slides need no layout. It is inferred:

- **`title`**: a slide with only a title (and subtitle) and no body.
- **`content`**: anything else.
- **`columns`**: must be asked for, by putting `{: layout=columns }` at the end of the title line. Each `### Heading` section becomes one column. Text above the first `###` is shown above the columns. A columns slide with no `###` section is an error.

```markdown
# Before and after {: layout=columns }

### Before

* Manual decks

### After

* Decks from Markdown
```

`layout` is the only attribute allowed. Any other `key=value` is an error, so typos are caught. The layout name must exist in the theme (see the `build-theme` skill), and the PowerPoint export only knows `title`, `content` and `columns`.

## Narration

- Use as many `<!-- voice: ... -->` comments as you like on a slide. They are joined, in order, into one clip played when the slide appears.
- Write for the ear: short sentences, numbers and acronyms spelt out the way they should sound ("S-A-S-T", "twenty twenty-six").
- Wording changes regenerate that clip; unchanged text reuses the cache in `.cache/audio`.
- The narration is not shown in the HTML. In PowerPoint it becomes the speaker notes.
- There is no step-by-step reveal and no per-bullet narration: everything on a slide appears at once.

## Rendering

```bash
./run.sh examples/preso                       # preso.html next to the folder, to present
./run.sh examples/preso -f video              # preso.mp4, narrated with edge-tts
./run.sh examples/preso -f pptx               # preso.pptx, for PowerPoint or Google Slides
./run.sh examples/preso -o out/talk.html      # explicit output file
./run.sh examples/preso -t other              # use a different theme
```

- `make run`, `make video`, `make test`, `make lint`, `make format` wrap the common ones.
- **HTML:** open it and present (code highlighting and diagrams need network access). Right, Space, Enter or PageDown for next; Left or PageUp for back; Home and End; `F` for fullscreen. Click the right two thirds to go forward, the left third to go back. Swipe on touch screens.
- **Video:** needs Chromium (`python -m playwright install chromium`) and a network connection for the first narration of each line, and for Mermaid diagrams. A diagram with a syntax error stops the build. Video options live in `.env` (see `.env.example`).
- **PowerPoint:** uses PowerPoint's stock layouts, so the theme's look is not carried over. Titles, subtitles, lists, bold, italic, links, code (as monospaced text, unhighlighted), tables (flattened to `a | b` lines) and narration (speaker notes) survive. Restyle in Slide Master. The slides are 4:3.

## Not supported yet

Images, PowerPoint diagrams (a Mermaid block comes through as its source text), `.md.j2` templating, and reveal steps. Do not invent syntax for them.

## Checklist before saying a deck is done

1. Every slide starts with `# `, or `---` if it should have no title.
2. A `columns` slide has `### ` sections.
3. Run `./run.sh <deck>` and confirm it reports the slide count you expect.
4. Run `python -m pytest -q` if you changed any code.
