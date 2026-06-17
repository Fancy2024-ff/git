"""平台层统一状态表达（单一事实源）。

所有平台（wechat/alipay/douyin/telegram）共用这套状态常量，
不允许各平台自造字符串。
"""

from __future__ import annotations


class AuthStatus:
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"


class UploadStatus:
    NOT_UPLOADED = "not_uploaded"      # 未上传（含未开始 not_started 语义）
    UPLOADED = "uploaded"              # 开发版已上传
    UPLOAD_FAILED = "upload_failed"    # 上传失败

    ALL = (NOT_UPLOADED, UPLOADED, UPLOAD_FAILED)


class ReviewStatus:
    NOT_SUBMITTED = "review_not_submitted"
    PENDING = "review_pending"
    PASSED = "review_passed"
    REJECTED = "review_rejected"

    ALL = (NOT_SUBMITTED, PENDING, PASSED, REJECTED)


class UploadErrorCode:
    CONFIG_MISSING = "config_missing"
    DIST_MISSING = "dist_missing"
    CLI_MISSING = "cli_missing"
    UPLOAD_DISABLED = "upload_disabled"
    AUTH_FAILED = "auth_failed"
    UPSTREAM_FAILED = "upstream_failed"
    TIMEOUT = "timeout"


# submit-status.json 用的精简上传态（与历史前端字段兼容）
def to_submit_status_value(upload_status: str) -> str:
    """公共 UploadStatus → submit-status.json 历史字段值（uploaded/failed/not_started）。"""
    return {
        UploadStatus.UPLOADED: "uploaded",
        UploadStatus.UPLOAD_FAILED: "failed",
        UploadStatus.NOT_UPLOADED: "not_started",
    }.get(upload_status, "not_started")
