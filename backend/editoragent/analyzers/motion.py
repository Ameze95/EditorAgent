"""Estimate global frame-to-frame camera motion.

This first motion slice measures displacement and direction consistency only.
It does not yet label motion as good/bad or calculate jerk; those decisions
belong to the profile and segment-building stages.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

MOTION_RESIZE_WIDTH = 320
REFERENCE_MOTION_PIXELS = 24.0


@dataclass(frozen=True)
class MotionRaw:
    displacement_x: float = 0.0
    displacement_y: float = 0.0
    magnitude: float = 0.0
    response: float = 1.0
    direction_radians: float | None = None


@dataclass(frozen=True)
class MotionSummary:
    direction_coherence: float
    jerk_norm: float
    tracking_confidence: float
    hard_turn_ratio: float
    hard_brake_ratio: float


# Frame-to-frame angle change above this is a real direction reversal, not
# just noise in a mostly-straight pan (docs/DECISIONS.md ADR-015).
HARD_TURN_ANGLE_RADIANS = 1.75  # ~100 degrees
# Relative drop in speed between consecutive frames that reads as a hard stop.
HARD_BRAKE_RATIO = 0.6


def _resize(gray: np.ndarray) -> np.ndarray:
    height, width = gray.shape[:2]
    if width <= MOTION_RESIZE_WIDTH:
        return gray
    scale = MOTION_RESIZE_WIDTH / width
    return cv2.resize(
        gray,
        (MOTION_RESIZE_WIDTH, max(2, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )


def estimate_motion(previous: np.ndarray | None, current: np.ndarray) -> MotionRaw:
    """Estimate global translation from the previous frame to the current one."""
    if previous is None:
        return MotionRaw(0.0, 0.0, 0.0, 1.0)
    previous_small = _resize(previous).astype(np.float32)
    current_small = _resize(current).astype(np.float32)
    shift, response = cv2.phaseCorrelate(previous_small, current_small)
    displacement_x, displacement_y = float(shift[0]), float(shift[1])
    magnitude = float(np.hypot(displacement_x, displacement_y))
    return MotionRaw(
        displacement_x=displacement_x,
        displacement_y=displacement_y,
        magnitude=magnitude,
        response=float(response),
        direction_radians=float(np.arctan2(displacement_y, displacement_x))
        if magnitude > 0.0
        else None,
    )


def normalize_motion(raw: MotionRaw) -> float:
    """Normalize motion intensity to [0, 1] for later profile calibration."""
    return max(0.0, min(1.0, raw.magnitude / REFERENCE_MOTION_PIXELS))


def summarize_motion(motions: list[MotionRaw]) -> MotionSummary:
    """Summarize directional consistency and abrupt magnitude changes."""
    moving = [motion for motion in motions if motion.magnitude > 0.5]
    if not moving:
        confidence = float(np.mean([motion.response for motion in motions])) if motions else 1.0
        return MotionSummary(
            direction_coherence=1.0,
            jerk_norm=0.0,
            tracking_confidence=max(0.0, min(1.0, confidence)),
            hard_turn_ratio=0.0,
            hard_brake_ratio=0.0,
        )

    directions = np.array(
        [
            motion.direction_radians
            if motion.direction_radians is not None
            else np.arctan2(motion.displacement_y, motion.displacement_x)
            for motion in moving
        ],
        dtype=float,
    )
    coherence = float(np.hypot(np.cos(directions).mean(), np.sin(directions).mean()))
    magnitudes = np.array([motion.magnitude for motion in moving], dtype=float)
    if len(magnitudes) < 2:
        jerk_norm = 0.0
    else:
        jerk_norm = float(np.mean(np.abs(np.diff(magnitudes))) / REFERENCE_MOTION_PIXELS)

    if len(directions) < 2:
        hard_turn_ratio = 0.0
    else:
        # Wrap angle differences to (-pi, pi] before comparing to the threshold.
        angle_diffs = np.abs(np.angle(np.exp(1j * np.diff(directions))))
        hard_turn_ratio = float(np.mean(angle_diffs >= HARD_TURN_ANGLE_RADIANS))

    if len(magnitudes) < 2:
        hard_brake_ratio = 0.0
    else:
        previous_speed = magnitudes[:-1]
        current_speed = magnitudes[1:]
        with np.errstate(divide="ignore", invalid="ignore"):
            drop_ratio = np.where(
                previous_speed > 1e-6,
                (previous_speed - current_speed) / previous_speed,
                0.0,
            )
        hard_brake_ratio = float(np.mean(drop_ratio >= HARD_BRAKE_RATIO))

    return MotionSummary(
        direction_coherence=max(0.0, min(1.0, coherence)),
        jerk_norm=max(0.0, min(1.0, jerk_norm)),
        tracking_confidence=max(
            0.0,
            min(1.0, float(np.mean([motion.response for motion in moving]))),
        ),
        hard_turn_ratio=max(0.0, min(1.0, hard_turn_ratio)),
        hard_brake_ratio=max(0.0, min(1.0, hard_brake_ratio)),
    )
