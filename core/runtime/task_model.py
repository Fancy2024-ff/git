"""统一任务模型：capability 的真实执行都表达为一个 Task。

状态机：CREATED → PROCESSING → (SUCCEEDED | FAILED | TIMEOUT) → CLEANED
绝不假完成：未接入 provider 的任务直接进 FAILED(provider_missing)，不停留在假 PROCESSING。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict


class TaskState:
    CREATED = "created"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CLEANED = "cleaned"

    ALL = (CREATED, PROCESSING, SUCCEEDED, FAILED, TIMEOUT, CLEANED)
    TERMINAL = (SUCCEEDED, FAILED, TIMEOUT, CLEANED)


# 合法状态转移
_TRANSITIONS = {
    TaskState.CREATED: {TaskState.PROCESSING, TaskState.SUCCEEDED, TaskState.FAILED, TaskState.TIMEOUT},
    TaskState.PROCESSING: {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.TIMEOUT},
    TaskState.SUCCEEDED: {TaskState.CLEANED},
    TaskState.FAILED: {TaskState.CLEANED},
    TaskState.TIMEOUT: {TaskState.CLEANED},
    TaskState.CLEANED: set(),
}


def can_transition(src: str, dst: str) -> bool:
    return dst in _TRANSITIONS.get(src, set())


@dataclass
class Task:
    capability_id: str
    operation: str
    task_id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    state: str = TaskState.CREATED
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    deadline: float | None = None        # 绝对时间戳；None=不限
    attempts: int = 0
    provider: str = ""
    result: dict = field(default_factory=dict)
    error_code: str = ""
    error_message: str = ""

    def transition(self, dst: str) -> None:
        if not can_transition(self.state, dst):
            from runtime.errors import RuntimeErrorCode
            raise ValueError(f"{RuntimeErrorCode.INVALID_STATE}: {self.state} -> {dst}")
        self.state = dst
        self.updated_at = time.time()

    def is_timed_out(self, now: float | None = None) -> bool:
        if self.deadline is None or self.state in TaskState.TERMINAL:
            return False
        return (now or time.time()) > self.deadline

    def to_dict(self) -> dict:
        return asdict(self)
