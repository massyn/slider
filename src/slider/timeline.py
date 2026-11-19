"""The video's timeline: which moment of the deck is on screen, for how long, and when
its narration plays.

A moment is one state of the slider: a slide with its first `step` items revealed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Moment:
    slide: int  # 0-based slide index
    step: int  # how many .step items are revealed
    text: str  # narration for this moment ("" for none)


@dataclass(frozen=True)
class Shot:
    moment: Moment
    start: float  # seconds into the video
    duration: float
    speech_at: float | None  # when narration starts, or None for a silent moment


def moments(structure: list[dict]) -> list[Moment]:
    """Every moment of the deck in order, from the page's slides and their step voices.

    `structure` is one {"voice": str, "steps": [str, ...]} per slide, read from the page.
    """
    result = []
    for index, slide in enumerate(structure):
        result.append(Moment(index, 0, slide["voice"].strip()))
        result += [
            Moment(index, step, voice.strip())
            for step, voice in enumerate(slide["steps"], 1)
        ]
    return result


def schedule(
    moments: list[Moment],
    lengths: dict[str, float],
    lead: float,
    gap: float,
    hold: float,
) -> list[Shot]:
    """Lay the moments end to end. A spoken moment lasts lead + speech + gap; a silent one
    (no text, or text with no clip in `lengths`) is held for `hold` seconds. The last
    moment is held a further `hold` so the video doesn't end on the final word.
    """
    shots = []
    clock = 0.0
    for i, moment in enumerate(moments):
        length = lengths.get(moment.text) if moment.text else None
        if length is None:
            duration, speech_at = hold, None
        else:
            duration, speech_at = lead + length + gap, clock + lead
        if i == len(moments) - 1:
            duration += hold
        shots.append(Shot(moment, clock, duration, speech_at))
        clock += duration
    return shots
