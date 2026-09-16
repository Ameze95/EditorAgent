"""SQLite engine/session helpers.

One SQLite file lives inside each project's artifact folder
(<project_root>/editoragent.db), never inside a media source folder.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, inspect, text
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

DB_FILENAME = "editoragent.db"


def project_db_path(project_root: Path) -> Path:
    return project_root / DB_FILENAME


def get_engine(project_root: Path) -> Engine:
    db_path = project_db_path(project_root)
    engine = create_engine(f"sqlite:///{db_path}", poolclass=NullPool)
    SQLModel.metadata.create_all(engine)
    _migrate_human_labels(engine)
    return engine


def _migrate_human_labels(engine: Engine) -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("humanlabel")}
    additions = {
        "capture_type": "VARCHAR",
        "motion_intent": "VARCHAR",
        "technical_issues_json": "VARCHAR NOT NULL DEFAULT '[]'",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(
                    text(f"ALTER TABLE humanlabel ADD COLUMN {name} {definition}")
                )


def get_session(project_root: Path) -> Session:
    return Session(get_engine(project_root))
