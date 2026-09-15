"""Create and evaluate private human-labeled analysis datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LabeledInterval:
    start_seconds: float
    end_seconds: float
    label: str
    reason: str | None = None


@dataclass(frozen=True)
class ClipAnnotation:
    clip_id: str
    relative_path: str
    intent_profile: str
    intervals: list[LabeledInterval]


def create_annotation_template(
    analysis_json: Path, destination: Path, *, clip_id: str = "", relative_path: str = ""
) -> Path:
    """Create an editable annotation file from a persisted windows JSON artifact."""
    windows = json.loads(analysis_json.read_text(encoding="utf-8"))
    intervals = [
        {
            "start_seconds": window["start_seconds"],
            "end_seconds": window["end_seconds"],
            "label": "unlabeled",
            "reason": None,
        }
        for window in windows
    ]
    payload = {
        "schema_version": 1,
        "clip_id": clip_id,
        "relative_path": relative_path,
        "intent_profile": "cinematic",
        "intervals": intervals,
        "labels": [
            "usable",
            "technical_bad",
            "intentional_dynamic",
            "abrupt_motion",
            "takeoff_landing",
            "redundant",
            "uncertain",
            "unlabeled",
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination


def load_annotations(path: Path) -> ClipAnnotation:
    payload = json.loads(path.read_text(encoding="utf-8"))
    intervals = [
        LabeledInterval(
            start_seconds=float(item["start_seconds"]),
            end_seconds=float(item["end_seconds"]),
            label=str(item["label"]),
            reason=item.get("reason"),
        )
        for item in payload["intervals"]
    ]
    return ClipAnnotation(
        clip_id=str(payload["clip_id"]),
        relative_path=str(payload["relative_path"]),
        intent_profile=str(payload.get("intent_profile", "unknown")),
        intervals=intervals,
    )


def evaluate_windows(
    windows_json: Path,
    annotation_path: Path,
    *,
    enter_threshold: float = 0.72,
    top_k: int = 5,
) -> dict[str, Any]:
    """Compare current score and sharpness/exposure baseline against usable intervals."""
    windows = json.loads(windows_json.read_text(encoding="utf-8"))
    annotation = load_annotations(annotation_path)
    usable = [item for item in annotation.intervals if item.label == "usable"]
    current = [
        item
        for item in windows
        if _current_score(item) >= enter_threshold
    ]
    baseline = sorted(
        windows,
        key=lambda item: (float(item["sharpness_norm"]) + float(item["exposure_norm"])) / 2,
        reverse=True,
    )[: len(current)]
    return {
        "clip_id": annotation.clip_id,
        "relative_path": annotation.relative_path,
        "usable_seconds": round(sum(_duration(item) for item in usable), 3),
        "current": _metrics(current, usable, top_k=top_k),
        "baseline_sharpness_exposure": _metrics(baseline, usable, top_k=top_k),
        "unlabeled_windows": sum(item.label == "unlabeled" for item in annotation.intervals),
    }


def _current_score(window: dict[str, Any]) -> float:
    return (
        0.40 * float(window.get("sharpness_norm", 0.0))
        + 0.25 * float(window.get("exposure_norm", 0.0))
        + 0.20 * float(window.get("direction_coherence", 0.0))
        + 0.10 * float(window.get("tracking_confidence", 0.0))
        + 0.05 * float(window.get("stability_norm", 0.0))
        - 0.20 * float(window.get("jerk_norm", 0.0))
        - 0.30 * float(window.get("hard_turn_ratio", 0.0))
        - 0.30 * float(window.get("hard_brake_ratio", 0.0))
    )


def _metrics(
    predicted: list[dict[str, Any]], usable: list[LabeledInterval], *, top_k: int
) -> dict[str, float | int]:
    predicted_intervals = [
        (float(item["start_seconds"]), float(item["end_seconds"])) for item in predicted
    ]
    usable_seconds = sum(_duration(item) for item in usable)
    predicted_seconds = sum(end - start for start, end in predicted_intervals)
    overlap_seconds = sum(
        _overlap(start, end, item.start_seconds, item.end_seconds)
        for start, end in predicted_intervals
        for item in usable
    )
    top = predicted[:top_k]
    top_overlap = sum(
        _overlap(
            float(item["start_seconds"]),
            float(item["end_seconds"]),
            truth.start_seconds,
            truth.end_seconds,
        )
        for item in top
        for truth in usable
    )
    top_seconds = sum(
        float(item["end_seconds"]) - float(item["start_seconds"]) for item in top
    )
    temporal_iou = sum(
        max(
            (_interval_iou(start, end, truth.start_seconds, truth.end_seconds) for truth in usable),
            default=0.0,
        )
        for start, end in predicted_intervals
    ) / len(predicted_intervals) if predicted_intervals else 0.0
    return {
        "predicted_windows": len(predicted),
        "precision": round(overlap_seconds / predicted_seconds, 4) if predicted_seconds else 0.0,
        "recall": round(overlap_seconds / usable_seconds, 4) if usable_seconds else 0.0,
        "precision_at_k": round(top_overlap / top_seconds, 4) if top_seconds > 0
        else 0.0,
        "temporal_iou": round(temporal_iou, 4),
    }


def _duration(interval: LabeledInterval) -> float:
    return max(0.0, interval.end_seconds - interval.start_seconds)


def _overlap(first_start: float, first_end: float, second_start: float, second_end: float) -> float:
    return max(0.0, min(first_end, second_end) - max(first_start, second_start))


def _interval_iou(
    first_start: float,
    first_end: float,
    second_start: float,
    second_end: float,
) -> float:
    intersection = _overlap(first_start, first_end, second_start, second_end)
    union = max(first_end, second_end) - min(first_start, second_start)
    return intersection / union if union > 0 else 0.0
