"""image provider 标准错误码（统一，供上层映射）。"""

from __future__ import annotations


class ImageProviderError(Exception):
    """带标准错误码的 provider 异常。"""
    def __init__(self, code: str, message: str = ""):
        self.code = code
        self.message = message or code
        super().__init__(f"{code}: {self.message}")


class ImageErrorCode:
    PROVIDER_MISSING = "provider_missing"   # 未配置 env
    AUTH_FAILED = "auth_failed"             # 401/403
    INVALID_REQUEST = "invalid_request"     # 400/参数错
    UPSTREAM_ERROR = "upstream_error"       # 5xx/网络
    TIMEOUT = "timeout"                     # 超时
    RESULT_NOT_READY = "result_not_ready"   # 轮询未完成
    UNSUPPORTED = "unsupported_operation"   # provider 不支持该 operation
