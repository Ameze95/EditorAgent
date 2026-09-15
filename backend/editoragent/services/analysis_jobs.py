from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event, Lock, Thread
from uuid import uuid4

from sqlmodel import select

from editoragent.domain.models import Clip
from editoragent.infrastructure.db import get_session
from editoragent.services import analysis_service
from editoragent.services.project_service import get_project


@dataclass
class AnalysisJob:
    id: str
    project_root: Path
    clip_ids: list[str]
    status: str = "queued"
    completed: int = 0
    current_progress: int = 0
    current_phase: str = "queued"
    current_frames: int = 0
    current_total_frames: int = 0
    current_clip_id: str | None = None
    errors: dict[str, str] = field(default_factory=dict)
    cancel_requested: bool = False
    _cancel: Event = field(default_factory=Event, repr=False)

    @property
    def total(self) -> int:
        return len(self.clip_ids)

    @property
    def progress(self) -> int:
        if not self.total:
            return 100
        return round(((self.completed * 100) + self.current_progress) / self.total)

    def snapshot(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "total": self.total,
            "completed": self.completed,
            "progress": self.progress,
            "current_clip_id": self.current_clip_id,
            "current_progress": self.current_progress,
            "current_phase": self.current_phase,
            "current_frames": self.current_frames,
            "current_total_frames": self.current_total_frames,
            "errors": self.errors.copy(),
        }


class AnalysisJobManager:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._jobs: dict[str, AnalysisJob] = {}
        self._lock = Lock()

    def start(self, project_root: Path, clip_ids: list[str]) -> AnalysisJob:
        job = AnalysisJob(id=str(uuid4()), project_root=project_root, clip_ids=clip_ids)
        with self._lock:
            self._jobs[job.id] = job
        Thread(target=self._run, args=(job,), daemon=True).start()
        return job

    def get(self, job_id: str) -> AnalysisJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> AnalysisJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.cancel_requested = True
                job._cancel.set()
        return job

    def _run(self, job: AnalysisJob) -> None:
        job.status = "running"
        for clip_id in job.clip_ids:
            if job._cancel.is_set():
                job.status = "cancelled"
                job.current_clip_id = None
                return
            job.current_clip_id = clip_id
            job.current_progress = 0
            job.current_phase = "starting"
            job.current_frames = 0
            job.current_total_frames = 0
            try:
                relative_path = self._relative_path(job.project_root, clip_id)
                analysis_service.analyze_clip(
                    job.project_root,
                    relative_path,
                    cancel_event=job._cancel,
                    progress_callback=lambda frames, total, phase: self._update_progress(
                        job, frames, total, phase
                    ),
                )
            except analysis_service.AnalysisCancelledError:
                job.status = "cancelled"
                job.current_clip_id = None
                return
            except Exception as exc:  # noqa: BLE001 - expose per-clip failure to UI
                job.errors[clip_id] = str(exc)
            finally:
                job.completed += 1
                job.current_progress = 0
                job.current_phase = "completed"
                job.current_frames = 0
                job.current_total_frames = 0
        job.current_clip_id = None
        job.status = "failed" if job.errors and job.completed == job.total else "completed"

    @staticmethod
    def _update_progress(job: AnalysisJob, frames: int, total: int, phase: str) -> None:
        job.current_frames = frames
        job.current_total_frames = total
        job.current_phase = phase
        job.current_progress = min(99, round(frames / total * 100)) if total else 0

    def _relative_path(self, project_root: Path, clip_id: str) -> str:
        project = get_project(project_root)
        with get_session(project_root) as session:
            clip = session.exec(
                select(Clip).where(Clip.id == clip_id, Clip.project_id == project.id)
            ).first()
        if clip is None:
            raise ValueError(f"Clip no encontrado: {clip_id}")
        return clip.relative_path
