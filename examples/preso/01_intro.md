---
title: My Presentation    # defaults to the first slide's title
author: Your Name         # PowerPoint file properties only
theme: default            # default, light or terminal; -t on the command line overrides it
voice:                    # narration settings, used by --format video
  enabled: true           # false: silent video, each slide held SLIDER_HOLD seconds
  engine: edge-tts        # only edge-tts for now
  speaker: en-US-AvaMultilingualNeural   # any `edge-tts --list-voices` name
  rate: 1.0               # speed multiplier: 1.1 is 10% faster
---

# My Slide title

## A short tagline

<!-- voice: Welcome. Today I'll walk you through how this tool works. -->

# Key points

* Every `# Heading` starts a new slide
* A `## Heading` straight after it is the subtitle
* Lists, **bold text**, code and tables all work

<!-- voice: There are two things to cover here. -->
<!-- voice: First, how slides are split. Second, how narration is written. -->

---

A slide with no title, started by a line of three dashes.

<!-- voice: A slide needs no title. A line of dashes starts one without. -->
