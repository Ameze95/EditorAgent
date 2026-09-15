"""Minimal FCPXML exporter for candidate segments.

The XML describes a Resolve-friendly selects timeline using the original
source as an asset and one asset-clip per candidate interval. It does not
re-encode or copy media; all source references remain non-destructive.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from editoragent.analyzers.segments import SegmentCandidate

FCPXML_VERSION = "1.10"


@dataclass(frozen=True)
class FCPXMLSource:
    name: str
    path: Path
    duration_seconds: float
    fps_num: int
    fps_den: int
    width: int
    height: int


def _time(seconds: float, fps_num: int, fps_den: int) -> str:
    """Encode seconds as a reduced rational string accepted by FCPXML."""
    frames = round(seconds * fps_num / fps_den)
    value = Fraction(frames * fps_den, fps_num)
    if value.denominator == 1:
        return f"{value.numerator}s"
    return f"{value.numerator}/{value.denominator}s"


def _uri(path: Path) -> str:
    return path.resolve().as_uri()


def export_fcpxml(
    source: FCPXMLSource,
    segments: list[SegmentCandidate],
    destination: Path,
    *,
    project_name: str = "EditorAgent selects",
) -> Path:
    """Write a FCPXML selects timeline for a single source and return its path."""
    return export_fcpxml_multi([(source, segments)], destination, project_name=project_name)


def export_fcpxml_multi(
    clip_segments: list[tuple[FCPXMLSource, list[SegmentCandidate]]],
    destination: Path,
    *,
    project_name: str = "EditorAgent selects",
) -> Path:
    """Write a FCPXML selects timeline spanning one or more source clips.

    Each source clip gets its own `asset` (and its own `format` unless an
    identical fps/resolution combination is already registered), so a single
    timeline can mix approved selects from different clips in one project.
    """
    if not clip_segments:
        raise ValueError("No hay clips con segmentos para exportar.")

    root = ET.Element("fcpxml", version=FCPXML_VERSION)
    resources = ET.SubElement(root, "resources")

    format_ids: dict[tuple[int, int, int, int], str] = {}
    assets: list[tuple[FCPXMLSource, str, str]] = []
    for index, (source, _segments) in enumerate(clip_segments, start=1):
        if source.duration_seconds <= 0:
            raise ValueError("La duración del clip debe ser mayor que cero.")
        if source.fps_num <= 0 or source.fps_den <= 0:
            raise ValueError("El FPS del clip debe ser un racional positivo.")
        format_key = (source.fps_num, source.fps_den, source.width, source.height)
        if format_key not in format_ids:
            format_id = f"format{len(format_ids) + 1}"
            format_ids[format_key] = format_id
            ET.SubElement(
                resources,
                "format",
                id=format_id,
                name=f"FFVideoFormat{source.fps_num}/{source.fps_den}",
                frameDuration=_time(
                    source.fps_den / source.fps_num, source.fps_num, source.fps_den
                ),
                width=str(source.width),
                height=str(source.height),
            )
        format_id = format_ids[format_key]
        asset_id = f"asset{index}"
        ET.SubElement(
            resources,
            "asset",
            id=asset_id,
            name=source.name,
            src=_uri(source.path),
            start="0s",
            duration=_time(source.duration_seconds, source.fps_num, source.fps_den),
            hasVideo="1",
            hasAudio="1",
            format=format_id,
        )
        assets.append((source, asset_id, format_id))

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", name="EditorAgent")
    project = ET.SubElement(event, "project", name=project_name)
    primary_source, _primary_asset_id, primary_format_id = assets[0]
    total_duration = sum(
        segment.duration_seconds for _source, segments in clip_segments for segment in segments
    )
    sequence = ET.SubElement(
        project,
        "sequence",
        format=primary_format_id,
        duration=_time(total_duration, primary_source.fps_num, primary_source.fps_den),
        tcStart="0s",
        tcFormat="NDF",
        audioLayout="stereo",
        audioRate="48k",
    )
    spine = ET.SubElement(sequence, "spine")
    offset_seconds = 0.0
    clip_counter = 0
    for (source, asset_id, format_id), (_source, segments) in zip(
        assets, clip_segments, strict=True
    ):
        for segment in segments:
            clip_counter += 1
            ET.SubElement(
                spine,
                "asset-clip",
                name=f"Select {clip_counter:03d}",
                ref=asset_id,
                offset=_time(offset_seconds, source.fps_num, source.fps_den),
                start=_time(segment.start_seconds, source.fps_num, source.fps_den),
                duration=_time(segment.duration_seconds, source.fps_num, source.fps_den),
                format=format_id,
            )
            offset_seconds += segment.duration_seconds

    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
    return destination
