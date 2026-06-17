"""平台层就绪度聚合（单一事实源）。

把"上下文（qa/build/dist/configured/uploaded）"聚合成 submission-readiness 的统一字段。
runner 只负责收集上下文并调这里；不再自己拼 upload_ready/review_ready 语义。

字段契约（详见 docs/product/PLATFORM_READINESS_CONTRACT.md）：
- platform_readiness[].can_upload   该平台具备上传条件
- platform_readiness[].uploaded     该平台开发版已上传成功
- platform_readiness[].upload_status not_uploaded / uploaded / upload_failed
- 顶层 upload_ready      ∃ 平台 can_upload（"是否具备上传条件"，失败不漂移）
- 顶层 upload_completed  ∃ 平台 uploaded（"是否已上传成功"）
- 顶层 review_ready      ∃ 平台可进入审核提交阶段（见 compute_review_ready）
"""

from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parents[2]
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from platforms.common.status import UploadStatus
from platforms import registry


def normalize_platform_readiness(
    *,
    platform_id: str,
    status: str,
    configured: bool,
    missing_fields: list[str],
    qa_passed: bool,
    dist_exists: bool,
    uploaded: bool = False,
    upload_status: str = UploadStatus.NOT_UPLOADED,
    upload_path: str = "",
) -> dict:
    """构造单个平台的 readiness 项（元数据从 registry，状态由入参）。"""
    can_upload = bool(
        configured and qa_passed and dist_exists and registry.is_upload_automatable(platform_id)
    )
    disp = registry.get_platform_display(platform_id)

    blocking = []
    if not configured:
        blocking.append(f"未配置 {platform_id} 平台授权（缺: {', '.join(missing_fields) or 'AppID'}）")
    if not qa_passed:
        blocking.append("QA/构建未通过")
    if not dist_exists:
        blocking.append("构建产物缺失")

    if uploaded:
        next_action = "开发版已上传，去平台后台提交审核（人工）"
    elif upload_status == UploadStatus.UPLOAD_FAILED:
        next_action = "上传失败，检查配置/网络后重试"
    elif can_upload:
        next_action = "具备上传条件，可自动上传开发版"
    else:
        next_action = f"先解决: {'; '.join(blocking)}" if blocking else "等待上游产物"

    return {
        "platform": platform_id,
        "name_cn": disp["name_cn"],
        "name_en": disp["name_en"],
        "status": status,
        "configured": configured,
        "missing_fields": missing_fields,
        "can_upload": can_upload,
        "uploaded": uploaded,
        "upload_status": upload_status,
        # ready 仅表示"上游就绪可进入上传/提审流程"，非"已完成"
        "ready": bool(status == "active" and configured and qa_passed and dist_exists),
        "next_action": next_action,
        "submit_url": registry.get_submit_url(platform_id),
        "upload_path": upload_path,
        "automation_level": registry.get_automation_level(platform_id),
    }


def compute_upload_ready(platform_readiness: list[dict]) -> bool:
    """顶层 upload_ready = ∃ 平台 can_upload（具备上传条件）。"""
    return any(p.get("can_upload") for p in platform_readiness)


def compute_upload_completed(platform_readiness: list[dict]) -> bool:
    """顶层 upload_completed = ∃ 平台 uploaded（已上传成功）。"""
    return any(p.get("uploaded") for p in platform_readiness)


def compute_review_ready(platform_readiness: list[dict], *, qa_passed: bool,
                         materials_ready: bool, human_blockers: list[str]) -> bool:
    """顶层 review_ready = ∃ 平台满足"可进入审核提交阶段"。

    条件：平台已配置 + 已上传成功 + qa/materials 完成 + 无人工阻塞（截图/真机）。
    当前微信：即便上传成功，human_blockers（截图/真机）非空 → review_ready 仍为 False。
    """
    if human_blockers:
        return False
    if not (qa_passed and materials_ready):
        return False
    return any(p.get("configured") and p.get("uploaded") for p in platform_readiness)


def merge_platform_upload_result(platform_item: dict, upload_result: dict) -> dict:
    """把一次平台上传结果合并进 platform_readiness 项（就地语义，返回新 dict）。"""
    item = dict(platform_item)
    passed = bool(upload_result.get("upload_passed"))
    item["uploaded"] = passed
    item["upload_status"] = UploadStatus.UPLOADED if passed else UploadStatus.UPLOAD_FAILED
    if passed:
        item["next_action"] = "开发版已上传，去平台后台提交审核（人工）"
    else:
        item["next_action"] = upload_result.get("next_action") or "上传失败，检查配置/网络后重试"
    return item


def build_submission_readiness_summary(platform_readiness: list[dict], *, qa_passed: bool,
                                       materials_ready: bool, human_blockers: list[str]) -> dict:
    """聚合顶层 upload_ready / upload_completed / review_ready。"""
    return {
        "upload_ready": compute_upload_ready(platform_readiness),
        "upload_completed": compute_upload_completed(platform_readiness),
        "review_ready": compute_review_ready(
            platform_readiness, qa_passed=qa_passed,
            materials_ready=materials_ready, human_blockers=human_blockers),
    }
