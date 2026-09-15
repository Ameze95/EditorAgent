from __future__ import annotations

from editoragent.analyzers.exposure import ExposureRaw
from editoragent.analyzers.motion import MotionRaw
from editoragent.analyzers.windowing import FrameMetrics, build_windows


def _frame(ts: float, sharpness_norm: float, exposure_norm: float) -> FrameMetrics:
    return FrameMetrics(
        timestamp_seconds=ts,
        sharpness_raw=sharpness_norm * 350.0,
        sharpness_norm=sharpness_norm,
        exposure=ExposureRaw(near_black_ratio=0.0, near_white_ratio=0.0, p05=10, p50=128, p95=240),
        exposure_norm=exposure_norm,
    )


def test_build_windows_overlap_and_scores() -> None:
    # 6 seconds of sharp+well-exposed frames sampled every 0.5s.
    timestamps = [i * 0.5 for i in range(12)]
    frames = [_frame(ts, sharpness_norm=0.9, exposure_norm=0.95) for ts in timestamps]

    windows = build_windows(frames, duration_seconds=6.0, window_seconds=3.0, overlap_ratio=0.5)

    assert len(windows) >= 2
    assert windows[0].start_seconds == 0.0
    assert windows[0].end_seconds == 3.0
    # 50% overlap -> second window starts at half the window length.
    assert windows[1].start_seconds == 1.5
    assert all(w.sharpness_norm > 0.7 for w in windows)
    assert all(w.motion_norm == 0.0 for w in windows)
    assert all(w.tracking_confidence == 1.0 for w in windows)
    assert all(w.stability_norm == 1.0 for w in windows)
    assert all("Nitidez alta" in " ".join(w.reasons) for w in windows)


def test_build_windows_flags_low_sharpness_as_penalty() -> None:
    frames = [_frame(ts, sharpness_norm=0.1, exposure_norm=0.95) for ts in [0.0, 0.5, 1.0]]

    windows = build_windows(frames, duration_seconds=3.0, window_seconds=3.0, overlap_ratio=0.5)

    assert windows
    assert any("desenfoque" in p for p in windows[0].penalties)


def test_build_windows_flags_low_tracking_confidence() -> None:
    frames = [_frame(ts, sharpness_norm=0.9, exposure_norm=0.95) for ts in [0.0, 0.5]]
    frames = [
        FrameMetrics(
            timestamp_seconds=frame.timestamp_seconds,
            sharpness_raw=frame.sharpness_raw,
            sharpness_norm=frame.sharpness_norm,
            exposure=frame.exposure,
            exposure_norm=frame.exposure_norm,
            motion=MotionRaw(response=0.1),
            motion_norm=frame.motion_norm,
        )
        for frame in frames
    ]

    windows = build_windows(frames, duration_seconds=1.0, window_seconds=1.0)

    assert any("tracking" in penalty for penalty in windows[0].penalties)


def test_build_windows_empty_input_returns_empty_list() -> None:
    assert build_windows([], duration_seconds=10.0) == []
