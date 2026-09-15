from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from editoragent.analyzers.segments import SegmentCandidate
from editoragent.exporters.fcpxml import FCPXMLSource, export_fcpxml


def test_export_fcpxml_writes_selects_timeline(tmp_path: Path) -> None:
    source = FCPXMLSource(
        name="DJI_0001.MP4",
        path=tmp_path / "DJI_0001.MP4",
        duration_seconds=20.0,
        fps_num=100,
        fps_den=1,
        width=3840,
        height=2160,
    )
    segments = [
        SegmentCandidate(1.25, 5.75, 0.84),
        SegmentCandidate(10.0, 13.5, 0.79),
    ]
    destination = tmp_path / "exports" / "selects.fcpxml"

    export_fcpxml(source, segments, destination)

    root = ET.parse(destination).getroot()
    assert root.tag == "fcpxml"
    assert root.attrib["version"] == "1.10"
    format_element = root.find("./resources/format")
    assert format_element is not None
    assert format_element.attrib["frameDuration"] == "1/100s"
    assert root.find("./resources/asset") is not None
    clips = root.findall("./library/event/project/sequence/spine/asset-clip")
    assert len(clips) == 2
    assert clips[0].attrib["start"] == "5/4s"
    assert clips[0].attrib["duration"] == "9/2s"
    assert clips[1].attrib["offset"] == "9/2s"
    assert clips[1].attrib["start"] == "10s"


def test_export_fcpxml_uses_file_uri_and_does_not_write_source(tmp_path: Path) -> None:
    source_path = tmp_path / "media" / "clip with spaces.MP4"
    source_path.parent.mkdir()
    source_path.write_bytes(b"source marker")
    destination = tmp_path / "selects.fcpxml"
    source = FCPXMLSource("clip with spaces.MP4", source_path, 8.0, 25, 1, 1920, 1080)

    export_fcpxml(source, [SegmentCandidate(0.0, 4.0, 0.8)], destination)

    asset = ET.parse(destination).find("./resources/asset")
    assert asset is not None
    assert asset.attrib["src"].startswith("file:///")
    assert source_path.read_bytes() == b"source marker"
