from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ffprobe"


@pytest.fixture
def load_ffprobe_fixture():
    def _load(name: str) -> dict:
        return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))

    return _load


@pytest.fixture
def make_synthetic_video(tmp_path: Path):
    """Write a tiny real .mp4 with a sharp first half and a blurred second half."""

    def _make(name: str = "synthetic.mp4", fps: int = 10, seconds: float = 2.0) -> Path:
        width, height = 320, 240
        path = tmp_path / name
        writer = cv2.VideoWriter(
            str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )
        frame_count = int(fps * seconds)
        idx = np.arange(width)
        checkerboard = (((idx // 8)[None, :] + (np.arange(height) // 8)[:, None]) % 2 * 255).astype(
            np.uint8
        )
        sharp_bgr = cv2.cvtColor(checkerboard, cv2.COLOR_GRAY2BGR)
        blurred_bgr = cv2.GaussianBlur(sharp_bgr, (25, 25), 0)
        for i in range(frame_count):
            frame = sharp_bgr if i < frame_count // 2 else blurred_bgr
            writer.write(frame)
        writer.release()
        return path

    return _make
