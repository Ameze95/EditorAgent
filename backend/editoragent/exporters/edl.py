"""CMX3600 EDL exporter for non-destructive NLE exchange."""

from __future__ import annotations

from pathlib import Path

from editoragent.analyzers.segments import SegmentCandidate
from editoragent.exporters.fcpxml import FCPXMLSource


def _timecode(seconds: float, fps_num: int, fps_den: int) -> str:
    fps = max(1, round(fps_num / fps_den))
    total_frames = max(0, round(seconds * fps_num / fps_den))
    frames = total_frames % fps
    total_seconds = total_frames // fps
    second = total_seconds % 60
    total_minutes = total_seconds // 60
    minute = total_minutes % 60
    hour = total_minutes // 60
    return f"{hour:02d}:{minute:02d}:{second:02d}:{frames:02d}"


def _reel_name(source: FCPXMLSource) -> str:
    stem = Path(source.name).stem.upper()
    return stem[:8] or "SOURCE"


def export_edl_multi(
    clip_segments: list[tuple[FCPXMLSource, list[SegmentCandidate]]],
    destination: Path,
    *,
    title: str = "EditorAgent selects",
) -> Path:
    """Write a CMX3600 EDL with one event per selected segment."""
    if not clip_segments:
        raise ValueError("No hay clips con segmentos para exportar.")

    lines = [f"TITLE: {title}", "FCM: NON-DROP FRAME", ""]
    event_number = 1
    for source, segments in clip_segments:
        if source.duration_seconds <= 0 or source.fps_num <= 0 or source.fps_den <= 0:
            raise ValueError("La fuente tiene duración o FPS inválidos.")
        reel = _reel_name(source)
        for segment in segments:
            source_in = _timecode(segment.start_seconds, source.fps_num, source.fps_den)
            source_out = _timecode(segment.end_seconds, source.fps_num, source.fps_den)
            record_in = _timecode(0.0, source.fps_num, source.fps_den)
            record_out = _timecode(
                segment.duration_seconds, source.fps_num, source.fps_den
            )
            lines.append(
                f"{event_number:03d}  {reel:<8} V     C        "
                f"{source_in} {source_out} {record_in} {record_out}"
            )
            lines.append(f"* FROM CLIP: {source.name}")
            lines.append("")
            event_number += 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="ascii")
    return destination
