from __future__ import annotations

from pathlib import Path

import pytest

from editoragent.domain.models import IngestStatus
from editoragent.services import media_service, project_service


@pytest.fixture
def project_and_root(tmp_path: Path):
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    project_service.create_project("Sesión playa", project_root)
    media_service.add_media_root(project_root, source_folder, confirm_read_only=True)
    return project_root, source_folder


def test_add_media_root_requires_explicit_confirmation(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "source"
    source_folder.mkdir()
    project_service.create_project("Sesión playa", project_root)

    with pytest.raises(ValueError):
        media_service.add_media_root(project_root, source_folder, confirm_read_only=False)


def test_inspect_clip_valid(project_and_root, monkeypatch, load_ffprobe_fixture) -> None:
    project_root, source_folder = project_and_root
    video = source_folder / "DJI_0001.MP4"
    video.write_bytes(b"fake video bytes")

    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("avata2_valid.json"),
    )

    result = media_service.inspect_clip(project_root, video)

    assert result.clip.ingest_status == IngestStatus.VALID
    assert result.clip.codec == "hevc"
    assert result.clip.relative_path == "DJI_0001.MP4"
    assert result.diagnostics_path.exists()


def test_inspect_clip_unsupported_extension(project_and_root) -> None:
    project_root, source_folder = project_and_root
    video = source_folder / "clip.mov"
    video.write_bytes(b"fake")

    result = media_service.inspect_clip(project_root, video)

    assert result.clip.ingest_status == IngestStatus.UNSUPPORTED
    assert "Extensión" in result.clip.error_message


def test_inspect_clip_unsupported_codec(
    project_and_root, monkeypatch, load_ffprobe_fixture
) -> None:
    project_root, source_folder = project_and_root
    video = source_folder / "clip2.mp4"
    video.write_bytes(b"fake")

    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("unsupported_codec.json"),
    )

    result = media_service.inspect_clip(project_root, video)

    assert result.clip.ingest_status == IngestStatus.UNSUPPORTED
    assert "vp9" in result.clip.error_message


def test_inspect_clip_no_video_stream(project_and_root, monkeypatch, load_ffprobe_fixture) -> None:
    project_root, source_folder = project_and_root
    video = source_folder / "corrupt.mp4"
    video.write_bytes(b"fake")

    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("no_video_stream.json"),
    )

    result = media_service.inspect_clip(project_root, video)

    assert result.clip.ingest_status == IngestStatus.ERROR


def test_inspect_clip_without_media_root_fails(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_service.create_project("Sesión playa", project_root)
    orphan_video = tmp_path / "orphan.mp4"
    orphan_video.write_bytes(b"fake")

    with pytest.raises(media_service.NoMatchingMediaRootError):
        media_service.inspect_clip(project_root, orphan_video)


def test_scan_media_root_registers_root_and_inspects_all_clips(
    tmp_path: Path, monkeypatch, load_ffprobe_fixture
) -> None:
    project_root = tmp_path / "project"
    source_folder = tmp_path / "batch_source"
    source_folder.mkdir()
    project_service.create_project("Sesión lote", project_root)
    (source_folder / "clip_a.mp4").write_bytes(b"fake")
    (source_folder / "clip_b.mp4").write_bytes(b"fake")
    (source_folder / "notes.txt").write_text("not a video")

    monkeypatch.setattr(
        media_service.ffprobe,
        "run_ffprobe",
        lambda _path: load_ffprobe_fixture("avata2_valid.json"),
    )

    result = media_service.scan_media_root(project_root, source_folder)

    assert result.inspected == 2
    assert result.valid == 2
    assert result.skipped_existing_root is False

    result_again = media_service.scan_media_root(project_root, source_folder)
    assert result_again.skipped_existing_root is True
    assert result_again.inspected == 2
