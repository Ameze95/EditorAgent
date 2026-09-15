"""Streaming frame sampling through FFmpeg's decoder and fps filter.

OpenCV random seeking was unreliable for the real DJI HEVC clip: it could
trigger invalid NAL errors and stall. FFmpeg decodes sequentially and emits
only the requested sample rate, while Python still processes one grayscale
frame at a time and never loads the clip into memory.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import Event

import numpy as np


class VideoOpenError(RuntimeError):
    """FFmpeg could not open or decode the video file."""


@dataclass(frozen=True)
class SampledFrame:
    timestamp_seconds: float
    gray: np.ndarray


def _output_dimensions(source_width: int, source_height: int) -> tuple[int, int]:
    output_width = min(640, source_width)
    output_height = max(2, round(source_height * output_width / source_width))
    if output_height % 2:
        output_height += 1
    return output_width, output_height


def _locate_ffmpeg() -> str:
    configured = os.environ.get("EDITORAGENT_FFMPEG")
    if configured and Path(configured).is_file():
        return configured
    from_path = shutil.which("ffmpeg")
    if from_path:
        return from_path
    winget_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    matches = sorted(winget_root.glob("Gyan.FFmpeg*/**/bin/ffmpeg.exe"))
    if matches:
        return str(matches[-1])
    raise VideoOpenError(
        "ffmpeg no está en el PATH. Instálalo junto con ffprobe antes de analizar vídeo."
    )


def sample_frames(
    video_path: Path,
    sample_fps: float,
    *,
    source_width: int = 640,
    source_height: int = 360,
        cancel_event: Event | None = None,
) -> Iterator[SampledFrame]:
    """Yield resized grayscale frames at `sample_fps` in timestamp order."""
    ffmpeg = _locate_ffmpeg()
    if sample_fps <= 0:
        raise ValueError("sample_fps debe ser mayor que cero.")
    width, height = _output_dimensions(source_width, source_height)
    args = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vf",
        f"fps={sample_fps},scale={width}:{height},format=gray",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]
    stderr_file = tempfile.TemporaryFile()
    process = subprocess.Popen(  # noqa: S603 - fixed args, no shell
        args, stdout=subprocess.PIPE, stderr=stderr_file
    )
    frame_size = width * height
    frame_index = 0
    try:
        assert process.stdout is not None
        while True:
            if cancel_event is not None and cancel_event.is_set():
                process.terminate()
                process.wait(timeout=2)
                return
            raw_frame = process.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break
            gray = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height, width)).copy()
            yield SampledFrame(
                timestamp_seconds=frame_index / sample_fps,
                gray=gray,
            )
            frame_index += 1
        return_code = process.wait()
        if return_code != 0:
            stderr_file.seek(0)
            stderr = stderr_file.read().decode("utf-8", errors="replace")
            raise VideoOpenError(f"FFmpeg no pudo decodificar {video_path}: {stderr.strip()}")
    finally:
        if process.poll() is None:
            process.kill()
        stdout_pipe = process.stdout
        if stdout_pipe:
            stdout_pipe.close()
        stderr_file.close()

