"""Runtime 层错误码（统一）。"""

from __future__ import annotations


class RuntimeErrorCode:
    PROVIDER_MISSING = "provider_missing"   # 能力未接入 provider
    UNSUPPORTED = "unsupported_operation"   # 不支持的操作
    TIMEOUT = "timeout"                     # 任务超时
    PROVIDER_ERROR = "provider_error"       # provider 执行抛错
    INVALID_STATE = "invalid_state"         # 非法状态转移
    NOT_FOUND = "task_not_found"            # 任务不存在
