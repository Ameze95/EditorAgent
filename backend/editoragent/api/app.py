"""Local FastAPI contract for the review UI."""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Annotated, cast

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlmodel import col, select

from editoragent.domain.models import (
    AnalysisRun,
    Clip,
    HumanLabel,
    MediaRoot,
    Segment,
    SegmentStatus,
)
from editoragent.infrastructure.db import get_session
from editoragent.services.analysis_jobs import AnalysisJobManager
from editoragent.services.analysis_service import (
    PROFILE_DEFAULTS,
    PROFILE_METADATA,
    AnalysisConfig,
)
from editoragent.services.dataset_export_service import (
    export_dataset_csv,
    export_dataset_json,
)
from editoragent.services.evaluation_service import evaluate_windows_data
from editoragent.services.export_service import (
    ExportClipInvalidError,
    export_approved_edl,
    export_approved_fcpxml,
)
from editoragent.services.label_service import list_labels, save_label, start_labeling_session
from editoragent.services.learning_monitor_service import learning_summary
from editoragent.services.media_service import scan_media_root
from editoragent.services.project_service import (
    ProjectAlreadyExistsError,
    ProjectOperationError,
    create_project,
    delete_project,
    get_project,
    registered_project_roots,
    update_project,
)
from editoragent.services.proxy_service import ProxyGenerationError, ensure_analysis_proxy
from editoragent.services.review_service import (
    SegmentNotFoundError,
    backfill_segments_from_analysis,
    create_manual_segment,
    list_segments,
    segment_to_dict,
    update_segment_review,
)


class ReviewUpdate(BaseModel):
    status: SegmentStatus | None = None
    start_seconds: float | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, gt=0)
    user_note: str | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_path: str | None = Field(default=None, min_length=1)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_path: str | None = Field(default=None, min_length=1)


class ScanFolderRequest(BaseModel):
    folder_path: str = Field(min_length=1)


class AnnotationInterval(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    label: str
    reason: str | None = None
    confidence: str | None = None


class AnnotationDocument(BaseModel):
    intent_profile: str = "cinematic"
    intervals: list[AnnotationInterval]


class HumanLabelPayload(BaseModel):
    id: str | None = None
    clip_id: str
    analysis_run_id: str | None = None
    segment_id: str | None = None
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    utility_label: str
    capture_type: str | None = None
    motion_intent: str | None = None
    shot_type: str | None = None
    motion_quality: str | None = None
    rejection_reason: str | None = None
    technical_issues: list[str] = Field(default_factory=list)
    confidence: str | None = None
    note: str | None = None
    annotator: str = "local-user"


class ManualSegmentPayload(BaseModel):
    clip_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)


class AnalyzeOverrides(BaseModel):
    profile_name: str | None = None
    sample_fps: float | None = Field(default=None, gt=0, le=30)
    window_seconds: float | None = Field(default=None, gt=0, le=10)
    overlap_ratio: float | None = Field(default=None, ge=0, lt=1)
    enter_threshold: float | None = Field(default=None, gt=0, le=1)
    exit_threshold: float | None = Field(default=None, gt=0, le=1)
    minimum_duration_seconds: float | None = Field(default=None, gt=0)
    merge_gap_seconds: float | None = Field(default=None, ge=0)
    handle_seconds: float | None = Field(default=None, ge=0)
    critical_jerk_threshold: float | None = Field(default=None, gt=0, le=1)
    critical_stability_floor: float | None = Field(default=None, ge=0, le=1)
    critical_tracking_floor: float | None = Field(default=None, ge=0, le=1)
    critical_hard_turn_ratio: float | None = Field(default=None, gt=0, le=1)
    critical_hard_brake_ratio: float | None = Field(default=None, gt=0, le=1)
    weight_sharpness: float | None = Field(default=None, ge=0, le=1)
    weight_exposure: float | None = Field(default=None, ge=0, le=1)
    weight_direction: float | None = Field(default=None, ge=0, le=1)
    weight_tracking: float | None = Field(default=None, ge=0, le=1)
    weight_stability: float | None = Field(default=None, ge=0, le=1)


def _build_analysis_config(overrides: AnalyzeOverrides | None) -> AnalysisConfig | None:
    if overrides is None:
        return None
    values = overrides.model_dump(exclude_none=True, exclude={"profile_name"})
    return AnalysisConfig.from_profile(overrides.profile_name or "cinematic_drone_v1", **values)


