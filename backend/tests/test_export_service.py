from __future__ import annotations

from pathlib import Path

from editoragent.domain.models import Segment, SegmentStatus
from editoragent.infrastructure.db import get_session
from editoragent.services import export_service, media_service, project_service


def test_export_approved_fcpxml_spans_multiple_clips(
    tmp_path: Path, monkeypatch, load_ffprobe_fixture
) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    project_service.create_project("Multi clip", project_root)
    media_service.add_media_root(project_root, source_folder, confirm_read_only=True)

    (source_folder / "clip_a.mp4").write_bytes(b"fake-a")
    (source_folder / "clip_b.mp4").write_bytes(b"fake-b")
    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("avata2_valid.json"),
    )
    clip_a = media_service.inspect_clip(project_root, source_folder / "clip_a.mp4").clip
    clip_b = media_service.inspect_clip(project_root, source_folder / "clip_b.mp4").clip

    with get_session(project_root) as session:
        session.add(
            Segment(
                project_id=clip_a.project_id,
                clip_id=clip_a.id,
                analysis_run_id="run-a",
                start_seconds=1.0,
                end_seconds=4.0,
                technical_score=0.8,
                status=SegmentStatus.APPROVED,
            )
        )
        session.add(
            Segment(
                project_id=clip_b.project_id,
                clip_id=clip_b.id,
                analysis_run_id="run-b",
                start_seconds=2.0,
                end_seconds=6.0,
                technical_score=0.75,
                status=SegmentStatus.APPROVED,
            )
        )
        session.commit()

    destination, count = export_service.export_approved_fcpxml(project_root)

    assert count == 2
    import xml.etree.ElementTree as ET

    root = ET.parse(destination).getroot()
    assets = root.findall("./resources/asset")
    clips = root.findall("./library/event/project/sequence/spine/asset-clip")
    assert len(assets) == 2
    assert len(clips) == 2


def test_export_approved_fcpxml_requires_at_least_one_approved(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_service.create_project("Empty", project_root)

    try:
        export_service.export_approved_fcpxml(project_root)
    except export_service.ExportClipInvalidError:
        pass
    else:
        raise AssertionError("Expected ExportClipInvalidError")
