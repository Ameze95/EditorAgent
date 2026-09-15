from __future__ import annotations

from editoragent.analyzers.segments import SegmentConfig, build_segments, preliminary_score
from editoragent.analyzers.windowing import WindowMetrics


def _window(start: float, score: float = 0.9) -> WindowMetrics:
    return WindowMetrics(
        start_seconds=start,
        end_seconds=start + 2.0,
        frame_count=8,
        sharpness_norm=score,
        exposure_norm=score,
        motion_norm=0.2,
        direction_coherence=1.0,
        jerk_norm=0.0,
        tracking_confidence=1.0,
        stability_norm=1.0,
        reasons=["Nitidez alta"],
        penalties=[],
    )


def test_preliminary_score_rewards_technical_quality() -> None:
    assert preliminary_score(_window(0.0, 0.95)) > preliminary_score(_window(0.0, 0.5))


def test_build_segments_preserves_natural_length_and_applies_handles() -> None:
    windows = [_window(start) for start in (0.0, 2.0, 4.0)]

    segments = build_segments(
        windows,
        clip_duration_seconds=8.0,
        config=SegmentConfig(minimum_duration_seconds=4.0, handle_seconds=0.5),
    )

    assert len(segments) == 1
    assert segments[0].start_seconds == 0.0
    assert segments[0].end_seconds == 6.5
    assert segments[0].duration_seconds == 6.5


def test_build_segments_uses_exit_threshold_to_keep_candidate_open() -> None:
    windows = [_window(0.0, 0.9), _window(2.0, 0.65), _window(4.0, 0.9)]

    segments = build_segments(
        windows,
        clip_duration_seconds=7.0,
        config=SegmentConfig(minimum_duration_seconds=4.0, handle_seconds=0.0),
    )

    assert len(segments) == 1
    assert segments[0].end_seconds == 6.0


def test_build_segments_discards_short_candidate() -> None:
    segments = build_segments(
        [_window(0.0), _window(2.0)],
        clip_duration_seconds=4.0,
        config=SegmentConfig(minimum_duration_seconds=5.0),
    )

    assert segments == []


def test_build_segments_splits_at_critical_jerk() -> None:
    critical = _window(2.0)
    critical.jerk_norm = 0.8

    segments = build_segments(
        [_window(0.0), critical, _window(4.0)],
        clip_duration_seconds=6.0,
        config=SegmentConfig(minimum_duration_seconds=1.0, handle_seconds=0.0),
    )

    assert len(segments) == 2
    assert segments[0].end_seconds == 2.0
    assert segments[1].start_seconds == 4.0


def test_build_segments_splits_at_critical_hard_turn() -> None:
    critical = _window(2.0)
    critical.hard_turn_ratio = 0.5

    segments = build_segments(
        [_window(0.0), critical, _window(4.0)],
        clip_duration_seconds=6.0,
        config=SegmentConfig(minimum_duration_seconds=1.0, handle_seconds=0.0),
    )

    assert len(segments) == 2
    assert segments[0].end_seconds == 2.0
    assert segments[1].start_seconds == 4.0


def test_build_segments_splits_at_critical_hard_brake() -> None:
    critical = _window(2.0)
    critical.hard_brake_ratio = 0.5

    segments = build_segments(
        [_window(0.0), critical, _window(4.0)],
        clip_duration_seconds=6.0,
        config=SegmentConfig(minimum_duration_seconds=1.0, handle_seconds=0.0),
    )

    assert len(segments) == 2
    assert segments[0].end_seconds == 2.0
    assert segments[1].start_seconds == 4.0
