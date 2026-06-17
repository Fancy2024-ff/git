"""微信审核提交（本轮未做自动提审，仅提供占位入口与诚实状态）。

自动提审涉及微信后台人工确认环节，本轮范围之外。
"""

from __future__ import annotations


def submit_for_review(**kwargs) -> dict:
    """自动提交审核 —— 本轮未接通，诚实返回 not_implemented。"""
    return {
        "review_passed": False,
        "status": "not_submitted",
        "error_code": "not_implemented",
        "message": "自动提审本轮未接入；开发版上传后需人工去 mp.weixin.qq.com 提交审核。",
        "next_action": "人工去微信后台提交审核",
    }
