"""真实 HTTP image provider。

约定一个通用的"提交任务 + 轮询"REST 协议（多数图像 API 通用）：
  POST {IMAGE_API_BASE}/tasks            {operation, image} → {task_id, status}
  GET  {IMAGE_API_BASE}/tasks/{id}        → {status, result_url}
不同 vendor 字段差异在此适配；上层只见 ProviderTask。

本轮真接通 operation：remove_background。
"""

from __future__ import annotations

import os

import httpx

from integrations.image_providers.base import ImageProvider, ProviderTask
from integrations.image_providers.errors import ImageProviderError, ImageErrorCode


class HttpImageProvider(ImageProvider):
    name = "http"
    supported_operations = ["remove_background"]  # 本轮真接通

    def __init__(self, base: str | None = None, key: str | None = None, timeout: float | None = None):
        self.base = (base or os.getenv("IMAGE_API_BASE", "")).rstrip("/")
        self.key = key or os.getenv("IMAGE_API_KEY", "")
        self.timeout = timeout or float(os.getenv("IMAGE_TIMEOUT_SECONDS", "30"))

    def is_configured(self) -> bool:
        return bool(self.base and self.key)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}

    def _map_http_error(self, status_code: int) -> str:
        if status_code in (401, 403):
            return ImageErrorCode.AUTH_FAILED
        if status_code == 400:
            return ImageErrorCode.INVALID_REQUEST
        return ImageErrorCode.UPSTREAM_ERROR

    def create_task(self, operation: str, image_ref: str, **params) -> ProviderTask:
        if not self.is_configured():
            raise ImageProviderError(ImageErrorCode.PROVIDER_MISSING, "缺 IMAGE_API_BASE/IMAGE_API_KEY")
        if operation not in self.supported_operations:
            raise ImageProviderError(ImageErrorCode.UNSUPPORTED, f"provider 暂不支持 {operation}")
        try:
            resp = httpx.post(
                f"{self.base}/tasks", headers=self._headers(),
                json={"operation": operation, "image": image_ref, **params},
                timeout=self.timeout,
            )
        except httpx.TimeoutException:
            raise ImageProviderError(ImageErrorCode.TIMEOUT, "create_task 超时")
        except httpx.HTTPError as e:
            raise ImageProviderError(ImageErrorCode.UPSTREAM_ERROR, str(e)[:200])
        if resp.status_code >= 400:
            raise ImageProviderError(self._map_http_error(resp.status_code), f"HTTP {resp.status_code}")
        data = resp.json()
        return ProviderTask(
            provider_task_id=str(data.get("task_id") or data.get("id") or ""),
            status=data.get("status", "processing"),
            result_url=data.get("result_url", ""),
            raw=data,
        )

    def poll_task(self, provider_task_id: str) -> ProviderTask:
        if not self.is_configured():
            raise ImageProviderError(ImageErrorCode.PROVIDER_MISSING)
        try:
            resp = httpx.get(f"{self.base}/tasks/{provider_task_id}",
                             headers=self._headers(), timeout=self.timeout)
        except httpx.TimeoutException:
            raise ImageProviderError(ImageErrorCode.TIMEOUT, "poll_task 超时")
        except httpx.HTTPError as e:
            raise ImageProviderError(ImageErrorCode.UPSTREAM_ERROR, str(e)[:200])
        if resp.status_code >= 400:
            raise ImageProviderError(self._map_http_error(resp.status_code), f"HTTP {resp.status_code}")
        data = resp.json()
        return ProviderTask(
            provider_task_id=provider_task_id,
            status=data.get("status", "processing"),
            result_url=data.get("result_url", ""),
            raw=data,
        )

    def get_result(self, provider_task_id: str) -> dict:
        t = self.poll_task(provider_task_id)
        if t.status != "succeeded":
            raise ImageProviderError(ImageErrorCode.RESULT_NOT_READY, f"status={t.status}")
        return {"result_url": t.result_url, "raw": t.raw}
