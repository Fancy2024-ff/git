"""core.runtime.database — 流水线状态持久化（JSON + 文件锁）。

属于运行时基础设施。
"""

import json
from datetime import datetime

from filelock import FileLock

from core.runtime.config import DATA_DIR
from core.shared.models import MiniAppProject, ProjectStatus


DB_FILE = DATA_DIR / "pipeline_state.json"
DB_LOCK = FileLock(str(DB_FILE) + ".lock", timeout=10)


def _load_db() -> dict:
    """Load the JSON database."""
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    return {"projects": {}}


def _save_db(db: dict) -> None:
    """Save the JSON database."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


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
