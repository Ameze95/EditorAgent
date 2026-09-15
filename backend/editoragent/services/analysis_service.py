"""Orchestrates a single-clip technical analysis run (sharpness + exposure only).

Fase 1 / slice 2. Follows ADR-005: one clip per invocation. Requires the
clip to have been inspected already (`media inspect`) with ingest_status
"valid"; it never re-probes metadata itself.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Any, cast

from sqlmodel import select

from editoragent.analyzers.frame_sampler import sample_frames
from editoragent.analyzers.segments import SegmentCandidate, SegmentConfig, build_segments
from editoragent.analyzers.windowing import WindowMetrics, build_windows, compute_frame_metrics
from editoragent.domain.models import (
    AnalysisRun,
    AnalysisRunStatus,
    Clip,
    IngestStatus,
    MediaRoot,
    Segment,
)
from editoragent.infrastructure.db import get_session
from editoragent.services.project_service import get_project

ANALYZER_VERSION = "0.2.0-sharpness-exposure-proxy"
logger = logging.getLogger(__name__)
DEFAULT_PROFILE = "cinematic_drone_v1"
DEFAULT_SAMPLE_FPS = 4.0
DEFAULT_WINDOW_SECONDS = 3.0
DEFAULT_OVERLAP_RATIO = 0.5

PROFILE_DEFAULTS: dict[str, dict[str, float]] = {
    "cinematic_drone_v1": {
        "enter_threshold": 0.72,
        "exit_threshold": 0.62,
        "minimum_duration_seconds": 4.0,
        "critical_jerk_threshold": 0.55,
        "critical_hard_turn_ratio": 0.15,
        "critical_hard_brake_ratio": 0.15,
    },
    "cinematic_traveling_v1": {
        "enter_threshold": 0.68,
        "exit_threshold": 0.56,
        "minimum_duration_seconds": 3.0,
        "critical_jerk_threshold": 0.68,
        "critical_hard_turn_ratio": 0.25,
        "critical_hard_brake_ratio": 0.20,
    },
    "fpv_controlled_v1": {
        "enter_threshold": 0.64,
        "exit_threshold": 0.50,
        "minimum_duration_seconds": 2.5,
        "critical_jerk_threshold": 0.78,
        "critical_hard_turn_ratio": 0.35,
        "critical_hard_brake_ratio": 0.28,
    },
    "static_aerial_v1": {
        "enter_threshold": 0.78,
        "exit_threshold": 0.70,
        "minimum_duration_seconds": 4.0,
        "critical_jerk_threshold": 0.40,
        "critical_hard_turn_ratio": 0.10,
        "critical_hard_brake_ratio": 0.10,
    },
    "recall_high_v1": {
        "enter_threshold": 0.58,
        "exit_threshold": 0.46,
        "minimum_duration_seconds": 2.0,
        "critical_jerk_threshold": 0.80,
        "critical_hard_turn_ratio": 0.40,
        "critical_hard_brake_ratio": 0.35,
    },
}


class ClipNotFoundError(RuntimeError):
    pass


class ClipNotIngestedError(RuntimeError):
    pass


class AnalysisCancelledError(RuntimeError):
    pass


def available_profiles() -> list[str]:
    return sorted(PROFILE_DEFAULTS)


@dataclass(frozen=True)
class AnalysisConfig:
    profile_name: str = DEFAULT_PROFILE
    sample_fps: float = DEFAULT_SAMPLE_FPS
    window_seconds: float = DEFAULT_WINDOW_SECONDS
    overlap_ratio: float = DEFAULT_OVERLAP_RATIO
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

    @classmethod
    def from_profile(cls, profile_name: str, **overrides: float) -> AnalysisConfig:
        if profile_name not in PROFILE_DEFAULTS:
            available = ", ".join(available_profiles())
            raise ValueError(f"Perfil desconocido '{profile_name}'. Disponibles: {available}")
        values = {**PROFILE_DEFAULTS[profile_name], **overrides}
        return replace(cls(profile_name=profile_name), **cast(Any, values))

    def config_hash(self) -> str:
        payload = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def segment_config(self) -> SegmentConfig:
        return SegmentConfig(
            enter_threshold=self.enter_threshold,
            exit_threshold=self.exit_threshold,
            minimum_duration_seconds=self.minimum_duration_seconds,
            merge_gap_seconds=self.merge_gap_seconds,
            handle_seconds=self.handle_seconds,
            critical_jerk_threshold=self.critical_jerk_threshold,
            critical_stability_floor=self.critical_stability_floor,
            critical_tracking_floor=self.critical_tracking_floor,
            critical_hard_turn_ratio=self.critical_hard_turn_ratio,
            critical_hard_brake_ratio=self.critical_hard_brake_ratio,
        )


@dataclass(frozen=True)
class AnalysisSummary:
    analysis_run: AnalysisRun
    windows: list[WindowMetrics]
    segments: list[SegmentCandidate]
    frames_processed: int
    elapsed_seconds: float


def _resolve_clip_and_path(
    project_root: Path, relative_path: str
) -> tuple[Clip, Path]:
    project = get_project(project_root)
    with get_session(project_root) as session:
        clip = session.exec(
            select(Clip).where(
                Clip.project_id == project.id,
                Clip.relative_path == relative_path,
            )
        ).first()
        if clip is None:
            raise ClipNotFoundError(
                f"No hay ningún clip inspeccionado con ruta relativa '{relative_path}'. "
                "Ejecuta 'media inspect' primero."
            )
        if clip.ingest_status != IngestStatus.VALID:
            raise ClipNotIngestedError(
                f"El clip '{relative_path}' tiene ingest_status="
                f"{clip.ingest_status.value}, no se puede analizar."
            )
        media_root = session.get(MediaRoot, clip.media_root_id)
        assert media_root is not None  # invariant: clip always has a valid root
        video_path = Path(media_root.path) / clip.relative_path
        return clip, video_path


def analyze_clip(
    project_root: Path,
    relative_path: str,
    config: AnalysisConfig | None = None,
    cancel_event: Event | None = None,
    progress_callback: Any = None,
) -> AnalysisSummary:
    config = config or AnalysisConfig()
    project = get_project(project_root)
    clip, video_path = _resolve_clip_and_path(project_root, relative_path)

    with get_session(project_root) as session:
        run = AnalysisRun(
            project_id=project.id,
            clip_id=clip.id,
            profile_name=config.profile_name,
            config_json=json.dumps(config.__dict__),
            config_hash=config.config_hash(),
            analyzer_version=ANALYZER_VERSION,
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        started = time.monotonic()
        estimated_frames = max(1, round((clip.duration_seconds or 0.0) * config.sample_fps))
        if progress_callback is not None:
            progress_callback(0, estimated_frames, "sampling")
        logger.info(
            "Analysis started clip=%s profile=%s estimated_frames=%s",
            clip.relative_path,
            config.profile_name,
            estimated_frames,
        )
        try:
            frame_metrics = []
            previous_gray = None
            for frame in sample_frames(
                video_path,
                config.sample_fps,
                source_width=clip.width or 640,
                source_height=clip.height or 360,
                cancel_event=cancel_event,
            ):
                if cancel_event is not None and cancel_event.is_set():
                    raise AnalysisCancelledError("Análisis cancelado por el usuario.")
                frame_metrics.append(compute_frame_metrics(frame, previous_gray))
                previous_gray = frame.gray
                if progress_callback is not None and len(frame_metrics) % 10 == 0:
                    progress_callback(len(frame_metrics), estimated_frames, "sampling")
                    logger.info(
                        "Analysis progress clip=%s frames=%s/%s",
                        clip.relative_path,
                        len(frame_metrics),
                        estimated_frames,
                    )
            if cancel_event is not None and cancel_event.is_set():
                raise AnalysisCancelledError("Análisis cancelado por el usuario.")
            duration = clip.duration_seconds or (
                frame_metrics[-1].timestamp_seconds if frame_metrics else 0.0
            )
            windows = build_windows(
                frame_metrics,
                duration_seconds=duration,
                window_seconds=config.window_seconds,
                overlap_ratio=config.overlap_ratio,
            )
            segments = build_segments(
                windows,
                clip_duration_seconds=duration,
                config=config.segment_config(),
            )
            if progress_callback is not None:
                progress_callback(len(frame_metrics), estimated_frames, "finalizing")
        except AnalysisCancelledError as exc:
            run.status = AnalysisRunStatus.CANCELLED
            run.error_message = str(exc)
            session.add(run)
            session.commit()
            raise
        except Exception as exc:  # noqa: BLE001 - persist any failure, then re-raise
            run.status = AnalysisRunStatus.FAILED
            run.error_message = str(exc)
            session.add(run)
            session.commit()
            raise

        elapsed = time.monotonic() - started
        logger.info(
            "Analysis completed clip=%s frames=%s segments=%s elapsed=%.1fs",
            clip.relative_path,
            len(frame_metrics),
            len(segments),
            elapsed,
        )
        windows_path = project_root / "analysis" / f"{run.id}_windows.json"
        windows_path.parent.mkdir(parents=True, exist_ok=True)
        windows_path.write_text(
            json.dumps([w.__dict__ for w in windows], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        segments_path = project_root / "analysis" / f"{run.id}_segments.json"
        segments_path.write_text(
            json.dumps([segment.__dict__ for segment in segments], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        run.status = AnalysisRunStatus.COMPLETED
        run.windows_path = str(windows_path)
        run.segments_path = str(segments_path)
        run.finished_at = datetime.now(UTC)
        session.add(run)
        previous_segments = session.exec(
            select(Segment).where(Segment.clip_id == clip.id)
        ).all()
        matched_previous: set[str] = set()
        for candidate in segments:
            previous = next(
                (
                    item
                    for item in previous_segments
                    if item.id not in matched_previous
                    and _interval_iou(
                        candidate.start_seconds,
                        candidate.end_seconds,
                        item.start_seconds,
                        item.end_seconds,
                    )
                    >= 0.5
                ),
                None,
            )
            if previous is None:
                session.add(
                    Segment(
                        project_id=project.id,
                        clip_id=clip.id,
                        analysis_run_id=run.id,
                        start_seconds=candidate.start_seconds,
                        end_seconds=candidate.end_seconds,
                        technical_score=candidate.technical_score,
                        reasons_json=json.dumps(candidate.reasons, ensure_ascii=False),
                        penalties_json=json.dumps(candidate.penalties, ensure_ascii=False),
                    )
                )
                continue
            matched_previous.add(previous.id)
            previous.analysis_run_id = run.id
            previous.start_seconds = candidate.start_seconds
            previous.end_seconds = candidate.end_seconds
            previous.technical_score = candidate.technical_score
            previous.reasons_json = json.dumps(candidate.reasons, ensure_ascii=False)
            previous.penalties_json = json.dumps(candidate.penalties, ensure_ascii=False)
            previous.updated_at = datetime.now(UTC)
            session.add(previous)
        for previous in previous_segments:
            if previous.id not in matched_previous:
                session.delete(previous)
        session.commit()
        session.refresh(run)

        return AnalysisSummary(
            analysis_run=run,
            windows=windows,
            segments=segments,
            frames_processed=len(frame_metrics),
            elapsed_seconds=elapsed,
        )


def _interval_iou(
    first_start: float,
    first_end: float,
    second_start: float,
    second_end: float,
) -> float:
    intersection = max(0.0, min(first_end, second_end) - max(first_start, second_start))
    union = max(first_end, second_end) - min(first_start, second_start)
    return intersection / union if union > 0 else 0.0
