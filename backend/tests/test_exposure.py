from __future__ import annotations

import numpy as np

from editoragent.analyzers.exposure import exposure_raw, normalize_exposure


def test_balanced_gray_frame_scores_well() -> None:
    rng = np.random.default_rng(seed=42)
    frame = rng.integers(low=90, high=170, size=(240, 320), dtype=np.uint8)

    raw = exposure_raw(frame)

    assert normalize_exposure(raw) > 0.9


def test_overexposed_frame_is_penalized() -> None:
    frame = np.full((240, 320), fill_value=250, dtype=np.uint8)

    raw = exposure_raw(frame)

    assert raw.near_white_ratio > 0.9
    assert normalize_exposure(raw) < 0.2


def test_underexposed_frame_is_penalized() -> None:
    frame = np.full((240, 320), fill_value=2, dtype=np.uint8)

    raw = exposure_raw(frame)

    assert raw.near_black_ratio > 0.9
    assert normalize_exposure(raw) < 0.2
