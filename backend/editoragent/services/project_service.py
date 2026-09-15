"""Project lifecycle: create a project workspace, separate from media sources."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sqlmodel import select

from editoragent import __version__
from editoragent.domain.models import Project
from editoragent.infrastructure.db import get_session, project_db_path


class ProjectAlreadyExistsError(RuntimeError):
    pass


class ProjectOperationError(RuntimeError):
    pass


def _registry_path(workspace: Path) -> Path:
    return workspace / ".editoragent-projects.json"


def registered_project_roots(workspace: Path) -> list[Path]:
    path = _registry_path(workspace)
    roots: set[Path] = set()
    if path.is_file():
        try:
            roots.update(
                Path(item).resolve()
                for item in json.loads(path.read_text(encoding="utf-8"))
            )
        except (json.JSONDecodeError, TypeError):
            pass
    roots.update(database.parent.resolve() for database in workspace.rglob("editoragent.db"))
    return sorted(roots)


def _register_root(workspace: Path, root: Path) -> None:
    roots = {item.resolve() for item in registered_project_roots(workspace)}
    roots.add(root.resolve())
    registry = _registry_path(workspace)
    registry.write_text(
        json.dumps([str(item) for item in sorted(roots)], indent=2), encoding="utf-8"
    )


def create_project(name: str, root: Path, workspace: Path | None = None) -> Project:
    if project_db_path(root).exists():
        raise ProjectAlreadyExistsError(f"Ya existe un proyecto en {root}.")
    if root.exists() and any(root.iterdir()):
        raise ProjectOperationError(f"La carpeta de proyecto no está vacía: {root}")
    root.mkdir(parents=True, exist_ok=True)
    with get_session(root) as session:
        existing = session.exec(select(Project)).first()
        if existing is not None:
            raise ProjectAlreadyExistsError(
                f"Ya existe un proyecto en {root} (id={existing.id})."
            )
        project = Project(name=name, root_path=str(root), app_version=__version__)
        session.add(project)
        session.commit()
        session.refresh(project)
        if workspace is not None:
            _register_root(workspace, root)
        return project


def update_project(
    workspace: Path,
    root: Path,
    *,
    name: str | None = None,
    target_root: Path | None = None,
) -> Project:
    project = get_project(root)
    destination = target_root.resolve() if target_root is not None else root.resolve()
    if destination != root.resolve():
        if destination.exists():
            raise ProjectOperationError(f"Ya existe una carpeta en el destino: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root), str(destination))
    with get_session(destination) as session:
        stored = session.exec(select(Project).where(Project.id == project.id)).first()
        if stored is None:
            raise LookupError("No se encuentra el proyecto movido.")
        if name is not None:
            stored.name = name.strip()
        stored.root_path = str(destination)
        session.add(stored)
        session.commit()
        session.refresh(stored)
    _register_root(workspace, destination)
    return stored


def delete_project(workspace: Path, root: Path) -> None:
    get_project(root)
    if not root.exists():
        raise ProjectOperationError("La carpeta del proyecto no existe.")
    shutil.rmtree(root)
    registry = _registry_path(workspace)
    roots = [item for item in registered_project_roots(workspace) if item != root.resolve()]
    registry.write_text(json.dumps([str(item) for item in roots], indent=2), encoding="utf-8")


def get_project(root: Path) -> Project:
    if not project_db_path(root).exists():
        raise LookupError(
            f"No hay ningún proyecto en {root}. Ejecuta 'project create' primero."
        )
    with get_session(root) as session:
        project = session.exec(select(Project)).first()
        if project is None:
            raise LookupError(
                f"No hay ningún proyecto en {root}. Ejecuta 'project create' primero."
            )
        return project
