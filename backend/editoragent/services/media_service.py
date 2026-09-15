"""Media ingestion: register read-only source folders and inspect single clips.

Fase 1 / slice 1 (see docs/DECISIONS.md ADR-005) processes one clip per
invocation on purpose, so each result can be checked manually before any
batch/folder scan is built on top of this same logic.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from editoragent.domain.models import Clip, IngestStatus, MediaRoot
from editoragent.infrastructure import ffprobe
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project

# Reference format per docs/DECISIONS.md ADR-004: DJI Avata 2, .MP4, H.265/HEVC.
# Anything else is recorded but flagged as unsupported rather than guessed at.
SUPPORTED_EXTENSIONS = {".mp4"}
SUPPORTED_CODECS = {"hevc", "h264"}


class MediaRootAlreadyExistsError(RuntimeError):
    pass


class NoMatchingMediaRootError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScanResult:
    media_root: MediaRoot
    inspected: int
    valid: int
    unsupported: int
    errored: int
    skipped_existing_root: bool


def add_media_root(
    project_root: Path,
    source_folder: Path,
    *,
    confirm_read_only: bool,
    display_name: str | None = None,
) -> MediaRoot:
    if not confirm_read_only:
        raise ValueError(
            "Debes confirmar explícitamente que la carpeta se trata en modo "
            "sólo lectura (--confirm-read-only)."
        )
    source_folder = source_folder.resolve()
    project = get_project(project_root)
    with get_session(project_root) as session:
        existing = session.exec(
            select(MediaRoot).where(
                MediaRoot.project_id == project.id,
                MediaRoot.path == str(source_folder),
            )
        ).first()
        if existing is not None:
            raise MediaRootAlreadyExistsError(
                f"{source_folder} ya está registrada como MediaRoot (id={existing.id})."
            )
        media_root = MediaRoot(
            project_id=project.id,
            path=str(source_folder),
            display_name=display_name or source_folder.name,
            read_only_confirmed=True,
        )
        session.add(media_root)
        session.commit()
        session.refresh(media_root)
        return media_root


def scan_media_root(project_root: Path, source_folder: Path) -> ScanResult:
    """Register (or reuse) a media root and inspect every supported file in it.

    Batch counterpart of `inspect_clip`: lets a UI "add more clips" to an
    existing project without dropping to the CLI, reusing the same per-file
    inspection logic and never touching originals.
    """
    source_folder = source_folder.resolve()
    if not source_folder.is_dir():
        raise FileNotFoundError(f"No existe la carpeta {source_folder}.")

    skipped_existing_root = False
    try:
        media_root = add_media_root(project_root, source_folder, confirm_read_only=True)
    except MediaRootAlreadyExistsError:
        project = get_project(project_root)
        with get_session(project_root) as session:
            media_root = session.exec(
                select(MediaRoot).where(
                    MediaRoot.project_id == project.id,
                    MediaRoot.path == str(source_folder),
                )
            ).one()
        skipped_existing_root = True

    valid = unsupported = errored = 0
    inspected = 0
    for path in sorted(source_folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        result = inspect_clip(project_root, path)
        inspected += 1
        if result.clip.ingest_status == IngestStatus.VALID:
            valid += 1
        elif result.clip.ingest_status == IngestStatus.UNSUPPORTED:
            unsupported += 1
        else:
            errored += 1

    return ScanResult(
        media_root=media_root,
        inspected=inspected,
        valid=valid,
        unsupported=unsupported,
        errored=errored,
        skipped_existing_root=skipped_existing_root,
    )


def _find_media_root(session: Session, project_id: str, video_path: Path) -> MediaRoot:
    roots = session.exec(
        select(MediaRoot).where(MediaRoot.project_id == project_id)
    ).all()
    for root in roots:
        try:
            video_path.relative_to(root.path)
        except ValueError:
            continue
        return root
    raise NoMatchingMediaRootError(
        f"{video_path} no está dentro de ningún MediaRoot registrado. "
        "Usa 'media add-root' primero."
    )


def _fingerprint(video_path: Path) -> str:
    stat = video_path.stat()
    raw = f"{stat.st_size}:{stat.st_mtime_ns}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InspectionResult:
    clip: Clip
    diagnostics_path: Path


def inspect_clip(project_root: Path, video_path: Path) -> InspectionResult:
    video_path = video_path.resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"No existe el archivo {video_path}.")

    project = get_project(project_root)

    with get_session(project_root) as session:
        media_root = _find_media_root(session, project.id, video_path)
        relative_path = str(video_path.relative_to(media_root.path))
        fingerprint = _fingerprint(video_path)

        clip = session.exec(
            select(Clip).where(
                Clip.project_id == project.id,
                Clip.media_root_id == media_root.id,
                Clip.relative_path == relative_path,
            )
        ).first() or Clip(
            project_id=project.id,
            media_root_id=media_root.id,
            relative_path=relative_path,
            source_fingerprint=fingerprint,
        )
        clip.source_fingerprint = fingerprint

        if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            clip.ingest_status = IngestStatus.UNSUPPORTED
            clip.error_message = f"Extensión no soportada: {video_path.suffix}"
        else:
            clip.ingest_status, clip.error_message = _probe_into_clip(clip, video_path)

        session.add(clip)
        session.commit()
        session.refresh(clip)

        diagnostics_path = _write_diagnostics(project_root, clip)
        return InspectionResult(clip=clip, diagnostics_path=diagnostics_path)


def _probe_into_clip(clip: Clip, video_path: Path) -> tuple[IngestStatus, str | None]:
    try:
        raw = ffprobe.run_ffprobe(video_path)
        metadata = ffprobe.normalize_probe(raw)
    except ffprobe.NoVideoStreamError as exc:
        return IngestStatus.ERROR, str(exc)
    except ffprobe.FfprobeExecutionError as exc:
        return IngestStatus.ERROR, str(exc)

    clip.duration_seconds = metadata.duration_seconds
    clip.fps_num = metadata.fps_num
    clip.fps_den = metadata.fps_den
    clip.is_vfr = metadata.is_vfr
    clip.width = metadata.width
    clip.height = metadata.height
    clip.codec = metadata.codec
    clip.pixel_format = metadata.pixel_format
    clip.color_metadata_json = json.dumps(metadata.color_metadata)
    clip.capture_time = metadata.capture_time

    if metadata.codec not in SUPPORTED_CODECS:
        return IngestStatus.UNSUPPORTED, f"Codec no soportado todavía: {metadata.codec}"
    return IngestStatus.VALID, None


def _write_diagnostics(project_root: Path, clip: Clip) -> Path:
    clips_dir = project_root / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_path = clips_dir / f"{clip.id}.json"
    diagnostics_path.write_text(clip.model_dump_json(indent=2), encoding="utf-8")
    return diagnostics_path
