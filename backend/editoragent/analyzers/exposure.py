"""Exposure/clipping metrics over a grayscale frame's luminance histogram.

docs/ANALYSIS_SPEC.md §3.2: proportion of near-black and near-white pixels,
plus luminance percentiles. Small specular highlights or a bit of sky glare
should not tank the score, so we penalize by *proportion* of clipped
pixels, not by their mere presence.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NEAR_BLACK_THRESHOLD = 16
NEAR_WHITE_THRESHOLD = 239

# Proportions of clipped pixels above this are treated as fully unusable.
# Placeholder, not yet calibrated against a labeled dataset (docs/EVALUATION.md).
BLACK_CLIP_TOLERANCE = 0.10
WHITE_CLIP_TOLERANCE = 0.05


@dataclass(frozen=True)
class ExposureRaw:
    near_black_ratio: float
    near_white_ratio: float
    p05: float
    p50: float
    p95: float


def exposure_raw(gray: np.ndarray) -> ExposureRaw:
    near_black_ratio = float(np.mean(gray <= NEAR_BLACK_THRESHOLD))
    near_white_ratio = float(np.mean(gray >= NEAR_WHITE_THRESHOLD))
    p05, p50, p95 = (float(v) for v in np.percentile(gray, [5, 50, 95]))
    return ExposureRaw(
        near_black_ratio=near_black_ratio,
        near_white_ratio=near_white_ratio,
        p05=p05,
        p50=p50,
        p95=p95,
    )


def normalize_exposure(raw: ExposureRaw) -> float:
    black_penalty = min(1.0, raw.near_black_ratio / BLACK_CLIP_TOLERANCE)
    white_penalty = min(1.0, raw.near_white_ratio / WHITE_CLIP_TOLERANCE)
    return max(0.0, 1.0 - black_penalty - white_penalty)
