"""Build a narrated MP4 from a rendered deck: stills per moment, edge-tts narration, ffmpeg."""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import imageio_ffmpeg
from playwright.async_api import Error as PlaywrightError

from slider.capture import Still, film
from slider.deck import DeckError
from slider.speech import Clip, Speaker, SpeechError, rate_percent
from slider.timeline import Shot, schedule

logger = logging.getLogger(__name__)


class VideoError(RuntimeError):
    """Raised when the video cannot be built."""


def _env(name: str, default: str) -> str:
    return os.getenv(name) or default


@dataclass(frozen=True)
class VideoSettings:
    """Video options, each overridable from the environment (see .env.example)."""

    width: int = field(default_factory=lambda: int(_env("SLIDER_VIDEO_WIDTH", "1920")))
    height: int = field(
        default_factory=lambda: int(_env("SLIDER_VIDEO_HEIGHT", "1080"))
    )
    fps: int = field(default_factory=lambda: int(_env("SLIDER_VIDEO_FPS", "30")))
    voice: str = field(
        default_factory=lambda: _env("SLIDER_VOICE", "en-US-AvaMultilingualNeural")
    )
    lead: float = field(default_factory=lambda: float(_env("SLIDER_LEAD", "0.4")))
    gap: float = field(default_factory=lambda: float(_env("SLIDER_GAP", "0.6")))
    hold: float = field(default_factory=lambda: float(_env("SLIDER_HOLD", "2.0")))
    audio_cache: Path = field(
        default_factory=lambda: Path(_env("SLIDER_AUDIO_CACHE", ".cache/audio"))
    )
    ffmpeg: str = field(default_factory=lambda: _env("SLIDER_FFMPEG", ""))


def find_ffmpeg(configured: str) -> str:
    """The configured ffmpeg, or else the one bundled with imageio-ffmpeg."""
    if not configured:
        return imageio_ffmpeg.get_ffmpeg_exe()
    found = shutil.which(configured)
    if found is None:
        raise VideoError(f"ffmpeg not found: {configured!r} (check SLIDER_FFMPEG)")
    return found


def concat_script(shots: list[Shot], stills: list[Still]) -> str:
    """An ffmpeg concat-demuxer script holding each still for its shot's duration."""
    lines = []
    for shot, still in zip(shots, stills, strict=True):
        lines += [f"file '{still.path.as_posix()}'", f"duration {shot.duration:.3f}"]
    # The demuxer ignores the last duration unless the final file is listed again.
    lines.append(f"file '{stills[-1].path.as_posix()}'")
    return "\n".join(lines) + "\n"


def mux_command(
    ffmpeg: str,
    script: Path,
    cues: list[tuple[float, Path]],
    fps: int,
    total: float,
    output: Path,
) -> list[str]:
    """ffmpeg call: the stills as steady video, each clip delayed to its offset.

    The output is cut at `total` seconds: the concat demuxer's handling of the final
    still's duration differs between ffmpeg versions, so it can't be trusted to end it.
    """
    args = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(script),
    ]
    filters = [f"[0:v]fps={fps},format=yuv420p[vout]"]
    maps = ["-map", "[vout]"]
    for i, (offset, path) in enumerate(cues, start=1):
        args += ["-i", str(path)]
        filters.append(f"[{i}:a]adelay={round(offset * 1000)}:all=1[a{i}]")
    if cues:
        labels = "".join(f"[a{i}]" for i in range(1, len(cues) + 1))
        filters.append(f"{labels}amix=inputs={len(cues)}:normalize=0[aout]")
        maps += ["-map", "[aout]", "-c:a", "aac", "-b:a", "160k"]
    return args + [
        "-filter_complex", ";".join(filters),
        *maps,
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
        "-t", f"{total:.3f}",
        "-movflags", "+faststart",
        str(output),
    ]  # fmt: skip


def make_video(
    page_html: str, deck_settings: dict[str, Any], output: Path, settings: VideoSettings
) -> None:
    """Render `page_html` (the deck's HTML output) to a narrated MP4 at `output`."""
    ffmpeg = find_ffmpeg(settings.ffmpeg)
    voice = deck_settings.get("voice") or {}
    if voice.get("engine", "edge-tts") != "edge-tts":
        raise DeckError(f"Unsupported voice engine {voice['engine']!r}: use edge-tts")

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        page_file = folder / "deck.html"
        page_file.write_text(page_html, encoding="utf-8")

        async def gather() -> tuple[list[Still], dict[str, Clip]]:
            """Screenshot every moment, then fetch a clip for each distinct line."""
            try:
                stills = await film(page_file, folder, settings.width, settings.height)
            except PlaywrightError as e:
                raise VideoError(f"Could not capture slides: {e}") from e
            clips: dict[str, Clip] = {}
            if not voice.get("enabled", True):
                return stills, clips
            speaker = Speaker(
                voice.get("speaker", settings.voice),
                rate_percent(float(voice.get("rate", 1.0))),
                settings.audio_cache,
                ffmpeg,
            )
            try:
                for text in dict.fromkeys(
                    s.moment.text for s in stills if s.moment.text
                ):
                    clips[text] = await speaker.clip(text)
            except SpeechError as e:
                raise VideoError(str(e)) from e
            return stills, clips

        stills, clips = asyncio.run(gather())
        shots = schedule(
            [s.moment for s in stills],
            {text: clip.duration for text, clip in clips.items()},
            settings.lead,
            settings.gap,
            settings.hold,
        )
        script = folder / "stills.txt"
        script.write_text(concat_script(shots, stills), encoding="utf-8")
        cues = [
            (shot.speech_at, clips[shot.moment.text].path)
            for shot in shots
            if shot.speech_at is not None
        ]
        output.parent.mkdir(parents=True, exist_ok=True)
        total = shots[-1].start + shots[-1].duration
        command = mux_command(ffmpeg, script, cues, settings.fps, total, output)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise VideoError(f"ffmpeg failed: {e.stderr.strip()}") from e

    logger.info("Video is %.1fs: %d moments, %d spoken", total, len(shots), len(cues))
