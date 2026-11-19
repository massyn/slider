from pathlib import Path

import pytest

from slider.capture import Still
from slider.speech import rate_percent
from slider.timeline import Moment, Shot
from slider.video import concat_script, mux_command


@pytest.mark.parametrize(
    "multiplier, expected", [(1.0, "+0%"), (1.1, "+10%"), (0.85, "-15%")]
)
def test_rate_multiplier_becomes_edge_tts_percentage(multiplier, expected):
    assert rate_percent(multiplier) == expected


def test_concat_script_holds_each_still_and_repeats_the_last():
    moments = [Moment(0, 0, ""), Moment(0, 1, "")]
    stills = [Still(m, Path(f"/tmp/{i}.png")) for i, m in enumerate(moments)]
    shots = [Shot(moments[0], 0.0, 1.5, None), Shot(moments[1], 1.5, 2.25, None)]
    assert concat_script(shots, stills) == (
        "file '/tmp/0.png'\nduration 1.500\n"
        "file '/tmp/1.png'\nduration 2.250\n"
        "file '/tmp/1.png'\n"
    )


def test_mux_delays_each_clip_and_mixes_them():
    command = mux_command(
        "ffmpeg",
        Path("s.txt"),
        [(0.4, Path("a.mp3")), (3.25, Path("b.mp3"))],
        30,
        12.5,
        Path("out.mp4"),
    )
    graph = command[command.index("-filter_complex") + 1]
    assert "[1:a]adelay=400:all=1[a1]" in graph
    assert "[2:a]adelay=3250:all=1[a2]" in graph
    assert "[a1][a2]amix=inputs=2:normalize=0[aout]" in graph
    assert command[command.index("-t") + 1] == "12.500"
    assert command[-1] == "out.mp4"


def test_mux_without_narration_has_no_audio_track():
    command = mux_command("ffmpeg", Path("s.txt"), [], 30, 5.0, Path("out.mp4"))
    assert "[aout]" not in command
    assert "amix" not in " ".join(command)
