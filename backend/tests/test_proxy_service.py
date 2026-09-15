from __future__ import annotations

from pathlib import Path

from editoragent.domain.models import Clip
from editoragent.services.proxy_service import ensure_analysis_proxy


def test_proxy_is_created_and_cached(tmp_path: Path, make_synthetic_video) -> None:
    source = make_synthetic_video(name="source.mp4", fps=10, seconds=2.0)
    clip = Clip(
        project_id="project",
        media_root_id="root",
        relative_path="source.mp4",
        source_fingerprint="fingerprint-1",
    )

    first = ensure_analysis_proxy(tmp_path, clip, source)
    second = ensure_analysis_proxy(tmp_path, clip, source)

    assert first == second
    assert first.exists()
    assert first.stat().st_size > 0
    assert first.with_suffix(".json").exists()


def test_proxy_regenerates_when_source_fingerprint_changes(
    tmp_path: Path, make_synthetic_video
) -> None:
    source = make_synthetic_video(name="source.mp4", fps=10, seconds=2.0)
    clip = Clip(
        project_id="project",
        media_root_id="root",
        relative_path="source.mp4",
        source_fingerprint="fingerprint-1",
    )

    first = ensure_analysis_proxy(tmp_path, clip, source)
    first_mtime = first.stat().st_mtime_ns

    clip.source_fingerprint = "fingerprint-2"
    second = ensure_analysis_proxy(tmp_path, clip, source)

    assert second == first
    assert second.stat().st_mtime_ns >= first_mtime
