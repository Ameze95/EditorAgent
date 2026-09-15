"""Estimate whether frame-to-frame motion follows a coherent global transform."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

MAX_FEATURES = 160
MIN_FEATURES = 8


@dataclass(frozen=True)
class StabilityRaw:
    inlier_ratio: float
    tracked_points: int
    rotation_radians: float
    scale_delta: float


def estimate_stability(
    previous: np.ndarray | None, current: np.ndarray
) -> StabilityRaw:
    """Estimate robust global affine coherence between two grayscale frames."""
    if previous is None:
        return StabilityRaw(1.0, 0, 0.0, 0.0)

    points = cv2.goodFeaturesToTrack(
        previous,
        maxCorners=MAX_FEATURES,
        qualityLevel=0.01,
        minDistance=8,
        blockSize=7,
    )
    if points is None or len(points) < MIN_FEATURES:
        return StabilityRaw(0.0, 0, 0.0, 0.0)

    next_points = np.empty_like(points)
    tracked, status, _ = cv2.calcOpticalFlowPyrLK(
        previous, current, points, next_points
    )
    if tracked is None or status is None:
        return StabilityRaw(0.0, 0, 0.0, 0.0)

    valid_previous = points[status.ravel() == 1]
    valid_current = tracked[status.ravel() == 1]
    if len(valid_previous) < MIN_FEATURES:
        return StabilityRaw(0.0, len(valid_previous), 0.0, 0.0)

    transform, inlier_mask = cv2.estimateAffinePartial2D(
        valid_previous,
        valid_current,
        method=cv2.RANSAC,
        ransacReprojThreshold=2.5,
    )
    if transform is None or inlier_mask is None:
        return StabilityRaw(0.0, len(valid_previous), 0.0, 0.0)

    inlier_ratio = float(np.mean(inlier_mask.ravel().astype(np.float32)))
    rotation = float(np.arctan2(transform[1, 0], transform[0, 0]))
    scale = float(np.hypot(transform[0, 0], transform[1, 0]))
    return StabilityRaw(
        inlier_ratio=max(0.0, min(1.0, inlier_ratio)),
        tracked_points=len(valid_previous),
        rotation_radians=rotation,
        scale_delta=abs(scale - 1.0),
    )


def normalize_stability(raw: StabilityRaw) -> float:
    """Map geometric coherence to [0, 1], penalizing scale changes."""
    scale_penalty = min(1.0, raw.scale_delta / 0.15)
    return max(0.0, min(1.0, raw.inlier_ratio * (1.0 - scale_penalty)))
