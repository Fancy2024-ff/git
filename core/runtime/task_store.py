"""任务持久化：把 Task 落到 data/temp/tasks/，供轮询/清理。

文件存储（MVP 级），与 persistence 层方向一致；后续可换 repository。
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.task_model import Task

# core/runtime/task_store.py → core/runtime → core → repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TASK_DIR = _REPO_ROOT / "data" / "temp" / "tasks"


def _task_path(task_id: str) -> Path:
    return _TASK_DIR / f"{task_id}.json"


def save(task: Task) -> None:
    _TASK_DIR.mkdir(parents=True, exist_ok=True)
    _task_path(task.task_id).write_text(
        json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load(task_id: str) -> Task | None:
    p = _task_path(task_id)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return Task(**data)


def delete(task_id: str) -> bool:
    p = _task_path(task_id)
    if p.exists():
        p.unlink()
        return True
    return False


def cleanup_all() -> int:
    """清理全部任务文件，返回清理数量。"""
    if not _TASK_DIR.exists():
        return 0
    n = 0
    for f in _TASK_DIR.glob("*.json"):
        try:
            f.unlink()
            n += 1
        except OSError:
            pass
    return n
