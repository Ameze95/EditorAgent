"""Safe ffprobe subprocess adapter and JSON metadata normalization.

Rules followed (see docs/ARCHITECTURE.md §6):
- Never build a shell string; always pass an argument list to subprocess.
- Never assume a fixed FPS; use ffprobe's rational frame rates.
- Distinguish "ffprobe not installed", "process failed" and
  "no readable video stream" as different, explicit failure modes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class FfprobeNotFoundError(RuntimeError):
    """ffprobe binary is not available on PATH."""


class FfprobeExecutionError(RuntimeError):
    """ffprobe ran but exited with an error for this file."""

    def __init__(self, path: Path, stderr: str) -> None:
        self.path = path
        self.stderr = stderr
        super().__init__(f"ffprobe failed for {path}: {stderr.strip()}")


class NoVideoStreamError(RuntimeError):
    """ffprobe succeeded but the file has no readable video stream."""


@dataclass(frozen=True)
class ProbeMetadata:
    duration_seconds: float | None
    fps_num: int | None
    fps_den: int | None
    is_vfr: bool | None
    width: int | None
    height: int | None
    codec: str | None
    pixel_format: str | None
    color_metadata: dict[str, str]
    capture_time: datetime | None


def locate_ffprobe() -> str:
    configured = os.environ.get("EDITORAGENT_FFPROBE")
    if configured and Path(configured).is_file():
        return configured
    from_path = shutil.which("ffprobe")
    if from_path:
        return from_path
    winget_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    matches = sorted(winget_root.glob("Gyan.FFmpeg*/**/bin/ffprobe.exe"))
    if matches:
        return str(matches[-1])
    raise FfprobeNotFoundError(
        "ffprobe no está en el PATH. Instálalo (p. ej. "
        "'winget install --id Gyan.FFmpeg -e') y reinicia la terminal."
    )


def run_ffprobe(video_path: Path) -> dict[str, Any]:
    """Invoke ffprobe on a single file and return the parsed JSON payload."""
    binary = locate_ffprobe()
    args = [
        binary,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]
    result = subprocess.run(  # noqa: S603 - fixed binary, argument list, no shell
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise FfprobeExecutionError(video_path, result.stderr)
    payload: dict[str, Any] = json.loads(result.stdout)
    return payload


def _parse_rational(value: str | None) -> tuple[int, int] | None:
    if not value or "/" not in value:
        return None
    num_str, den_str = value.split("/", 1)
    try:
        num, den = int(num_str), int(den_str)
    except ValueError:
        return None
    if den == 0:
        return None
    return num, den


def _parse_capture_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_probe(raw: dict[str, Any]) -> ProbeMetadata:
    """Translate raw ffprobe JSON into normalized, provenance-friendly fields."""
    streams = raw.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video_stream is None:
        raise NoVideoStreamError("No se encontró ningún stream de vídeo legible.")

    fmt = raw.get("format", {})

    duration_raw = video_stream.get("duration") or fmt.get("duration")
    duration_seconds = float(duration_raw) if duration_raw is not None else None

    r_frame_rate = _parse_rational(video_stream.get("r_frame_rate"))
    avg_frame_rate = _parse_rational(video_stream.get("avg_frame_rate"))
    fps = r_frame_rate or avg_frame_rate
    fps_num, fps_den = fps if fps else (None, None)

    is_vfr: bool | None = None
    if r_frame_rate and avg_frame_rate:
        is_vfr = r_frame_rate != avg_frame_rate

    color_metadata = {
        key: video_stream[key]
        for key in ("color_range", "color_space", "color_transfer", "color_primaries")
        if video_stream.get(key)
    }

    capture_time = _parse_capture_time(fmt.get("tags", {}).get("creation_time"))

    return ProbeMetadata(
        duration_seconds=duration_seconds,
        fps_num=fps_num,
        fps_den=fps_den,
        is_vfr=is_vfr,
        width=video_stream.get("width"),
        height=video_stream.get("height"),
        codec=video_stream.get("codec_name"),
        pixel_format=video_stream.get("pix_fmt"),
        color_metadata=color_metadata,
        capture_time=capture_time,
    )
