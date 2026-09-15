from __future__ import annotations

from pathlib import Path

from editoragent.analyzers.frame_sampler import sample_frames


def test_sample_frames_yields_increasing_timestamps(make_synthetic_video) -> None:
    video_path: Path = make_synthetic_video(fps=10, seconds=2.0)

    frames = list(sample_frames(video_path, sample_fps=4.0))

    assert len(frames) >= 6  # ~4fps * 2s, allowing for rounding at the tail
    timestamps = [f.timestamp_seconds for f in frames]
    assert timestamps == sorted(timestamps)
    assert all(t >= 0 for t in timestamps)
