import pytest

from slider.timeline import Moment, moments, schedule


def test_each_slide_then_each_step_becomes_a_moment():
    structure = [
        {"voice": " Hello \n", "steps": []},
        {"voice": "", "steps": ["first", ""]},
    ]
    assert moments(structure) == [
        Moment(0, 0, "Hello"),
        Moment(1, 0, ""),
        Moment(1, 1, "first"),
        Moment(1, 2, ""),
    ]


def test_spoken_moments_last_lead_plus_speech_plus_gap():
    shots = schedule(
        [Moment(0, 0, "hi"), Moment(0, 1, "there"), Moment(1, 0, "")],
        {"hi": 2.0, "there": 1.0},
        lead=0.5,
        gap=0.25,
        hold=3.0,
    )
    assert [(s.start, s.duration, s.speech_at) for s in shots] == [
        (0.0, 2.75, 0.5),
        (2.75, 1.75, 3.25),
        (4.5, 6.0, None),  # silent hold, plus the closing hold
    ]


def test_text_without_a_clip_is_held_silently():
    (shot,) = schedule([Moment(0, 0, "unspoken")], {}, lead=0.5, gap=0.5, hold=2.0)
    assert shot.speech_at is None
    assert shot.duration == pytest.approx(4.0)
