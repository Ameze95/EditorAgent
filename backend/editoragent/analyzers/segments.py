"""Build provisional technical candidate segments from window metrics.

This is intentionally not an editorial verdict. It applies configurable
hysteresis to a preliminary technical score so short threshold fluctuations
do not create dozens of tiny candidates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from editoragent.analyzers.windowing import WindowMetrics


@dataclass(frozen=True)
class SegmentConfig:
    enter_threshold: float = 0.72
    exit_threshold: float = 0.62
    minimum_duration_seconds: float = 4.0
    merge_gap_seconds: float = 1.0
    handle_seconds: float = 0.5
    critical_jerk_threshold: float = 0.55
    critical_stability_floor: float = 0.35
    critical_tracking_floor: float = 0.20
    critical_hard_turn_ratio: float = 0.15
    critical_hard_brake_ratio: float = 0.15
    weight_sharpness: float = 0.40
    weight_exposure: float = 0.25
    weight_direction: float = 0.20
    weight_tracking: float = 0.10
    weight_stability: float = 0.05

    def __post_init__(self) -> None:
        weights = (
            self.weight_sharpness,
            self.weight_exposure,
            self.weight_direction,
            self.weight_tracking,
            self.weight_stability,
        )
        if any(weight < 0 for weight in weights) or abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Los pesos del score deben ser no negativos y sumar 1.")


@dataclass
class SegmentCandidate:
    start_seconds: float
    end_seconds: float
    technical_score: float
    reasons: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return round(self.end_seconds - self.start_seconds, 3)


def preliminary_score(
    window: WindowMetrics, config: SegmentConfig | None = None
) -> float:
    config = config or SegmentConfig()
    score = (
        config.weight_sharpness * window.sharpness_norm
        + config.weight_exposure * window.exposure_norm
        + config.weight_direction * window.direction_coherence
        + config.weight_tracking * window.tracking_confidence
        + config.weight_stability * window.stability_norm
        - 0.20 * window.jerk_norm
        - 0.30 * window.hard_turn_ratio
        - 0.30 * window.hard_brake_ratio
    )
    return max(0.0, min(1.0, score))


def _reasons_and_penalties(windows: list[WindowMetrics]) -> tuple[list[str], list[str]]:
    reasons = sorted({reason for window in windows for reason in window.reasons})
    penalties = sorted({penalty for window in windows for penalty in window.penalties})
    return reasons, penalties


def _is_critical(window: WindowMetrics, config: SegmentConfig) -> bool:
    return (
        window.jerk_norm >= config.critical_jerk_threshold
        or window.stability_norm < config.critical_stability_floor
        or window.tracking_confidence < config.critical_tracking_floor
        or window.hard_turn_ratio >= config.critical_hard_turn_ratio
        or window.hard_brake_ratio >= config.critical_hard_brake_ratio
    )


def build_segments(
    windows: list[WindowMetrics],
    *,
    clip_duration_seconds: float,
    config: SegmentConfig | None = None,
) -> list[SegmentCandidate]:
    """Build natural-length candidates using enter/exit hysteresis."""
    config = config or SegmentConfig()
    if not windows:
        return []

    candidates: list[tuple[float, float, list[WindowMetrics]]] = []
    active_start: float | None = None
    active_windows: list[WindowMetrics] = []

    for window in windows:
        score = preliminary_score(window, config)
        if active_start is None:
            if score >= config.enter_threshold:
                active_start = window.start_seconds
                active_windows = [window]
            continue
        if _is_critical(window, config):
            candidates.append((active_start, active_windows[-1].end_seconds, active_windows))
            active_start = None
            active_windows = []
            continue
        if score >= config.exit_threshold:
            active_windows.append(window)
            continue
        candidates.append((active_start, active_windows[-1].end_seconds, active_windows))
        active_start = None
        active_windows = []

    if active_start is not None and active_windows:
        candidates.append((active_start, active_windows[-1].end_seconds, active_windows))

    merged: list[tuple[float, float, list[WindowMetrics]]] = []
    for start, end, candidate_windows in candidates:
        if merged and start - merged[-1][1] <= config.merge_gap_seconds:
            previous_start, previous_end, previous_windows = merged[-1]
            merged[-1] = (previous_start, end, previous_windows + candidate_windows)
        else:
            merged.append((start, end, candidate_windows))

    segments: list[SegmentCandidate] = []
    for start, end, candidate_windows in merged:
        if end - start < config.minimum_duration_seconds:
            continue
        start = max(0.0, start - config.handle_seconds)
        end = min(clip_duration_seconds, end + config.handle_seconds)
        reasons, penalties = _reasons_and_penalties(candidate_windows)
        score = sum(preliminary_score(window, config) for window in candidate_windows) / len(
            candidate_windows
        )
        segments.append(
            SegmentCandidate(
                start_seconds=round(start, 3),
                end_seconds=round(end, 3),
                technical_score=round(score, 4),
                reasons=reasons,
                penalties=penalties,
            )
        )
    return segments
