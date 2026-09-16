from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from editoragent.api.app import create_app
from editoragent.domain.models import AnalysisRun, AnalysisRunStatus, Segment, SegmentStatus
from editoragent.infrastructure.db import get_session
from editoragent.services import analysis_service
from editoragent.services.analysis_jobs import AnalysisJobManager
from editoragent.services.project_service import create_project


def test_review_api_lists_and_updates_segment(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project = create_project("UI test", project_root)
    with get_session(project_root) as session:
        segment = Segment(
            project_id=project.id,
            clip_id="clip-1",
            analysis_run_id="run-1",
            start_seconds=2.0,
            end_seconds=8.0,
            technical_score=0.81,
            reasons_json='["Nitidez alta"]',
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
        segment_id = segment.id

    client = TestClient(create_app(project_root))

    assert client.get("/health").json() == {"status": "ok"}
    listed = client.get("/segments?clip_id=clip-1")
    assert listed.status_code == 200
    assert listed.json()[0]["duration_seconds"] == 6.0

    updated = client.patch(
        f"/segments/{segment_id}",
        json={
            "status": "approved",
            "start_seconds": 2.5,
            "end_seconds": 7.5,
            "user_note": "Toma usable",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == SegmentStatus.APPROVED.value
    assert updated.json()["start_seconds"] == 2.5
    assert updated.json()["duration_seconds"] == 5.0


def test_review_api_rejects_invalid_interval(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project = create_project("UI test", project_root)
    with get_session(project_root) as session:
        segment = Segment(
            project_id=project.id,
            clip_id="clip-1",
            analysis_run_id="run-1",
            start_seconds=2.0,
            end_seconds=8.0,
            technical_score=0.81,
        )
        session.add(segment)
        session.commit()
        session.refresh(segment)
        segment_id = segment.id

    client = TestClient(create_app(project_root))
    response = client.patch(
        f"/segments/{segment_id}",
        json={"start_seconds": 9.0, "end_seconds": 4.0},
    )

    assert response.status_code == 422


def test_project_api_lists_creates_and_switches_projects(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    first_root = workspace / "first"
    create_project("First", first_root)
    client = TestClient(create_app(first_root, workspace))

    listed = client.get("/projects")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "First"

    created = client.post("/projects", json={"name": "Second Project"})
    assert created.status_code == 200
    second_id = created.json()["id"]

    selected = client.post(f"/active-project/{second_id}")
    assert selected.status_code == 200
    assert selected.json()["name"] == "Second Project"


def test_project_api_can_rename_move_and_delete_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    project_root = workspace / "projects" / "first"
    create_project("First", project_root)
    client = TestClient(create_app(project_root, workspace))
    project_id = client.get("/projects").json()[0]["id"]
    destination = tmp_path / "user-projects"

    updated = client.patch(
        f"/projects/{project_id}",
        json={"name": "Renamed", "parent_path": str(destination)},
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"
    moved_root = Path(updated.json()["root_path"])
    assert moved_root.is_dir()
    assert not project_root.exists()

    deleted = client.delete(f"/projects/{project_id}")

    assert deleted.status_code == 200
    assert not moved_root.exists()


def test_analysis_profiles_api_lists_calibration_presets(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    create_project("Profiles", project_root)
    client = TestClient(create_app(project_root))

    response = client.get("/analysis/profiles")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "cinematic_traveling_v1" in names
    assert "recall_high_v1" in names
    gimbal = next(item for item in response.json() if item["name"] == "cinematic_gimbal_v1")
    assert gimbal["capture_type"] == "gimbal"
    assert sum(gimbal["parameters"][key] for key in (
        "weight_sharpness",
        "weight_exposure",
        "weight_direction",
        "weight_tracking",
        "weight_stability",
    )) == 1.0


def test_calibration_api_loads_and_saves_annotations(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project = create_project("Calibration", project_root)
    windows_path = project_root / "analysis" / "run_windows.json"
    windows_path.parent.mkdir()
    windows_path.write_text(
        json.dumps([{"start_seconds": 0.0, "end_seconds": 3.0, "sharpness_norm": 0.8}]),
        encoding="utf-8",
    )
    with get_session(project_root) as session:
        run = AnalysisRun(
            project_id=project.id,
            clip_id="clip-1",
            profile_name="cinematic_drone_v1",
            config_json="{}",
            config_hash="hash",
            analyzer_version="test",
            status=AnalysisRunStatus.COMPLETED,
            windows_path=str(windows_path),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

    client = TestClient(create_app(project_root))
    assert client.get(f"/analysis/runs/{run_id}/windows").json()[0]["end_seconds"] == 3.0
    saved = client.put(
        f"/evaluation/annotations/{run_id}",
        json={
            "intent_profile": "cinematic",
            "intervals": [
                {"start_seconds": 0, "end_seconds": 3, "label": "usable"}
            ],
        },
    )
    assert saved.status_code == 200
    annotations = client.get(f"/evaluation/annotations/{run_id}").json()
    assert annotations["intervals"][0]["label"] == "usable"


def test_analysis_run_metrics_previews_threshold_against_annotations(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project = create_project("Metrics", project_root)
    windows_path = project_root / "analysis" / "run_windows.json"
    windows_path.parent.mkdir()
    windows_path.write_text(
        json.dumps(
            [
                {
                    "start_seconds": 0.0,
                    "end_seconds": 3.0,
                    "sharpness_norm": 0.9,
                    "exposure_norm": 0.9,
                    "direction_coherence": 0.9,
                    "tracking_confidence": 0.9,
                    "stability_norm": 0.9,
                    "jerk_norm": 0.0,
                    "hard_turn_ratio": 0.0,
                    "hard_brake_ratio": 0.0,
                }
            ]
        ),
        encoding="utf-8",
    )
    with get_session(project_root) as session:
        run = AnalysisRun(
            project_id=project.id,
            clip_id="clip-1",
            profile_name="cinematic_drone_v1",
            config_json="{}",
            config_hash="hash",
            analyzer_version="test",
            status=AnalysisRunStatus.COMPLETED,
            windows_path=str(windows_path),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

    client = TestClient(create_app(project_root))
    client.put(
        f"/evaluation/annotations/{run_id}",
        json={"intent_profile": "cinematic", "intervals": [
            {"start_seconds": 0, "end_seconds": 3, "label": "usable"}
        ]},
    )

    lenient = client.get(f"/analysis/runs/{run_id}/metrics", params={"enter_threshold": 0.5})
    strict = client.get(f"/analysis/runs/{run_id}/metrics", params={"enter_threshold": 0.99})

    assert lenient.status_code == 200
    assert lenient.json()["current"]["recall"] == 1.0
    assert strict.json()["current"]["recall"] == 0.0


def test_analysis_windows_resolves_artifact_after_project_move(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project = create_project("Moved project", project_root)
    windows_path = project_root / "analysis" / "moved_windows.json"
    windows_path.parent.mkdir()
    windows_path.write_text(
        json.dumps([{"start_seconds": 2.0, "end_seconds": 5.0}]),
        encoding="utf-8",
    )
    with get_session(project_root) as session:
        run = AnalysisRun(
            project_id=project.id,
            clip_id="clip-1",
            profile_name="cinematic_drone_v1",
            config_json="{}",
            config_hash="hash",
            analyzer_version="test",
            status=AnalysisRunStatus.COMPLETED,
            windows_path=str(tmp_path / "old-location" / windows_path.name),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.id

    client = TestClient(create_app(project_root))
    response = client.get(f"/analysis/runs/{run_id}/windows")

    assert response.status_code == 200
    assert response.json()[0]["start_seconds"] == 2.0


def test_analyze_clip_rejects_unknown_profile_override(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    create_project("Overrides", project_root)
    from editoragent.services import media_service

    media_service.add_media_root(project_root, source_folder, confirm_read_only=True)
    (source_folder / "clip.mp4").write_bytes(b"fake")
    client = TestClient(create_app(project_root))
    clip_id = media_service.inspect_clip(project_root, source_folder / "clip.mp4").clip.id

    response = client.post(
        f"/clips/{clip_id}/analyze", json={"profile_name": "does_not_exist"}
    )

    assert response.status_code == 422


def test_human_labels_are_persisted_separately_from_editorial_segments(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    create_project("Labels", project_root)
    client = TestClient(create_app(project_root))

    created = client.put(
        "/labels",
        json={
            "clip_id": "clip-1",
            "start_seconds": 1.0,
            "end_seconds": 5.0,
            "utility_label": "usable",
            "capture_type": "gimbal",
            "motion_intent": "traveling",
            "shot_type": "traveling",
            "motion_quality": "smooth",
            "technical_issues": ["exposure"],
        },
    )

    assert created.status_code == 200
    assert created.json()["capture_type"] == "gimbal"
    assert created.json()["technical_issues"] == ["exposure"]
    label_id = created.json()["id"]
    listed = client.get("/labels?clip_id=clip-1")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == label_id
    assert listed.json()[0]["shot_type"] == "traveling"

    session = client.post("/labeling/sessions")
    assert session.status_code == 200
    assert session.json()["clips_total"] == 0


def test_manual_segment_can_be_created_for_valid_clip_without_analysis(
    tmp_path: Path, monkeypatch, load_ffprobe_fixture
) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    create_project("Manual", project_root)
    from editoragent.services import media_service

    media_service.add_media_root(project_root, source_folder, confirm_read_only=True)
    video = source_folder / "clip.mp4"
    video.write_bytes(b"fake")
    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("avata2_valid.json"),
    )
    clip = media_service.inspect_clip(project_root, video).clip

    response = TestClient(create_app(project_root)).post(
        "/segments/manual",
        json={"clip_id": clip.id, "start_seconds": 2.0, "end_seconds": 6.0},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "manual"
    assert response.json()["analysis_run_id"]


def test_manual_segments_cannot_overlap(tmp_path: Path, monkeypatch, load_ffprobe_fixture) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    create_project("Overlap", project_root)
    from editoragent.services import media_service

    media_service.add_media_root(project_root, source_folder, confirm_read_only=True)
    video = source_folder / "clip.mp4"
    video.write_bytes(b"fake")
    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("avata2_valid.json"),
    )
    clip = media_service.inspect_clip(project_root, video).clip
    client = TestClient(create_app(project_root))
    first = client.post(
        "/segments/manual",
        json={"clip_id": clip.id, "start_seconds": 2.0, "end_seconds": 6.0},
    )
    second = client.post(
        "/segments/manual",
        json={"clip_id": clip.id, "start_seconds": 5.0, "end_seconds": 8.0},
    )

    assert first.status_code == 200
    assert second.status_code == 422


def test_approving_segment_ignores_overlap_with_preexisting_sibling(tmp_path: Path) -> None:
    """Approve/reject must not fail even if legacy overlapping segments exist."""
    project_root = tmp_path / "project"
    project = create_project("Legacy overlap", project_root)
    with get_session(project_root) as session:
        first = Segment(
            project_id=project.id,
            clip_id="clip-1",
            analysis_run_id="run-1",
            start_seconds=2.0,
            end_seconds=8.0,
            technical_score=0.7,
        )
        second = Segment(
            project_id=project.id,
            clip_id="clip-1",
            analysis_run_id="run-2",
            start_seconds=5.0,
            end_seconds=10.0,
            technical_score=0.6,
        )
        session.add(first)
        session.add(second)
        session.commit()
        session.refresh(first)
        segment_id = first.id

    client = TestClient(create_app(project_root))
    response = client.patch(f"/segments/{segment_id}", json={"status": "approved"})

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_analysis_job_cancel_stops_active_clip(monkeypatch, tmp_path: Path) -> None:
    manager = AnalysisJobManager(tmp_path)

    def wait_for_cancel(*_args, cancel_event, **_kwargs):
        cancel_event.wait(timeout=1)
        raise analysis_service.AnalysisCancelledError("cancelled")

    monkeypatch.setattr(analysis_service, "analyze_clip", wait_for_cancel)
    monkeypatch.setattr(manager, "_relative_path", lambda _root, _clip_id: "clip.mp4")
    job = manager.start(tmp_path, ["clip-1"])
    manager.cancel(job.id)
    import time

    deadline = time.monotonic() + 1
    while job.status not in {"cancelled", "completed", "failed"} and time.monotonic() < deadline:
        time.sleep(0.01)

    assert job.status == "cancelled"
