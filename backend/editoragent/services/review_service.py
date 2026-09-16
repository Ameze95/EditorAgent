"""Read and update human review decisions for persisted segments."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, col, select

from editoragent.domain.models import AnalysisRun, AnalysisRunStatus, Clip, Segment, SegmentStatus
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project


class SegmentNotFoundError(LookupError):
    pass


def create_manual_segment(
    project_root: Path,
    clip_id: str,
    *,
    start_seconds: float,
    end_seconds: float,
) -> Segment:
    project = get_project(project_root)
    if start_seconds < 0 or end_seconds <= start_seconds:
        raise ValueError("El intervalo debe cumplir 0 <= inicio < fin.")
    with get_session(project_root) as session:
        clip = session.get(Clip, clip_id)
        if clip is None or clip.project_id != project.id:
            raise SegmentNotFoundError(f"No existe el clip {clip_id}.")
        if clip.duration_seconds is not None and end_seconds > clip.duration_seconds:
            raise ValueError("El intervalo no puede superar la duración del clip.")
        _ensure_no_overlap(session, clip_id, start_seconds, end_seconds)
        manual_run = AnalysisRun(
            project_id=project.id,
            clip_id=clip.id,
            profile_name="manual",
            config_json="{}",
            config_hash="manual",
            analyzer_version="manual",
            status=AnalysisRunStatus.COMPLETED,
        )
        session.add(manual_run)
        session.commit()
        session.refresh(manual_run)
        segment = Segment(
            project_id=project.id,
            clip_id=clip.id,
            analysis_run_id=manual_run.id,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            technical_score=0.0,
            status=SegmentStatus.MANUAL,
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
        return segment


def backfill_segments_from_analysis(project_root: Path) -> int:
    """Import candidates created before Segment rows existed in SQLite."""
    project = get_project(project_root)
    created = 0
    with get_session(project_root) as session:
        runs = session.exec(
            select(AnalysisRun).where(
                AnalysisRun.project_id == project.id,
                col(AnalysisRun.segments_path).is_not(None),
            )
        ).all()
        for run in runs:
            existing = session.exec(
                select(Segment).where(Segment.analysis_run_id == run.id)
            ).first()
            if existing is not None or run.segments_path is None:
                continue
            path = Path(run.segments_path)
            if not path.is_file():
                continue
            raw_segments = json.loads(path.read_text(encoding="utf-8"))
            for item in raw_segments:
                session.add(
                    Segment(
                        project_id=project.id,
                        clip_id=run.clip_id,
                        analysis_run_id=run.id,
                        start_seconds=float(item["start_seconds"]),
                        end_seconds=float(item["end_seconds"]),
                        technical_score=float(item["technical_score"]),
                        reasons_json=json.dumps(item.get("reasons", []), ensure_ascii=False),
                        penalties_json=json.dumps(item.get("penalties", []), ensure_ascii=False),
                    )
                )
                created += 1
        session.commit()
    return created


def list_segments(project_root: Path, clip_id: str | None = None) -> list[Segment]:
    project = get_project(project_root)
    with get_session(project_root) as session:
        statement = select(Segment).where(Segment.project_id == project.id)
        if clip_id:
            statement = statement.where(Segment.clip_id == clip_id)
        statement = statement.order_by(col(Segment.clip_id), col(Segment.start_seconds))
        return list(session.exec(statement).all())


def update_segment_review(
    project_root: Path,
    segment_id: str,
    *,
    status: SegmentStatus | None = None,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    user_note: str | None = None,
) -> Segment:
    get_project(project_root)
    with get_session(project_root) as session:
        segment = session.get(Segment, segment_id)
        if segment is None:
            raise SegmentNotFoundError(f"No existe el segmento {segment_id}.")
        new_start = segment.start_seconds if start_seconds is None else start_seconds
        new_end = segment.end_seconds if end_seconds is None else end_seconds
        if new_start < 0 or new_end <= new_start:
            raise ValueError("El intervalo debe cumplir 0 <= inicio < fin.")
        if start_seconds is not None or end_seconds is not None:
            _ensure_no_overlap(session, segment.clip_id, new_start, new_end, segment_id)
        segment.start_seconds = new_start
        segment.end_seconds = new_end
        if status is not None:
            segment.status = status
        if user_note is not None:
            segment.user_note = user_note
        segment.updated_at = datetime.now(UTC)
        session.add(segment)
        session.commit()
        session.refresh(segment)
        return segment


def _ensure_no_overlap(
    session: Session,
    clip_id: str,
    start_seconds: float,
    end_seconds: float,
    excluded_segment_id: str | None = None,
) -> None:
    statement = select(Segment).where(Segment.clip_id == clip_id)
    segments = session.exec(statement).all()
    for other in segments:
        overlaps = start_seconds < other.end_seconds and end_seconds > other.start_seconds
        if other.id != excluded_segment_id and overlaps:
            raise ValueError("El intervalo se solapa con otro segmento del clip.")


def segment_to_dict(segment: Segment) -> dict[str, object]:
    return {
        "id": segment.id,
        "clip_id": segment.clip_id,
        "analysis_run_id": segment.analysis_run_id,
        "start_seconds": segment.start_seconds,
        "end_seconds": segment.end_seconds,
        "duration_seconds": round(segment.end_seconds - segment.start_seconds, 3),
        "technical_score": segment.technical_score,
        "reasons": json.loads(segment.reasons_json),
        "penalties": json.loads(segment.penalties_json),
        "status": segment.status.value,
        "user_note": segment.user_note,
    }
