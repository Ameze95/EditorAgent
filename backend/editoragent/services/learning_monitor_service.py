from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from sqlmodel import select

from editoragent.domain.models import Clip, HumanLabel, Segment
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project


def learning_summary(project_root: Path) -> dict[str, object]:
    project = get_project(project_root)
    with get_session(project_root) as session:
        clips = session.exec(select(Clip).where(Clip.project_id == project.id)).all()
        segments = session.exec(select(Segment).where(Segment.project_id == project.id)).all()
        labels = session.exec(select(HumanLabel).where(HumanLabel.project_id == project.id)).all()

    labeled_segment_ids = {label.segment_id for label in labels if label.segment_id}
    shot_types = _counts(label.shot_type for label in labels if label.shot_type)
    utility = _counts(label.utility_label for label in labels)
    motion = _counts(label.motion_quality for label in labels if label.motion_quality)
    return {
        "clips_total": len(clips),
        "clips_with_segments": len({segment.clip_id for segment in segments}),
        "segments_total": len(segments),
        "segments_labeled": len(labeled_segment_ids),
        "labels_total": len(labels),
        "uncertain_labels": utility.get("uncertain", 0),
        "approved_segments": sum(segment.status.value == "approved" for segment in segments),
        "rejected_segments": sum(segment.status.value == "rejected" for segment in segments),
        "utility_labels": utility,
        "shot_types": shot_types,
        "motion_quality": motion,
        "coverage_percent": (
            round(len(labeled_segment_ids) / len(segments) * 100, 1)
            if segments
            else 0.0
        ),
    }


def _counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts
