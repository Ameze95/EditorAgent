from __future__ import annotations

import json
from pathlib import Path

from editoragent.domain.models import AnalysisRunStatus
from editoragent.services import analysis_service, media_service, project_service


def test_analysis_profiles_have_distinct_calibration_defaults() -> None:
    assert "cinematic_traveling_v1" in analysis_service.available_profiles()
    traveling = analysis_service.AnalysisConfig.from_profile("cinematic_traveling_v1")
    static = analysis_service.AnalysisConfig.from_profile("static_aerial_v1")

    assert traveling.profile_name == "cinematic_traveling_v1"
    assert traveling.enter_threshold < static.enter_threshold
    assert traveling.critical_jerk_threshold > static.critical_jerk_threshold


def test_unknown_analysis_profile_fails_with_available_names() -> None:
    try:
        analysis_service.AnalysisConfig.from_profile("unknown")
    except ValueError as exc:
        assert "cinematic_traveling_v1" in str(exc)
    else:
        raise AssertionError("Expected unknown profile to fail")


def test_analyze_clip_end_to_end(
    tmp_path: Path, make_synthetic_video, monkeypatch, load_ffprobe_fixture
) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    project_service.create_project("Sesión playa", project_root)
    media_service.add_media_root(project_root, source_folder, confirm_read_only=True)

    video_path = make_synthetic_video(name="clip.mp4", fps=10, seconds=2.0)
    real_video = source_folder / "clip.mp4"
    real_video.write_bytes(video_path.read_bytes())

    fixture = load_ffprobe_fixture("avata2_valid.json")
    fixture["format"]["duration"] = "2.0"
    fixture["streams"][0]["duration"] = "2.0"
    monkeypatch.setattr(media_service.ffprobe, "run_ffprobe", lambda _path: fixture)
    media_service.inspect_clip(project_root, real_video)

    config = analysis_service.AnalysisConfig(sample_fps=4.0, window_seconds=1.0, overlap_ratio=0.5)
    summary = analysis_service.analyze_clip(project_root, "clip.mp4", config)

    assert summary.analysis_run.status == AnalysisRunStatus.COMPLETED
    assert summary.frames_processed > 0
    assert summary.windows
    assert summary.segments == []
    windows_path = Path(summary.analysis_run.windows_path)
    assert windows_path.exists()
    stored = json.loads(windows_path.read_text(encoding="utf-8"))
    assert len(stored) == len(summary.windows)
    assert Path(summary.analysis_run.segments_path).exists()


def test_analyze_clip_rejects_unanalyzed_clip(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_service.create_project("Sesión playa", project_root)

    try:
        analysis_service.analyze_clip(project_root, "nope.mp4")
    except analysis_service.ClipNotFoundError:
        pass
    else:
        raise AssertionError("Expected ClipNotFoundError")
