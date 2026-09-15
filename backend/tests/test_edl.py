from __future__ import annotations

from pathlib import Path

from editoragent.analyzers.segments import SegmentCandidate
from editoragent.exporters.edl import export_edl_multi
from editoragent.exporters.fcpxml import FCPXMLSource


def test_export_edl_writes_cmx3600_events(tmp_path: Path) -> None:
    source = FCPXMLSource(
        name="DJI_0001.MP4",
        path=tmp_path / "DJI_0001.MP4",
        duration_seconds=20.0,
        fps_num=25,
        fps_den=1,
        width=1920,
        height=1080,
    )
    destination = tmp_path / "exports" / "selects.edl"

    output = export_edl_multi(
        [(source, [SegmentCandidate(2.0, 6.0, 0.8, [], [])])], destination
    )

    content = output.read_text(encoding="ascii")
    assert content.startswith("TITLE: EditorAgent selects")
    assert "001  DJI_0001 V     C" in content
    assert "00:00:02:00 00:00:06:00" in content
    assert "* FROM CLIP: DJI_0001.MP4" in content
