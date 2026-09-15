"""Sharpness metric: Laplacian variance over a resized grayscale frame.

docs/ANALYSIS_SPEC.md §3.1: base signal is the variance of the Laplacian.
Frames are resized to a fixed width first so the raw value is comparable
across clips of different resolutions (a 4K and a 1080p clip of the same
real sharpness should not get wildly different raw scores).
"""

from __future__ import annotations

import cv2
import numpy as np

RESIZE_WIDTH = 640

# Placeholder normalization reference, not yet calibrated against a labeled
# dataset (see docs/EVALUATION.md): raw Laplacian variance at/above this
# value maps to a normalized score of 1.0.
REFERENCE_SHARPNESS_MAX = 350.0


def _resize_for_analysis(gray: np.ndarray) -> np.ndarray:
    height, width = gray.shape[:2]
    if width <= RESIZE_WIDTH:
        return gray
    scale = RESIZE_WIDTH / width
    new_size = (RESIZE_WIDTH, max(1, round(height * scale)))
    return cv2.resize(gray, new_size, interpolation=cv2.INTER_AREA)


def sharpness_raw(gray: np.ndarray) -> float:
    """Variance of the Laplacian; higher means sharper."""
    resized = _resize_for_analysis(gray)
    laplacian = cv2.Laplacian(resized, cv2.CV_64F)
    return float(laplacian.var())


def normalize_sharpness(raw_value: float) -> float:
    return max(0.0, min(1.0, raw_value / REFERENCE_SHARPNESS_MAX))
