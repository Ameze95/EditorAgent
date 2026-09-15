from __future__ import annotations

import csv
import json
from pathlib import Path

from editoragent.domain.models import HumanLabel, Segment, SegmentStatus
from editoragent.infrastructure.db import get_session
from editoragent.services import dataset_export_service, project_service


def test_dataset_exports_include_segments_metrics_and_human_labels(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project = project_service.create_project("Dataset", project_root)
    with get_session(project_root) as session:
        segment = Segment(
            project_id=project.id,
            clip_id="clip-1",
            analysis_run_id=None,
            start_seconds=1.0,
            end_seconds=5.0,
            technical_score=0.82,
            reasons_json='["Movimiento suave"]',
            penalties_json="[]",
            status=SegmentStatus.APPROVED,
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
        session.add(
            HumanLabel(
                project_id=project.id,
                clip_id="clip-1",
                segment_id=segment.id,
                start_seconds=1.0,
                end_seconds=5.0,
                utility_label="usable",
                shot_type="traveling",
                motion_quality="smooth",
            )
        )
        session.commit()

    json_path, count = dataset_export_service.export_dataset_json(project_root)
    csv_path, csv_count = dataset_export_service.export_dataset_csv(project_root)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert count == 1
    assert csv_count == 1
    assert payload["segments"][0]["technical_score"] == 0.82
    assert payload["segments"][0]["human_label"]["shot_type"] == "traveling"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["utility_label"] == "usable"
    assert row["motion_quality"] == "smooth"