def _resolve_analysis_artifact(project_root: Path, stored_path: str) -> Path:
    """Resolve an artifact after a project folder move without leaving its root."""
    candidate = Path(stored_path)
    if candidate.is_file():
        return candidate
    fallback = project_root / "analysis" / candidate.name
    return fallback


def create_app(project_root: Path, workspace_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="EditorAgent local API", version="0.1.0")
    workspace = (workspace_root or project_root.parent).resolve()
    active_project = {"root": project_root.resolve()}
    analysis_jobs = AnalysisJobManager(active_project["root"])
    backfill_segments_from_analysis(active_project["root"])
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    extra_origins = os.environ.get("EDITORAGENT_ALLOWED_ORIGINS", "")
    allowed_origins.extend(origin.strip() for origin in extra_origins.split(",") if origin.strip())
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["DELETE", "GET", "POST", "PUT", "PATCH"],
        allow_headers=["Content-Type"],
    )

    def current_root() -> Path:
        return active_project["root"]

    @app.get("/projects")
    def projects() -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        for root in registered_project_roots(workspace):
            if not (root / "editoragent.db").exists():
                continue
            project = get_project(root)
            result.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "root_path": str(root),
                    "active": root == current_root(),
                }
            )
        return sorted(result, key=lambda item: str(item["name"]).lower())

    @app.post("/projects")
    def create_project_endpoint(payload: ProjectCreate) -> dict[str, object]:
        safe_name = re.sub(
            r"[^a-zA-Z0-9_-]+", "_", payload.name
        ).strip("_")
        if not safe_name:
            raise HTTPException(status_code=422, detail="El nombre no produce una carpeta válida.")
        parent = (
            Path(payload.parent_path).expanduser().resolve()
            if payload.parent_path
            else workspace / "projects"
        )
        root = parent / safe_name
        try:
            project = create_project(payload.name, root, workspace)
        except (ProjectOperationError, ProjectAlreadyExistsError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"id": project.id, "name": project.name, "root_path": str(root), "active": False}

    @app.get("/active-project")
    def active_project_endpoint() -> dict[str, object]:
        project = get_project(current_root())
        return {"id": project.id, "name": project.name, "root_path": str(current_root())}

    @app.post("/active-project/{project_id}")
    def select_project(project_id: str) -> dict[str, object]:
        for root in registered_project_roots(workspace):
            if not (root / "editoragent.db").exists():
                continue
            candidate = get_project(root)
            if candidate.id == project_id:
                active_project["root"] = root.resolve()
                backfill_segments_from_analysis(active_project["root"])
                return {
                    "id": candidate.id,
                    "name": candidate.name,
                    "root_path": str(root),
                }
        raise HTTPException(status_code=404, detail="Proyecto no encontrado en este workspace.")

    @app.patch("/projects/{project_id}")
    def update_project_endpoint(project_id: str, payload: ProjectUpdate) -> dict[str, object]:
        for root in registered_project_roots(workspace):
            if not (root / "editoragent.db").exists():
                continue
            candidate = get_project(root)
            if candidate.id != project_id:
                continue
            target = None
            if payload.parent_path:
                safe_name = re.sub(
                    r"[^a-zA-Z0-9_-]+", "_", payload.name or candidate.name
                ).strip("_")
                target = Path(payload.parent_path).expanduser().resolve() / safe_name
            try:
                updated = update_project(workspace, root, name=payload.name, target_root=target)
            except (ProjectOperationError, LookupError) as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            if active_project["root"] == root.resolve():
                active_project["root"] = Path(updated.root_path)
            return {
                "id": updated.id,
                "name": updated.name,
                "root_path": updated.root_path,
                "active": active_project["root"] == Path(updated.root_path),
            }
        raise HTTPException(status_code=404, detail="Proyecto no encontrado en este workspace.")

    @app.delete("/projects/{project_id}")
    def delete_project_endpoint(project_id: str) -> dict[str, str]:
        for root in registered_project_roots(workspace):
            if not (root / "editoragent.db").exists():
                continue
            candidate = get_project(root)
            if candidate.id == project_id:
                try:
                    delete_project(workspace, root)
                except (ProjectOperationError, LookupError) as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc
                if active_project["root"] == root.resolve():
                    active_project["root"] = project_root.resolve()
                return {"status": "deleted"}
        raise HTTPException(status_code=404, detail="Proyecto no encontrado en este workspace.")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/analysis/profiles")
    def analysis_profiles() -> list[dict[str, object]]:
        return [
            {
                "name": name,
                **PROFILE_METADATA.get(name, {}),
                "parameters": {
                    key: value
                    for key, value in AnalysisConfig.from_profile(name).__dict__.items()
                    if key != "profile_name"
                },
            }
            for name in sorted(PROFILE_DEFAULTS)
        ]

    @app.post("/labeling/sessions")
    def create_labeling_session() -> dict[str, object]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            clips_total = len(session.exec(select(Clip).where(Clip.project_id == project.id)).all())
        labeling_session = start_labeling_session(current_root(), clips_total)
        return {
            "id": labeling_session.id,
            "status": labeling_session.status.value,
            "clips_total": labeling_session.clips_total,
            "clips_completed": labeling_session.clips_completed,
            "labels_count": labeling_session.labels_count,
        }

    @app.get("/learning/summary")
    def learning_summary_endpoint() -> dict[str, object]:
        return learning_summary(current_root())

    @app.get("/labels")
    def labels(clip_id: Annotated[str | None, Query()] = None) -> list[dict[str, object]]:
        return [
            {
                "id": label.id,
                "clip_id": label.clip_id,
                "analysis_run_id": label.analysis_run_id,
                "segment_id": label.segment_id,
                "start_seconds": label.start_seconds,
                "end_seconds": label.end_seconds,
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
            for label in list_labels(current_root(), clip_id)
        ]

    @app.put("/labels")
    def put_label(payload: HumanLabelPayload) -> dict[str, object]:
        project = get_project(current_root())
        label = save_label(
            current_root(),
            HumanLabel(
                id=payload.id or str(uuid.uuid4()),
                project_id=project.id,
                clip_id=payload.clip_id,
                analysis_run_id=payload.analysis_run_id,
                segment_id=payload.segment_id,
                start_seconds=payload.start_seconds,
                end_seconds=payload.end_seconds,
                utility_label=payload.utility_label,
                capture_type=payload.capture_type,
                motion_intent=payload.motion_intent,
                shot_type=payload.shot_type,
                motion_quality=payload.motion_quality,
                rejection_reason=payload.rejection_reason,
                technical_issues_json=json.dumps(payload.technical_issues),
                confidence=payload.confidence,
                note=payload.note,
                annotator=payload.annotator,
            ),
        )
        return {
            "id": label.id,
            "clip_id": label.clip_id,
            "analysis_run_id": label.analysis_run_id,
            "segment_id": label.segment_id,
            "start_seconds": label.start_seconds,
            "end_seconds": label.end_seconds,
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

    @app.get("/analysis/runs")
    def analysis_runs(clip_id: Annotated[str | None, Query()] = None) -> list[dict[str, object]]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            statement = select(AnalysisRun).where(AnalysisRun.project_id == project.id)
            if clip_id is not None:
                statement = statement.where(AnalysisRun.clip_id == clip_id)
            runs = session.exec(statement).all()
            return [
                {
                    "id": run.id,
                    "clip_id": run.clip_id,
                    "profile_name": run.profile_name,
                    "status": run.status.value,
                    "started_at": run.started_at.isoformat(),
                    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                    "windows_path": run.windows_path,
                    "windows_available": bool(
                        run.windows_path
                        and _resolve_analysis_artifact(current_root(), run.windows_path).is_file()
                    ),
                }
                for run in runs
            ]

    @app.get("/analysis/runs/{run_id}/windows")
    def analysis_windows(run_id: str) -> list[dict[str, object]]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            run = session.get(AnalysisRun, run_id)
            if run is None or run.project_id != project.id or not run.windows_path:
                raise HTTPException(status_code=404, detail="Ejecución de análisis no encontrada.")
            windows_path = _resolve_analysis_artifact(current_root(), run.windows_path)
        if not windows_path.is_file():
            raise HTTPException(status_code=404, detail="No se encuentra el artefacto de ventanas.")
        payload = json.loads(windows_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise HTTPException(status_code=500, detail="El artefacto de ventanas no es válido.")
        return cast(list[dict[str, object]], [item for item in payload if isinstance(item, dict)])

    @app.get("/evaluation/annotations/{run_id}")
    def get_annotations(run_id: str) -> dict[str, object]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            run = session.get(AnalysisRun, run_id)
            if run is None or run.project_id != project.id:
                raise HTTPException(status_code=404, detail="Ejecución de análisis no encontrada.")
        path = current_root() / "evaluation" / "annotations" / f"{run_id}.json"
        if not path.is_file():
            return {"intent_profile": "cinematic", "intervals": []}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise HTTPException(status_code=500, detail="El archivo de anotaciones no es válido.")
        return cast(dict[str, object], payload)

    @app.get("/analysis/runs/{run_id}/metrics")
    def analysis_run_metrics(
        run_id: str,
        enter_threshold: Annotated[float, Query(gt=0, le=1)] = 0.72,
        top_k: Annotated[int, Query(ge=1)] = 5,
    ) -> dict[str, object]:
        """Preview precision/recall/IoU for a threshold against the run's own annotations."""
        project = get_project(current_root())
        with get_session(current_root()) as session:
            run = session.get(AnalysisRun, run_id)
            if run is None or run.project_id != project.id or not run.windows_path:
                raise HTTPException(status_code=404, detail="Ejecución de análisis no encontrada.")
            windows_path = _resolve_analysis_artifact(current_root(), run.windows_path)
        if not windows_path.is_file():
            raise HTTPException(status_code=404, detail="No se encuentra el artefacto de ventanas.")
        windows = json.loads(windows_path.read_text(encoding="utf-8"))
        try:
            config = json.loads(run.config_json)
        except json.JSONDecodeError:
            config = {}
        score_weights = {
            name.removeprefix("weight_"): float(config[name])
            for name in (
                "weight_sharpness",
                "weight_exposure",
                "weight_direction",
                "weight_tracking",
                "weight_stability",
            )
            if name in config
        }
        annotations_path = current_root() / "evaluation" / "annotations" / f"{run_id}.json"
        intervals: list[dict[str, object]] = []
        if annotations_path.is_file():
            document = json.loads(annotations_path.read_text(encoding="utf-8"))
            intervals = document.get("intervals", []) if isinstance(document, dict) else []
        return evaluate_windows_data(
            windows,
            intervals,
            enter_threshold=enter_threshold,
            top_k=top_k,
            score_weights=score_weights or None,
        )

    @app.put("/evaluation/annotations/{run_id}")
    def save_annotations(run_id: str, document: AnnotationDocument) -> dict[str, object]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            run = session.get(AnalysisRun, run_id)
            if run is None or run.project_id != project.id:
                raise HTTPException(status_code=404, detail="Ejecución de análisis no encontrada.")
        path = current_root() / "evaluation" / "annotations" / f"{run_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = document.model_dump()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return payload

    @app.post("/dialogs/select-folder")
    def select_folder_dialog() -> dict[str, str | None]:
        """Open a native OS folder picker (this API runs on the user's own machine)."""
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            chosen = filedialog.askdirectory(title="Selecciona la carpeta de clips")
        finally:
            root.destroy()
        return {"path": chosen or None}

    @app.post("/clips/scan")
    def scan_clips(payload: ScanFolderRequest) -> dict[str, object]:
        try:
            result = scan_media_root(current_root(), Path(payload.folder_path))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "media_root_path": result.media_root.path,
            "inspected": result.inspected,
            "valid": result.valid,
            "unsupported": result.unsupported,
            "errored": result.errored,
            "reused_existing_root": result.skipped_existing_root,
        }

    @app.get("/clips")
    def clips() -> list[dict[str, object]]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            rows = session.exec(
                select(Clip).where(Clip.project_id == project.id)
            ).all()
            return [
                {
                    "id": clip.id,
                    "relative_path": clip.relative_path,
                    "duration_seconds": clip.duration_seconds,
                    "width": clip.width,
                    "height": clip.height,
                    "fps_num": clip.fps_num,
                    "fps_den": clip.fps_den,
                    "ingest_status": clip.ingest_status.value,
                    "analysis_status": (
                        latest.status.value if latest is not None else "not_started"
                    ),
                    "segment_count": len(
                        session.exec(
                            select(Segment).where(Segment.clip_id == clip.id)
                        ).all()
                    ),
                }
                for clip in rows
                for latest in [
                    session.exec(
                        select(AnalysisRun)
                        .where(AnalysisRun.clip_id == clip.id)
                        .order_by(col(AnalysisRun.started_at).desc())
                    ).first()
                ]
            ]

    @app.get("/clips/{clip_id}/proxy")
    def clip_proxy(clip_id: str) -> FileResponse:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            clip = session.get(Clip, clip_id)
            if clip is None or clip.project_id != project.id:
                raise HTTPException(status_code=404, detail="Clip no encontrado.")
            media_root = session.get(MediaRoot, clip.media_root_id)
            if media_root is None:
                raise HTTPException(status_code=404, detail="Origen del clip no encontrado.")
            source_path = Path(media_root.path) / clip.relative_path
        try:
            proxy = ensure_analysis_proxy(current_root(), clip, source_path)
        except (FileNotFoundError, ProxyGenerationError) as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return FileResponse(proxy, media_type="video/mp4", filename=proxy.name)

    @app.post("/clips/{clip_id}/analyze")
    def analyze_clip_endpoint(
        clip_id: str, overrides: AnalyzeOverrides | None = None
    ) -> dict[str, object]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            clip = session.get(Clip, clip_id)
            if clip is None or clip.project_id != project.id:
                raise HTTPException(status_code=404, detail="Clip no encontrado.")
        try:
            config = _build_analysis_config(overrides)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        job = analysis_jobs.start(current_root(), [clip_id], config)
        return job.snapshot()

    @app.post("/analysis/all")
    def analyze_all_endpoint() -> dict[str, object]:
        project = get_project(current_root())
        with get_session(current_root()) as session:
            clip_ids = [
                clip.id
                for clip in session.exec(
                    select(Clip).where(Clip.project_id == project.id)
                ).all()
            ]
        if not clip_ids:
            raise HTTPException(status_code=422, detail="No hay clips en el proyecto.")
        job = analysis_jobs.start(current_root(), clip_ids)
        return job.snapshot()

    @app.get("/analysis/jobs/{job_id}")
    def analysis_job_status(job_id: str) -> dict[str, object]:
        job = analysis_jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Trabajo de análisis no encontrado.")
        return job.snapshot()

    @app.delete("/analysis/jobs/{job_id}")
    def cancel_analysis_job(job_id: str) -> dict[str, object]:
        job = analysis_jobs.cancel(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Trabajo de análisis no encontrado.")
        return job.snapshot()

    @app.get("/clips/{clip_id}/media")
    def clip_media(clip_id: str) -> FileResponse:
        """Serve the original read-only for native browser playback."""
        project = get_project(current_root())
        with get_session(current_root()) as session:
            clip = session.get(Clip, clip_id)
            if clip is None or clip.project_id != project.id:
                raise HTTPException(status_code=404, detail="Clip no encontrado.")
            media_root = session.get(MediaRoot, clip.media_root_id)
            if media_root is None:
                raise HTTPException(status_code=404, detail="Origen del clip no encontrado.")
            source_path = Path(media_root.path) / clip.relative_path
        if not source_path.is_file():
            raise HTTPException(status_code=404, detail="Archivo fuente no encontrado.")
        return FileResponse(source_path, media_type="video/mp4", filename=source_path.name)

    @app.get("/segments")
    def segments(
        clip_id: Annotated[str | None, Query()] = None,
    ) -> list[dict[str, object]]:
        return [segment_to_dict(segment) for segment in list_segments(current_root(), clip_id)]

    @app.post("/segments/manual")
    def create_manual_segment_endpoint(payload: ManualSegmentPayload) -> dict[str, object]:
        try:
            segment = create_manual_segment(
                current_root(),
                payload.clip_id,
                start_seconds=payload.start_seconds,
                end_seconds=payload.end_seconds,
            )
        except SegmentNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return segment_to_dict(segment)

    @app.patch("/segments/{segment_id}")
    def review_segment(segment_id: str, update: ReviewUpdate) -> dict[str, object]:
        try:
            segment = update_segment_review(
                current_root(),
                segment_id,
                status=update.status,
                start_seconds=update.start_seconds,
                end_seconds=update.end_seconds,
                user_note=update.user_note,
            )
        except SegmentNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return segment_to_dict(segment)

    @app.post("/exports/fcpxml")
    def export_approved() -> dict[str, object]:
        try:
            destination, count = export_approved_fcpxml(current_root())
        except ExportClipInvalidError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"path": str(destination), "segment_count": count}

    @app.post("/exports/edl")
    def export_approved_edl_endpoint() -> dict[str, object]:
        try:
            destination, count = export_approved_edl(current_root())
        except ExportClipInvalidError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"path": str(destination), "segment_count": count}

    @app.post("/exports/dataset/json")
    def export_dataset_json_endpoint() -> dict[str, object]:
        destination, count = export_dataset_json(current_root())
        return {"path": str(destination), "segment_count": count}

    @app.post("/exports/dataset/csv")
    def export_dataset_csv_endpoint() -> dict[str, object]:
        destination, count = export_dataset_csv(current_root())
        return {"path": str(destination), "segment_count": count}

    return app
