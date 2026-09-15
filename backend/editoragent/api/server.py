"""Run the local review API for one project."""

from __future__ import annotations

from pathlib import Path

import uvicorn

from editoragent.api.app import create_app


def run_server(
    project_root: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    workspace_root: Path | None = None,
) -> None:
    uvicorn.run(create_app(project_root, workspace_root), host=host, port=port)
