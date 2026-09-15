from __future__ import annotations

import numpy as np

from editoragent.analyzers.sharpness import normalize_sharpness, sharpness_raw


def _checkerboard(size: int = 256, square: int = 8) -> np.ndarray:
    idx = np.arange(size)
    pattern = ((idx[:, None] // square) + (idx[None, :] // square)) % 2
    return (pattern * 255).astype(np.uint8)


def test_sharp_image_scores_higher_than_blurred() -> None:
    sharp = _checkerboard()
    blurred = np.full_like(sharp, fill_value=int(sharp.mean()))

    assert sharpness_raw(sharp) > sharpness_raw(blurred)


def test_normalize_sharpness_is_clamped_to_unit_range() -> None:
    assert normalize_sharpness(-10.0) == 0.0
    assert normalize_sharpness(0.0) == 0.0
    assert normalize_sharpness(10_000.0) == 1.0
