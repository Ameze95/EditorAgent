"""Create and cache low-resolution analysis proxies outside source folders."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from editoragent.analyzers.frame_sampler import _locate_ffmpeg
from editoragent.domain.models import Clip

PROXY_VERSION = "0.1.0"
DEFAULT_PROXY_WIDTH = 640


class ProxyGenerationError(RuntimeError):
    """FFmpeg could not create an analysis proxy."""


def proxy_path(project_root: Path, clip: Clip, width: int = DEFAULT_PROXY_WIDTH) -> Path:
    return project_root / "proxies" / f"{clip.id}_{width}.mp4"


def _manifest_path(proxy: Path) -> Path:
    return proxy.with_suffix(".json")


def _is_current(proxy: Path, clip: Clip, width: int) -> bool:
    manifest = _manifest_path(proxy)
    if not proxy.is_file() or not manifest.is_file():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    proxy_version = data.get("proxy_version")
    source_fingerprint = data.get("source_fingerprint")
    proxy_width = data.get("width")
    return bool(
        proxy_version == PROXY_VERSION
        and source_fingerprint == clip.source_fingerprint
        and proxy_width == width
    )


def ensure_analysis_proxy(
    project_root: Path,
    clip: Clip,
    source_path: Path,
    *,
    width: int = DEFAULT_PROXY_WIDTH,
) -> Path:
    """Return a current proxy, creating it atomically when needed."""
    destination = proxy_path(project_root, clip, width)
    if _is_current(destination, clip, width):
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{clip.id}_", suffix=".mp4", dir=destination.parent
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    ffmpeg = _locate_ffmpeg()
    args = [
        ffmpeg,
        "-v",
        "error",
        "-y",
        "-i",
        str(source_path),
        "-map",
        "0:v:0",
        "-vf",
        f"scale={width}:-2:flags=fast_bilinear",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "28",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(temporary_path),
    ]
    try:
        result = subprocess.run(  # noqa: S603 - fixed args, no shell
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ProxyGenerationError(
                f"FFmpeg no pudo crear el proxy de {source_path}: {result.stderr.strip()}"
            )
        temporary_path.replace(destination)
        _manifest_path(destination).write_text(
            json.dumps(
                {
                    "proxy_version": PROXY_VERSION,
                    "source_fingerprint": clip.source_fingerprint,
                    "source_path": str(source_path),
                    "width": width,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return destination
    finally:
        temporary_path.unlink(missing_ok=True)
