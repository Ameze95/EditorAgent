from __future__ import annotations

import json
from pathlib import Path

from editoragent.services.evaluation_service import (
    create_annotation_template,
    evaluate_windows,
)


def test_create_annotation_template_preserves_window_boundaries(tmp_path: Path) -> None:
    windows = tmp_path / "windows.json"
    destination = tmp_path / "annotations" / "clip.json"
    windows.write_text(
        json.dumps(
            [
                {"start_seconds": 0.0, "end_seconds": 3.0},
                {"start_seconds": 1.5, "end_seconds": 4.5},
            ]
        ),
        encoding="utf-8",
    )

    output = create_annotation_template(
        windows, destination, clip_id="clip-1", relative_path="clip.mp4"
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["clip_id"] == "clip-1"
    assert payload["intervals"][1]["start_seconds"] == 1.5
    assert payload["intervals"][0]["label"] == "unlabeled"


def test_evaluate_windows_reports_current_and_baseline_metrics(tmp_path: Path) -> None:
    windows = tmp_path / "windows.json"
    annotation = tmp_path / "clip.json"
    windows.write_text(
        json.dumps(
            [
                {
                    "start_seconds": 0.0,
                    "end_seconds": 3.0,
                    "sharpness_norm": 0.9,
                    "exposure_norm": 0.9,
                    "direction_coherence": 0.9,
                    "tracking_confidence": 0.9,
                    "stability_norm": 0.9,
                    "jerk_norm": 0.0,
                    "hard_turn_ratio": 0.0,
                    "hard_brake_ratio": 0.0,
                },
                {
                    "start_seconds": 3.0,
                    "end_seconds": 6.0,
                    "sharpness_norm": 0.2,
                    "exposure_norm": 0.2,
                    "direction_coherence": 0.2,
                    "tracking_confidence": 0.2,
                    "stability_norm": 0.2,
                    "jerk_norm": 0.8,
                    "hard_turn_ratio": 0.0,
                    "hard_brake_ratio": 0.0,
                },
            ]
        ),
        encoding="utf-8",
    )
    annotation.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "clip_id": "clip-1",
                "relative_path": "clip.mp4",
                "intent_profile": "cinematic",
                "intervals": [
                    {"start_seconds": 0.0, "end_seconds": 3.0, "label": "usable"},
                    {"start_seconds": 3.0, "end_seconds": 6.0, "label": "technical_bad"},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_windows(windows, annotation)

    assert result["current"]["precision"] == 1.0
    assert result["current"]["recall"] == 1.0
    assert result["current"]["temporal_iou"] == 1.0
    assert result["baseline_sharpness_exposure"]["precision"] == 1.0
