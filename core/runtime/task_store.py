"""任务持久化：把 Task 落到 data/temp/tasks/，供轮询/清理。

文件存储（MVP 级），与 persistence 层方向一致；后续可换 repository。
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import fields
from pathlib import Path

from runtime.task_model import Task

# core/runtime/task_store.py → core/runtime → core → repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TASK_DIR = _REPO_ROOT / "data" / "temp" / "tasks"

# 允许写入 Task 的字段集合（用于 load 时过滤未知字段，容忍 schema 演进）
_TASK_FIELDS = {f.name for f in fields(Task)}


def _task_path(task_id: str) -> Path:
    return _TASK_DIR / f"{task_id}.json"


def save(task: Task) -> None:
    """原子写：先写临时文件再 os.replace，避免并发读到截断/半截 JSON。"""
    _TASK_DIR.mkdir(parents=True, exist_ok=True)
    target = _task_path(task.task_id)
    # 同目录临时文件 → os.replace（POSIX 上同文件系统 rename 原子）
    tmp = target.with_name(f"{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(
            json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp, target)
    finally:
        # 若 replace 前出错，清掉残留临时文件
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def load(task_id: str) -> Task | None:
    """读取任务。文件不存在 / 损坏 / schema 不匹配 → 返回 None（不抛，不让 500 击穿）。"""
    p = _task_path(task_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        # 并发写中途读到半截内容，或文件损坏
        return None
    if not isinstance(data, dict):
        return None
    # 只保留已知字段，容忍旧 schema 的多余字段；缺必填字段则视为损坏
    filtered = {k: v for k, v in data.items() if k in _TASK_FIELDS}
    try:
        return Task(**filtered)
    except TypeError:
        return None


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
