from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import select

from editoragent.domain.models import HumanLabel, LabelingSession
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project


class LabelNotFoundError(LookupError):
    pass


def list_labels(project_root: Path, clip_id: str | None = None) -> list[HumanLabel]:
    project = get_project(project_root)
    with get_session(project_root) as session:
        statement = select(HumanLabel).where(HumanLabel.project_id == project.id)
        if clip_id is not None:
            statement = statement.where(HumanLabel.clip_id == clip_id)
        return list(session.exec(statement).all())


def save_label(project_root: Path, label: HumanLabel) -> HumanLabel:
    project = get_project(project_root)
    if label.project_id != project.id:
        raise ValueError("La etiqueta no pertenece al proyecto activo.")
    if label.start_seconds >= label.end_seconds:
        raise ValueError("El intervalo etiquetado debe tener duración positiva.")
    with get_session(project_root) as session:
        existing = session.get(HumanLabel, label.id)
        if existing is None:
            session.add(label)
            session.commit()
            session.refresh(label)
            return label
        for field in (
            "clip_id",
            "analysis_run_id",
            "segment_id",
            "start_seconds",
            "end_seconds",
            "utility_label",
            "shot_type",
            "motion_quality",
            "rejection_reason",
            "confidence",
            "note",
            "annotator",
        ):
            setattr(existing, field, getattr(label, field))
        existing.updated_at = datetime.now(UTC)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing


def get_label(project_root: Path, label_id: str) -> HumanLabel:
    project = get_project(project_root)
    with get_session(project_root) as session:
        label = session.get(HumanLabel, label_id)
        if label is None or label.project_id != project.id:
            raise LabelNotFoundError(f"Etiqueta no encontrada: {label_id}")
        return label


def start_labeling_session(project_root: Path, clips_total: int) -> LabelingSession:
    project = get_project(project_root)
    with get_session(project_root) as session:
        labeling_session = LabelingSession(project_id=project.id, clips_total=clips_total)
        session.add(labeling_session)
        session.commit()
        session.refresh(labeling_session)
        return labeling_session
