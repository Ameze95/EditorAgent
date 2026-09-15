from __future__ import annotations

import cv2
import numpy as np
import pytest

from editoragent.analyzers.motion import (
    MotionRaw,
    estimate_motion,
    normalize_motion,
    summarize_motion,
)
from editoragent.analyzers.stability import estimate_stability, normalize_stability


def _pattern() -> np.ndarray:
    frame = np.zeros((180, 240), dtype=np.uint8)
    cv2.rectangle(frame, (40, 50), (120, 130), 220, thickness=-1)
    cv2.circle(frame, (180, 40), 20, 150, thickness=-1)
    return frame


def test_identical_frames_have_negligible_motion() -> None:
    frame = _pattern()

    motion = estimate_motion(frame, frame.copy())

    assert motion.magnitude == pytest.approx(0.0, abs=0.1)
    assert normalize_motion(motion) == pytest.approx(0.0, abs=0.01)


def test_translated_frame_reports_global_displacement() -> None:
    previous = _pattern()
    transform = np.float32([[1, 0, 8], [0, 1, -5]])
    current = cv2.warpAffine(previous, transform, (previous.shape[1], previous.shape[0]))

    motion = estimate_motion(previous, current)

    assert motion.displacement_x == pytest.approx(8.0, abs=1.0)
    assert motion.displacement_y == pytest.approx(-5.0, abs=1.0)
    assert motion.magnitude == pytest.approx(np.hypot(8.0, 5.0), abs=1.0)
    assert motion.response > 0.5


def test_first_frame_has_zero_motion() -> None:
    motion = estimate_motion(None, _pattern())

    assert motion.magnitude == 0.0
    assert motion.response == 1.0


def test_untextured_frames_have_low_tracking_confidence() -> None:
    previous = np.full((180, 240), 128, dtype=np.uint8)
    current = previous.copy()

    motion = estimate_motion(previous, current)
    summary = summarize_motion([motion])

    assert summary.tracking_confidence < 0.1


def test_consistent_direction_has_high_coherence_and_low_jerk() -> None:
    motions = [MotionRaw(displacement_x=8.0, magnitude=8.0) for _ in range(4)]

    summary = summarize_motion(motions)

    assert summary.direction_coherence == pytest.approx(1.0)
    assert summary.jerk_norm == pytest.approx(0.0)


def test_direction_change_reduces_coherence_and_speed_change_increases_jerk() -> None:
    motions = [
        MotionRaw(displacement_x=4.0, magnitude=4.0, direction_radians=0.0),
        MotionRaw(displacement_x=-20.0, magnitude=20.0, direction_radians=np.pi),
    ]

    summary = summarize_motion(motions)

    assert summary.direction_coherence < 0.2
    assert summary.jerk_norm > 0.5


def test_sharp_reversal_is_flagged_as_hard_turn() -> None:
    motions = [
        MotionRaw(displacement_x=10.0, magnitude=10.0, direction_radians=0.0),
        MotionRaw(displacement_x=10.0, magnitude=10.0, direction_radians=0.05),
        MotionRaw(displacement_x=-10.0, magnitude=10.0, direction_radians=np.pi),
    ]

    summary = summarize_motion(motions)

    assert summary.hard_turn_ratio > 0.0
    assert summary.hard_brake_ratio == 0.0


def test_sudden_stop_is_flagged_as_hard_brake() -> None:
    motions = [
        MotionRaw(displacement_x=20.0, magnitude=20.0, direction_radians=0.0),
        MotionRaw(displacement_x=20.0, magnitude=20.0, direction_radians=0.0),
        MotionRaw(displacement_x=1.0, magnitude=1.0, direction_radians=0.0),
    ]

    summary = summarize_motion(motions)

    assert summary.hard_brake_ratio > 0.0
    assert summary.hard_turn_ratio == 0.0


def test_smooth_motion_has_no_hard_turn_or_brake() -> None:
    motions = [
        MotionRaw(displacement_x=10.0, magnitude=10.0, direction_radians=0.0)
        for _ in range(5)
    ]

    summary = summarize_motion(motions)

    assert summary.hard_turn_ratio == 0.0
    assert summary.hard_brake_ratio == 0.0


def test_coherent_translation_has_high_stability() -> None:
    previous = _pattern()
    transform = np.float32([[1, 0, 6], [0, 1, 3]])
    current = cv2.warpAffine(previous, transform, (previous.shape[1], previous.shape[0]))

    stability = estimate_stability(previous, current)

    assert stability.tracked_points >= 8
    assert stability.inlier_ratio > 0.7
    assert normalize_stability(stability) > 0.7


def test_unrelated_frames_have_low_stability() -> None:
    rng = np.random.default_rng(seed=7)
    previous = rng.integers(0, 256, size=(180, 240), dtype=np.uint8)
    current = rng.integers(0, 256, size=(180, 240), dtype=np.uint8)

    stability = estimate_stability(previous, current)

    assert normalize_stability(stability) < 0.7
