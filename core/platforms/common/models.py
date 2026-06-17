"""平台层通用数据结构（单一事实源）。

各平台上传/授权/审核结果统一用这些结构，不再各写一套裸 dict。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from platforms.common.status import AuthStatus, UploadStatus, ReviewStatus


@dataclass
class PlatformAuthStatus:
    platform_id: str
    configured: bool
    missing_fields: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return AuthStatus.CONFIGURED if self.configured else AuthStatus.NOT_CONFIGURED

    def to_dict(self) -> dict:
        return {**asdict(self), "status": self.status}


@dataclass
class PlatformNextAction:
    owner: str          # "agent" | "human"
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PlatformUploadResult:
    """各平台上传统一结果。平台层内部一律产出此结构，再序列化给 API。"""
    platform_id: str
    upload_passed: bool
    upload_status: str          # UploadStatus.*
    provider: str               # 工具/供应商，如 miniprogram-ci
    dist_path: str = ""
    appid: str = ""
    version: str = ""
    message: str = ""
    error_code: str = ""
    raw_output: str = ""
    next_action: PlatformNextAction | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["next_action"] = self.next_action.text if self.next_action else ""
        d["next_action_owner"] = self.next_action.owner if self.next_action else "human"
        # 兼容历史前端字段
        d["status"] = {"uploaded": "uploaded", "upload_failed": "failed",
                       "not_uploaded": "not_started"}.get(self.upload_status, "not_started")
        d["tool"] = self.provider
        d["raw_output"] = (self.raw_output or "")[-1500:]
        return d


@dataclass
class PlatformReviewStatus:
    platform_id: str
    review_status: str = ReviewStatus.NOT_SUBMITTED
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
