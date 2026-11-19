"""Narration clips from edge-tts, cached on disk by voice, rate and wording."""

import hashlib
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import edge_tts
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)


class SpeechError(RuntimeError):
    """Raised when a clip cannot be generated."""


@dataclass(frozen=True)
class Clip:
    path: Path
    duration: float  # seconds


def rate_percent(multiplier: float) -> str:
    """Turn a speed multiplier (1.0 = normal, 1.1 = 10% faster) into edge-tts's '+10%'."""
    return f"{round((multiplier - 1) * 100):+d}%"


class Speaker:
    def __init__(self, voice: str, rate: str, folder: Path, ffmpeg: str) -> None:
        self.voice = voice
        self.rate = rate
        self.folder = folder
        self.ffmpeg = ffmpeg

    async def clip(self, text: str) -> Clip:
        """The clip for `text`, fetched the first time and reused on later runs."""
        key = hashlib.sha1(
            f"trimmed|{self.voice}|{self.rate}|{text}".encode()
        ).hexdigest()[:16]
        path = self.folder / f"{key}.mp3"
        if not path.exists():
            self.folder.mkdir(parents=True, exist_ok=True)
            # Written aside first so an interrupted download never passes for a clip.
            partial = path.with_suffix(".part")
            try:
                await edge_tts.Communicate(text, self.voice, rate=self.rate).save(
                    str(partial)
                )
            except (edge_tts.exceptions.EdgeTTSException, aiohttp.ClientError) as e:
                raise SpeechError(f"edge-tts failed for {text[:40]!r}: {e}") from e
            self._trim(partial, path)
            partial.unlink()
            logger.info("Generated clip %s: %s", path.name, text[:60])
        return Clip(path, MP3(path).info.length)

    def _trim(self, source: Path, target: Path) -> None:
        """Cut the silence edge-tts leaves after the words, keeping a short tail, so pauses
        between moments are set by the timeline rather than by the clip."""
        trim = "silenceremove=start_periods=1:start_threshold=-45dB"
        command = [
            self.ffmpeg, "-y", "-loglevel", "error", "-i", str(source),
            "-af", f"areverse,{trim},areverse,apad=pad_dur=0.12",
            "-f", "mp3", str(target),
        ]  # fmt: skip
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise SpeechError(
                f"Could not trim {source.name}: {e.stderr.strip()}"
            ) from e
