"""Export the private human-knowledge dataset without touching source media."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import select

from editoragent.domain.models import AnalysisRun, Clip, HumanLabel, Segment
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project


def _dataset_rows(project_root: Path) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    project = get_project(project_root)
    with get_session(project_root) as session:
        clips = session.exec(select(Clip).where(Clip.project_id == project.id)).all()
        segments = session.exec(select(Segment).where(Segment.project_id == project.id)).all()
        labels = session.exec(select(HumanLabel).where(HumanLabel.project_id == project.id)).all()
        runs = {
            run.id: run
            for run in session.exec(
                select(AnalysisRun).where(AnalysisRun.project_id == project.id)
            ).all()
        }

    clip_payload = [
        {
            "id": clip.id,
            "relative_path": clip.relative_path,
            "duration_seconds": clip.duration_seconds,
            "width": clip.width,
            "height": clip.height,
            "fps_num": clip.fps_num,
            "fps_den": clip.fps_den,
            "codec": clip.codec,
            "pixel_format": clip.pixel_format,
            "ingest_status": clip.ingest_status.value,
        }
        for clip in clips
    ]
    label_by_segment = {label.segment_id: label for label in labels if label.segment_id}
    rows: list[dict[str, Any]] = []
    for segment in segments:
        run = runs.get(segment.analysis_run_id) if segment.analysis_run_id else None
        label = label_by_segment.get(segment.id)
        rows.append(
            {
                "segment_id": segment.id,
                "clip_id": segment.clip_id,
                "analysis_run_id": segment.analysis_run_id,
                "start_seconds": segment.start_seconds,
                "end_seconds": segment.end_seconds,
                "duration_seconds": round(segment.end_seconds - segment.start_seconds, 3),
                "technical_score": segment.technical_score,
                "status": segment.status.value,
                "reasons": json.loads(segment.reasons_json),
                "penalties": json.loads(segment.penalties_json),
                "user_note": segment.user_note,
                "profile_name": run.profile_name if run else None,
                "analyzer_version": run.analyzer_version if run else None,
                "config_hash": run.config_hash if run else None,
                "config": json.loads(run.config_json) if run else None,
                "human_label": _label_payload(label),
            }
        )
    return project.name, clip_payload, rows


def _label_payload(label: HumanLabel | None) -> dict[str, Any] | None:
    if label is None:
        return None
    return {
        "id": label.id,
        "utility_label": label.utility_label,
        "capture_type": label.capture_type,
        "motion_intent": label.motion_intent,
        "shot_type": label.shot_type,
        "motion_quality": label.motion_quality,
        "rejection_reason": label.rejection_reason,
        "technical_issues": json.loads(label.technical_issues_json),
        "confidence": label.confidence,
        "note": label.note,
        "annotator": label.annotator,
    }


def export_dataset_json(project_root: Path) -> tuple[Path, int]:
    project_name, clips, rows = _dataset_rows(project_root)
    version, destination = _next_destination(project_root, "json")
    payload = {
        "schema_version": 1,
        "dataset_version": version,
        "exported_at": datetime.now(UTC).isoformat(),
        "project_name": project_name,
        "clips": clips,
        "segments": rows,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination, len(rows)


def export_dataset_csv(project_root: Path) -> tuple[Path, int]:
    _project_name, _clips, rows = _dataset_rows(project_root)
    _version, destination = _next_destination(project_root, "csv")
    fields = [
        "segment_id", "clip_id", "analysis_run_id", "start_seconds", "end_seconds",
        "duration_seconds", "technical_score", "status", "profile_name",
        "analyzer_version", "config_hash", "utility_label", "shot_type",
        "motion_quality", "rejection_reason", "confidence", "user_note", "label_note",
    ]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            label = row["human_label"] or {}
            writer.writerow(
                {
                    **{field: row.get(field) for field in fields},
                    "utility_label": label.get("utility_label"),
                    "shot_type": label.get("shot_type"),
                    "motion_quality": label.get("motion_quality"),
                    "rejection_reason": label.get("rejection_reason"),
                    "confidence": label.get("confidence"),
                    "label_note": label.get("note"),
                }
            )
    return destination, len(rows)


def _next_destination(project_root: Path, extension: str) -> tuple[str, Path]:
    directory = project_root / "exports" / "datasets"
    directory.mkdir(parents=True, exist_ok=True)
    version = 1
    while (directory / f"dataset_v{version:03d}.{extension}").exists():
        version += 1
    return f"dataset_v{version:03d}", directory / f"dataset_v{version:03d}.{extension}"
