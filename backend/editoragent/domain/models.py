"""Domain models for EditorAgent, persisted via SQLModel/SQLite.

These mirror docs/DATA_MODEL.md. Only the fields needed for the
single-clip inspection slice (Fase 1 / slice 1) are populated today;
the rest of docs/DATA_MODEL.md (AnalysisRun, Segment, Export, ...) is
added in later slices.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return str(uuid.uuid4())


class IngestStatus(StrEnum):
    """Outcome of trying to read a clip's metadata via ffprobe."""

    VALID = "valid"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class AnalysisRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SegmentStatus(StrEnum):
    SUGGESTED = "suggested"
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL = "manual"


class LabelingSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class Project(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    name: str
    root_path: str
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    app_version: str


class MediaRoot(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    path: str
    display_name: str
    added_at: datetime = Field(default_factory=_now)
    # Must be explicitly True: the CLI refuses to add a root otherwise.
    read_only_confirmed: bool


class Clip(SQLModel, table=True):
    id: str = Field(default_factory=_new_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    media_root_id: str = Field(foreign_key="mediaroot.id")
    relative_path: str
    source_fingerprint: str
    duration_seconds: float | None = None
    fps_num: int | None = None
    fps_den: int | None = None
    is_vfr: bool | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    pixel_format: str | None = None
    color_metadata_json: str | None = None
    capture_time: datetime | None = None
    ingest_status: IngestStatus = IngestStatus.ERROR
    error_message: str | None = None
    analyzed_at: datetime = Field(default_factory=_now)


class AnalysisRun(SQLModel, table=True):
    """A single, versioned execution of the technical analyzer over one clip.

    Fase 1 / slice 2 only analyzes sharpness + exposure; motion/stability and
    the final composite score (docs/ANALYSIS_SPEC.md §4) are added later, so
    `config_json` and `analyzer_version` exist to make that partial scope
    explicit and reproducible rather than silently incomplete.
    """

    id: str = Field(default_factory=_new_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    clip_id: str = Field(foreign_key="clip.id")
    profile_name: str
    config_json: str
    config_hash: str
    analyzer_version: str
    started_at: datetime = Field(default_factory=_now)
    finished_at: datetime | None = None
    status: AnalysisRunStatus = AnalysisRunStatus.RUNNING
    error_message: str | None = None
    # Window-level metrics live in a JSON file (see services/analysis_service.py);
    # this keeps this row pointing at it instead of exploding SQLite row counts.
    windows_path: str | None = None
    segments_path: str | None = None


class Segment(SQLModel, table=True):
    """A versioned technical candidate plus the user's review decision."""

    id: str = Field(default_factory=_new_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    clip_id: str = Field(foreign_key="clip.id")
    analysis_run_id: str | None = Field(default=None, foreign_key="analysisrun.id")
    start_seconds: float
    end_seconds: float
    technical_score: float
    reasons_json: str = "[]"
    penalties_json: str = "[]"
    status: SegmentStatus = SegmentStatus.SUGGESTED
    user_note: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class HumanLabel(SQLModel, table=True):
    """Structured human knowledge linked to a clip and optional editorial segment."""

    id: str = Field(default_factory=_new_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    clip_id: str = Field(foreign_key="clip.id")
    analysis_run_id: str | None = Field(default=None, foreign_key="analysisrun.id")
    segment_id: str | None = Field(default=None, foreign_key="segment.id")
    start_seconds: float
    end_seconds: float
    utility_label: str
    shot_type: str | None = None
    motion_quality: str | None = None
    rejection_reason: str | None = None
    confidence: str | None = None
    note: str | None = None
    annotator: str = "local-user"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class LabelingSession(SQLModel, table=True):
    """Progress record for a human labeling session."""

    id: str = Field(default_factory=_new_id, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    annotator: str = "local-user"
    status: LabelingSessionStatus = LabelingSessionStatus.ACTIVE
    clips_total: int = 0
    clips_completed: int = 0
    labels_count: int = 0
    started_at: datetime = Field(default_factory=_now)
    finished_at: datetime | None = None
