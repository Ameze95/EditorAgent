from __future__ import annotations

import pytest

from editoragent.infrastructure.ffprobe import NoVideoStreamError, normalize_probe


def test_normalize_valid_avata2_clip(load_ffprobe_fixture):
    raw = load_ffprobe_fixture("avata2_valid.json")

    metadata = normalize_probe(raw)

    assert metadata.codec == "hevc"
    assert metadata.width == 3840
    assert metadata.height == 2160
    assert metadata.pixel_format == "yuv420p10le"
    assert metadata.fps_num == 60000
    assert metadata.fps_den == 1001
    assert metadata.is_vfr is False
    assert metadata.duration_seconds == pytest.approx(12.345)
    assert metadata.color_metadata["color_transfer"] == "arib-std-b67"
    assert metadata.capture_time is not None
    assert metadata.capture_time.year == 2026


def test_normalize_raises_without_video_stream(load_ffprobe_fixture):
    raw = load_ffprobe_fixture("no_video_stream.json")

    with pytest.raises(NoVideoStreamError):
        normalize_probe(raw)
