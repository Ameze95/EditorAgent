from __future__ import annotations

from pathlib import Path

import pytest

from editoragent.services import project_service


def test_create_project_creates_root_and_row(tmp_path: Path) -> None:
    root = tmp_path / "my_project"

    project = project_service.create_project("Sesión playa", root)

    assert root.exists()
    assert (root / "editoragent.db").exists()
    assert project.name == "Sesión playa"


def test_create_project_twice_fails(tmp_path: Path) -> None:
    root = tmp_path / "my_project"
    project_service.create_project("Sesión playa", root)

    with pytest.raises(project_service.ProjectAlreadyExistsError):
        project_service.create_project("Otro nombre", root)


def test_get_project_without_creation_fails(tmp_path: Path) -> None:
    with pytest.raises(LookupError):
        project_service.get_project(tmp_path / "does_not_exist")
