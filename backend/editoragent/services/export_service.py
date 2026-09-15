"""Export persisted candidate segments without touching source media."""

from __future__ import annotations

import json
from pathlib import Path

from sqlmodel import col, select

from editoragent.analyzers.segments import SegmentCandidate
from editoragent.domain.models import Clip, IngestStatus, MediaRoot, Segment, SegmentStatus
from editoragent.exporters.edl import export_edl_multi
from editoragent.exporters.fcpxml import FCPXMLSource, export_fcpxml, export_fcpxml_multi
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project


class ExportClipNotFoundError(RuntimeError):
    pass


class ExportClipInvalidError(RuntimeError):
    pass


def export_segments_fcpxml(
    project_root: Path,
    relative_path: str,
    segments_json: Path,
    destination: Path,
) -> Path:
    project = get_project(project_root)
    with get_session(project_root) as session:
        clip = session.exec(
            select(Clip).where(
                Clip.project_id == project.id,
                Clip.relative_path == relative_path,
            )
        ).first()
        if clip is None:
            raise ExportClipNotFoundError(f"No existe el clip inspeccionado: {relative_path}")
        if clip.ingest_status != IngestStatus.VALID:
            raise ExportClipInvalidError(
                f"El clip no es exportable porque tiene estado {clip.ingest_status.value}."
            )
        media_root = session.get(MediaRoot, clip.media_root_id)
        if media_root is None or clip.duration_seconds is None:
            raise ExportClipInvalidError("Faltan MediaRoot o duración del clip.")
        source = FCPXMLSource(
            name=Path(relative_path).name,
            path=Path(media_root.path) / relative_path,
            duration_seconds=clip.duration_seconds,
            fps_num=clip.fps_num or 25,
            fps_den=clip.fps_den or 1,
            width=clip.width or 1920,
            height=clip.height or 1080,
        )

    raw_segments = json.loads(segments_json.read_text(encoding="utf-8"))
    segments = [
        SegmentCandidate(
            start_seconds=float(item["start_seconds"]),
            end_seconds=float(item["end_seconds"]),
            technical_score=float(item["technical_score"]),
            reasons=list(item.get("reasons", [])),
            penalties=list(item.get("penalties", [])),
        )
        for item in raw_segments
    ]
    return export_fcpxml(source, segments, destination, project_name=project.name)


def export_approved_fcpxml(project_root: Path) -> tuple[Path, int]:
    """Export every approved segment across all clips in the project.

    Segments are grouped by clip; each clip becomes its own asset in the
    FCPXML, ordered by clip relative_path, so a single timeline can mix
    approved selects from multiple source clips.
    """
    clip_segments, count, project_name = _approved_clip_segments(project_root)
    destination = project_root / "exports" / "approved_selects.fcpxml"
    return (
        export_fcpxml_multi(
            clip_segments, destination, project_name=f"{project_name} approved selects"
        ),
        count,
    )


def export_approved_edl(project_root: Path) -> tuple[Path, int]:
    """Export approved segments as a CMX3600 EDL for Premiere Pro."""
    clip_segments, count, project_name = _approved_clip_segments(project_root)
    destination = project_root / "exports" / "approved_selects.edl"
    output = export_edl_multi(
        clip_segments, destination, title=f"{project_name} approved selects"
    )
    return output, count


def _approved_clip_segments(
    project_root: Path,
) -> tuple[list[tuple[FCPXMLSource, list[SegmentCandidate]]], int, str]:
    project = get_project(project_root)
    with get_session(project_root) as session:
        approved = session.exec(
            select(Segment).where(
                Segment.project_id == project.id,
                Segment.status == SegmentStatus.APPROVED,
            ).order_by(col(Segment.created_at))
        ).all()
        if not approved:
            raise ExportClipInvalidError("No hay segmentos aprobados para exportar.")

        by_clip: dict[str, list[Segment]] = {}
        for segment in approved:
            by_clip.setdefault(segment.clip_id, []).append(segment)

        clip_segments: list[tuple[FCPXMLSource, list[SegmentCandidate]]] = []
        for clip_id, clip_approved in by_clip.items():
            clip = session.get(Clip, clip_id)
            if (
                clip is None
                or clip.duration_seconds is None
                or clip.ingest_status != IngestStatus.VALID
            ):
                raise ExportClipInvalidError(
                    f"El clip aprobado '{clip.relative_path if clip else clip_id}' "
                    "no es exportable."
                )
            media_root = session.get(MediaRoot, clip.media_root_id)
            if media_root is None:
                raise ExportClipInvalidError("No se encuentra el origen de un clip aprobado.")
            source = FCPXMLSource(
                name=Path(clip.relative_path).name,
                path=Path(media_root.path) / clip.relative_path,
                duration_seconds=clip.duration_seconds,
                fps_num=clip.fps_num or 25,
                fps_den=clip.fps_den or 1,
                width=clip.width or 1920,
                height=clip.height or 1080,
            )
            candidates = [
                SegmentCandidate(
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    technical_score=segment.technical_score,
                    reasons=json.loads(segment.reasons_json),
                    penalties=json.loads(segment.penalties_json),
                )
                for segment in clip_approved
            ]
            clip_segments.append((source, candidates))
        clip_segments.sort(key=lambda pair: pair[0].name)

    return clip_segments, len(approved), project.name
