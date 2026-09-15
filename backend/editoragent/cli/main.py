"""EditorAgent CLI: project and single-clip media commands.

Fase 1 / slice 1 only. No folder batch scan, no proxies, no analysis yet.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from editoragent.analyzers.frame_sampler import VideoOpenError
from editoragent.api.server import run_server
from editoragent.infrastructure.ffprobe import FfprobeNotFoundError
from editoragent.services import (
    analysis_service,
    evaluation_service,
    export_service,
    media_service,
    project_service,
)

app = typer.Typer(help="EditorAgent — análisis local de metraje de dron.")
project_app = typer.Typer(help="Gestión de proyectos EditorAgent.")
media_app = typer.Typer(help="Ingestión e inspección de clips.")
analyze_app = typer.Typer(help="Análisis técnico de clips (nitidez, exposición, ...).")
export_app = typer.Typer(help="Exportación de candidatos para NLE.")
api_app = typer.Typer(help="API local para la interfaz de revisión.")
evaluation_app = typer.Typer(help="Evaluación reproducible con anotaciones humanas.")
app.add_typer(project_app, name="project")
app.add_typer(media_app, name="media")
app.add_typer(analyze_app, name="analyze")
app.add_typer(export_app, name="export")
app.add_typer(api_app, name="api")
app.add_typer(evaluation_app, name="evaluation")


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Nombre visible del proyecto."),
    root: Path = typer.Option(..., "--root", help="Carpeta de artefactos del proyecto."),
) -> None:
    """Crea un proyecto nuevo (no toca ninguna carpeta de medios)."""
    try:
        project = project_service.create_project(name, root)
    except project_service.ProjectAlreadyExistsError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Proyecto creado: {project.id} en {project.root_path}", fg=typer.colors.GREEN)


@media_app.command("add-root")
def media_add_root(
    project_root: Path = typer.Argument(..., help="Carpeta del proyecto."),
    source_folder: Path = typer.Argument(..., help="Carpeta fuente de medios (sólo lectura)."),
    confirm_read_only: bool = typer.Option(
        False,
        "--confirm-read-only",
        help="Confirma explícitamente que la carpeta se analiza sin modificarla.",
    ),
    display_name: str | None = typer.Option(None, "--display-name"),
) -> None:
    """Registra una carpeta fuente de medios en modo sólo lectura."""
    try:
        media_root = media_service.add_media_root(
            project_root,
            source_folder,
            confirm_read_only=confirm_read_only,
            display_name=display_name,
        )
    except (ValueError, media_service.MediaRootAlreadyExistsError, LookupError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(
        f"MediaRoot registrada: {media_root.id} -> {media_root.path}", fg=typer.colors.GREEN
    )


@media_app.command("inspect")
def media_inspect(
    project_root: Path = typer.Argument(..., help="Carpeta del proyecto."),
    video_file: Path = typer.Argument(..., help="Ruta a un único clip de vídeo."),
) -> None:
    """Analiza metadatos de UN clip con ffprobe y persiste el resultado."""
    try:
        result = media_service.inspect_clip(project_root, video_file)
    except (
        FileNotFoundError,
        LookupError,
        media_service.NoMatchingMediaRootError,
        FfprobeNotFoundError,
    ) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    clip = result.clip
    color = {
        "valid": typer.colors.GREEN,
        "unsupported": typer.colors.YELLOW,
        "error": typer.colors.RED,
    }[clip.ingest_status.value]
    typer.secho(
        f"[{clip.ingest_status.value}] {clip.relative_path} "
        f"(codec={clip.codec}, {clip.width}x{clip.height}, "
        f"{clip.duration_seconds}s)",
        fg=color,
    )
    if clip.error_message:
        typer.secho(f"  motivo: {clip.error_message}", fg=color)
    typer.echo(f"Diagnóstico: {result.diagnostics_path}")


@analyze_app.command("clip")
def analyze_clip_cmd(
    project_root: Path = typer.Argument(..., help="Carpeta del proyecto."),
    relative_path: str = typer.Argument(
        ..., help="Ruta relativa del clip dentro de su MediaRoot (la misma que 'media inspect')."
    ),
    sample_fps: float = typer.Option(
        analysis_service.DEFAULT_SAMPLE_FPS, "--sample-fps", help="FPS de muestreo."
    ),
    window_seconds: float = typer.Option(
        analysis_service.DEFAULT_WINDOW_SECONDS, "--window-seconds"
    ),
    profile: str = typer.Option(analysis_service.DEFAULT_PROFILE, "--profile"),
    minimum_duration: float = typer.Option(4.0, "--minimum-duration"),
    enter_threshold: float = typer.Option(0.72, "--enter-threshold"),
    exit_threshold: float = typer.Option(0.62, "--exit-threshold"),
) -> None:
    """Analiza nitidez y exposición por ventanas para UN clip ya inspeccionado.

    No calcula movimiento/estabilidad todavía (slice siguiente) ni un score
    compuesto final: sólo dos de las cinco señales de docs/ANALYSIS_SPEC.md.
    """
    config = analysis_service.AnalysisConfig.from_profile(
        profile,
        sample_fps=sample_fps,
        window_seconds=window_seconds,
        minimum_duration_seconds=minimum_duration,
        enter_threshold=enter_threshold,
        exit_threshold=exit_threshold,
    )
    try:
        summary = analysis_service.analyze_clip(project_root, relative_path, config)
    except (
        analysis_service.ClipNotFoundError,
        analysis_service.ClipNotIngestedError,
        LookupError,
        VideoOpenError,
    ) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"Análisis completado: {summary.frames_processed} frames, "
        f"{len(summary.windows)} ventanas, {summary.elapsed_seconds:.1f}s de proceso.",
        fg=typer.colors.GREEN,
    )
    for window in summary.windows:
        typer.echo(
            f"  [{window.start_seconds:6.1f}-{window.end_seconds:6.1f}s] "
            f"nitidez={window.sharpness_norm:.2f} exposición={window.exposure_norm:.2f} "
            f"movimiento={window.motion_norm:.2f} "
            f"coherencia={window.direction_coherence:.2f} jerk={window.jerk_norm:.2f} "
            f"confianza_tracking={window.tracking_confidence:.2f} "
            f"estabilidad={window.stability_norm:.2f}"
        )
        for reason in window.reasons:
            typer.secho(f"    + {reason}", fg=typer.colors.GREEN)
        for penalty in window.penalties:
            typer.secho(f"    - {penalty}", fg=typer.colors.YELLOW)
    typer.echo(f"Ventanas guardadas en: {summary.analysis_run.windows_path}")
    typer.echo(f"Segmentos candidatos: {len(summary.segments)}")
    for segment in summary.segments:
        typer.echo(
            f"  [{segment.start_seconds:.1f}-{segment.end_seconds:.1f}s] "
            f"duración={segment.duration_seconds:.1f}s "
            f"score_técnico={segment.technical_score:.2f}"
        )
    typer.echo(f"Segmentos guardados en: {summary.analysis_run.segments_path}")


@evaluation_app.command("template")
def evaluation_template(
    windows_json: Path = typer.Argument(..., help="JSON de ventanas generado por analyze clip."),
    destination: Path = typer.Argument(..., help="Ruta de la plantilla de anotación."),
    clip_id: str = typer.Option("", "--clip-id"),
    relative_path: str = typer.Option("", "--relative-path"),
) -> None:
    """Crea una plantilla JSON para etiquetar ventanas humanas."""
    try:
        output = evaluation_service.create_annotation_template(
            windows_json,
            destination,
            clip_id=clip_id,
            relative_path=relative_path,
        )
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Plantilla creada: {output}", fg=typer.colors.GREEN)


@evaluation_app.command("windows")
def evaluation_windows(
    windows_json: Path = typer.Argument(..., help="JSON de ventanas del análisis."),
    annotation_json: Path = typer.Argument(..., help="JSON anotado por una persona."),
    enter_threshold: float = typer.Option(0.72, "--enter-threshold"),
    top_k: int = typer.Option(5, "--top-k", min=1),
) -> None:
    """Compara el score actual con el baseline de nitidez y exposición."""
    try:
        result = evaluation_service.evaluate_windows(
            windows_json,
            annotation_json,
            enter_threshold=enter_threshold,
            top_k=top_k,
        )
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@export_app.command("fcpxml")
def export_fcpxml_cmd(
    project_root: Path = typer.Argument(..., help="Carpeta del proyecto."),
    relative_path: str = typer.Argument(..., help="Ruta relativa del clip inspeccionado."),
    segments_json: Path = typer.Argument(..., help="JSON de segmentos generado por analyze clip."),
    destination: Path = typer.Argument(..., help="Ruta del FCPXML de salida."),
) -> None:
    """Exporta candidatos a una secuencia FCPXML no destructiva."""
    try:
        output = export_service.export_segments_fcpxml(
            project_root, relative_path, segments_json, destination
        )
    except (FileNotFoundError, LookupError, export_service.ExportClipNotFoundError,
            export_service.ExportClipInvalidError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    typer.secho(f"FCPXML exportado: {output}", fg=typer.colors.GREEN)


@api_app.command("serve")
def api_serve(
    project_root: Path = typer.Argument(..., help="Carpeta del proyecto."),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
    workspace_root: Path | None = typer.Option(None, "--workspace-root"),
) -> None:
    """Inicia la API local para la interfaz de revisión."""
    run_server(project_root, host=host, port=port, workspace_root=workspace_root)


if __name__ == "__main__":
    app()
