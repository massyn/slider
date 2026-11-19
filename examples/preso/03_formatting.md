# Text styles

Ordinary paragraphs support **bold**, *italic*, `inline code` and [links](https://github.com/massyn/slider).

<!-- voice: Paragraphs support bold, italic, inline code and links. -->

# Lists

1. Numbered lists keep their order
2. Bullet lists can nest:
    * like this
    * and this
3. Everything on a slide appears at once

<!-- voice: Lists can be numbered or bulleted, and they can nest. -->

# Code

```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```

<!-- voice: Fenced code blocks are shown as written. -->

# Tables

| Output | Command | Needs |
|---|---|---|
| HTML | `slider deck` | Nothing |
| Video | `slider deck -f video` | Chromium and a network |
| PowerPoint | `slider deck -f pptx` | Nothing |

<!-- voice: Tables work too. In PowerPoint they are flattened to plain lines. -->
