"""Database layer for pipeline state persistence."""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from filelock import FileLock

from config.settings import DATA_DIR
from shared.models import MiniAppProject, ProjectStatus


DB_FILE = DATA_DIR / "pipeline_state.json"
DB_LOCK = FileLock(str(DB_FILE) + ".lock", timeout=10)


def _load_db() -> dict:
    """Load the JSON database. Tolerates a corrupt/partial file by resetting."""
    if DB_FILE.exists():
        try:
            return json.loads(DB_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            # File was left truncated by a crash mid-write — start fresh rather
            # than propagating a parse error to every caller.
            return {"projects": {}}
    return {"projects": {}}


def _save_db(db: dict) -> None:
    """Save the JSON database atomically (write temp + os.replace).

    A crash mid-write leaves the original file intact instead of a truncated,
    unparseable file.
    """
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(db, ensure_ascii=False, indent=2, default=str)
    fd, tmp_path = tempfile.mkstemp(dir=str(DB_FILE.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, DB_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def save_project(project: MiniAppProject) -> None:
    """Save or update a project in the database (file-locked)."""
    with DB_LOCK:
        db = _load_db()
        project.updated_at = datetime.now()
        db["projects"][project.id] = json.loads(project.model_dump_json())
        _save_db(db)


def get_project(project_id: str) -> MiniAppProject | None:
    """Get a project by ID (file-locked to avoid reading partial writes)."""
    with DB_LOCK:
        db = _load_db()
        data = db["projects"].get(project_id)
        if data:
            return MiniAppProject(**data)
        return None


def list_projects(status: ProjectStatus | None = None) -> list[MiniAppProject]:
    """List projects, optionally filtered by status (file-locked)."""
    with DB_LOCK:
        db = _load_db()
        projects = [MiniAppProject(**data) for data in db["projects"].values()]
        if status:
            projects = [p for p in projects if p.status == status]
        return projects
