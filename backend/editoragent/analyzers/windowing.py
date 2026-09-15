"""Aggregate per-frame technical metrics into fixed-size, overlapping windows.

docs/ANALYSIS_SPEC.md §2: windows of 2-4s with ~50% overlap. This slice only
has sharpness + exposure plus raw global motion intensity. Stability,
direction consistency, jerk, frame health and the composite score are still
future signals; presenting a final score now would hide that incompleteness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from editoragent.analyzers.exposure import ExposureRaw, exposure_raw, normalize_exposure
from editoragent.analyzers.frame_sampler import SampledFrame
from editoragent.analyzers.motion import (
    MotionRaw,
    estimate_motion,
    normalize_motion,
    summarize_motion,
)
from editoragent.analyzers.sharpness import normalize_sharpness, sharpness_raw
from editoragent.analyzers.stability import StabilityRaw, estimate_stability, normalize_stability

SHARPNESS_HIGH = 0.7
SHARPNESS_LOW = 0.4
EXPOSURE_GOOD = 0.85


@dataclass(frozen=True)
class FrameMetrics:
    timestamp_seconds: float
    sharpness_raw: float
    sharpness_norm: float
    exposure: ExposureRaw
    exposure_norm: float
    motion: MotionRaw = field(default_factory=MotionRaw)
    motion_norm: float = 0.0
    stability: StabilityRaw = field(default_factory=lambda: StabilityRaw(1.0, 0, 0.0, 0.0))
    stability_norm: float = 1.0


def compute_frame_metrics(
    frame: SampledFrame, previous_gray: np.ndarray | None = None
) -> FrameMetrics:
    raw_sharp = sharpness_raw(frame.gray)
    raw_exposure = exposure_raw(frame.gray)
    raw_motion = estimate_motion(previous_gray, frame.gray)
    raw_stability = estimate_stability(previous_gray, frame.gray)
    return FrameMetrics(
        timestamp_seconds=frame.timestamp_seconds,
        sharpness_raw=raw_sharp,
        sharpness_norm=normalize_sharpness(raw_sharp),
        exposure=raw_exposure,
        exposure_norm=normalize_exposure(raw_exposure),
        motion=raw_motion,
        motion_norm=normalize_motion(raw_motion),
        stability=raw_stability,
        stability_norm=normalize_stability(raw_stability),
    )


@dataclass
class WindowMetrics:
    start_seconds: float
    end_seconds: float
    frame_count: int
    sharpness_norm: float
    exposure_norm: float
    motion_norm: float
    direction_coherence: float
    jerk_norm: float
    tracking_confidence: float
    stability_norm: float
    hard_turn_ratio: float = 0.0
    hard_brake_ratio: float = 0.0
    reasons: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)


def _describe_window(
    sharpness_norm: float,
    exposure_norm: float,
    tracking_confidence: float,
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    penalties: list[str] = []
    if sharpness_norm >= SHARPNESS_HIGH:
        reasons.append(f"Nitidez alta (score {sharpness_norm:.2f})")
    elif sharpness_norm < SHARPNESS_LOW:
        penalties.append(f"Nitidez baja / posible desenfoque (score {sharpness_norm:.2f})")
    if exposure_norm >= EXPOSURE_GOOD:
        reasons.append(f"Exposición equilibrada (score {exposure_norm:.2f})")
    else:
        penalties.append(f"Clipping de negros/blancos relevante (score {exposure_norm:.2f})")
    if tracking_confidence < 0.4:
        penalties.append(
            f"Confianza de movimiento limitada (tracking {tracking_confidence:.2f})"
        )
    return reasons, penalties


def build_windows(
    frame_metrics: list[FrameMetrics],
    *,
    duration_seconds: float,
    window_seconds: float = 3.0,
    overlap_ratio: float = 0.5,
) -> list[WindowMetrics]:
    if not frame_metrics:
        return []

    step_seconds = window_seconds * (1 - overlap_ratio)
    windows: list[WindowMetrics] = []
    start = 0.0
    while start < duration_seconds:
        end = min(start + window_seconds, duration_seconds)
        in_window = [fm for fm in frame_metrics if start <= fm.timestamp_seconds < end]
        if in_window:
            sharpness_norm = sum(fm.sharpness_norm for fm in in_window) / len(in_window)
            exposure_norm = sum(fm.exposure_norm for fm in in_window) / len(in_window)
            motion_norm = sum(fm.motion_norm for fm in in_window) / len(in_window)
            motion_summary = summarize_motion([fm.motion for fm in in_window])
            stability_norm = sum(fm.stability_norm for fm in in_window) / len(in_window)
            reasons, penalties = _describe_window(
                sharpness_norm, exposure_norm, motion_summary.tracking_confidence
            )
            if motion_summary.hard_turn_ratio > 0.0:
                penalties.append(
                    "Cambio de dirección brusco detectado "
                    f"(ratio {motion_summary.hard_turn_ratio:.2f})"
                )
            if motion_summary.hard_brake_ratio > 0.0:
                penalties.append(
                    "Frenazo/parada brusca detectada "
                    f"(ratio {motion_summary.hard_brake_ratio:.2f})"
                )
            windows.append(
                WindowMetrics(
                    start_seconds=round(start, 3),
                    end_seconds=round(end, 3),
                    frame_count=len(in_window),
                    sharpness_norm=round(sharpness_norm, 4),
                    exposure_norm=round(exposure_norm, 4),
                    motion_norm=round(motion_norm, 4),
                    direction_coherence=round(motion_summary.direction_coherence, 4),
                    jerk_norm=round(motion_summary.jerk_norm, 4),
                    tracking_confidence=round(motion_summary.tracking_confidence, 4),
                    stability_norm=round(stability_norm, 4),
                    hard_turn_ratio=round(motion_summary.hard_turn_ratio, 4),
                    hard_brake_ratio=round(motion_summary.hard_brake_ratio, 4),
                    reasons=reasons,
                    penalties=penalties,
                )
            )
        start += step_seconds
    return windows
