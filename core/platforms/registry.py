"""平台层注册表：已接入平台的单一事实源。

描述每个平台的自动化等级、支持的动作、当前实现状态。
后续 alipay/douyin/telegram 照此注册扩展。
"""

from __future__ import annotations

# 平台动作
ACTION_UPLOAD = "upload"
ACTION_REVIEW = "review"
ACTION_MATERIALS = "materials"

# 实现状态
IMPL_IMPLEMENTED = "implemented"        # 已真实接入
IMPL_PARTIAL = "partial"                # 部分接入（如仅上传，未自动提审）
IMPL_NOT_IMPLEMENTED = "not_implemented"

_PLATFORMS: dict[str, dict] = {
    "wechat": {
        "platform_id": "wechat",
        "name_cn": "微信小程序",
        "name_en": "WeChat Mini Program",
        "automation_level": "semi_automatic",   # 开发版可自动上传，提审需人工
        "actions": {
            ACTION_UPLOAD: IMPL_IMPLEMENTED,      # miniprogram-ci 开发版上传已接入
            ACTION_REVIEW: IMPL_NOT_IMPLEMENTED,  # 自动提审未做
            ACTION_MATERIALS: IMPL_PARTIAL,       # 读取 listing-materials
        },
        "tool": "miniprogram-ci",
        "submit_url": "https://mp.weixin.qq.com",
    },
    # 占位：后续按同模式注册（当前未实现）
    "alipay": {
        "platform_id": "alipay", "name_cn": "支付宝小程序", "name_en": "Alipay Mini Program",
        "automation_level": "manual",
        "actions": {ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED,
                    ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED},
        "tool": "", "submit_url": "https://open.alipay.com/develop/manage",
    },
    "douyin": {
        "platform_id": "douyin", "name_cn": "抖音小程序", "name_en": "Douyin Mini Program",
        "automation_level": "manual",
        "actions": {ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED,
                    ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED},
        "tool": "", "submit_url": "https://developer.open-douyin.com",
    },
    "telegram": {
        "platform_id": "telegram", "name_cn": "Telegram Mini App", "name_en": "Telegram Mini App",
        "automation_level": "semi_automatic",
        "actions": {ACTION_UPLOAD: IMPL_NOT_IMPLEMENTED, ACTION_REVIEW: IMPL_NOT_IMPLEMENTED,
                    ACTION_MATERIALS: IMPL_NOT_IMPLEMENTED},
        "tool": "", "submit_url": "",
    },
}


def list_platforms() -> list[str]:
    return list(_PLATFORMS.keys())


def get_platform(platform_id: str) -> dict | None:
    return _PLATFORMS.get(platform_id)


def supports_action(platform_id: str, action: str) -> bool:
    """该平台是否已真实实现某动作（implemented 才算）。"""
    p = _PLATFORMS.get(platform_id)
    return bool(p and p["actions"].get(action) == IMPL_IMPLEMENTED)


def snapshot() -> dict:
    """平台层快照，供 API/前端/文档消费。"""
    return {
        "platforms": [
            {
                "platform_id": p["platform_id"],
                "name_cn": p["name_cn"],
                "automation_level": p["automation_level"],
                "actions": p["actions"],
                "tool": p["tool"],
            }
            for p in _PLATFORMS.values()
        ],
        "implemented_upload": [pid for pid in _PLATFORMS if supports_action(pid, ACTION_UPLOAD)],
    }
