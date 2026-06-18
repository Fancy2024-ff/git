"""core.growth.share_strategy — 分享/裂变策略，产出 share-strategy.md。

职责：设计分享钩子、激励策略、去水印/去广告建议、裂变传播路径。
规则版 v1。产物 = share-strategy.md。
"""

from __future__ import annotations


def build_share_strategy(app: dict, viral: dict, selection: dict) -> str:
    """生成 share-strategy.md 正文（markdown）。"""
    name = app.get("name_cn") or app.get("name", "小程序")
    theme = selection.get("theme", "general-tool")
    theme_label = selection.get("theme_label", "通用工具")
    dims = viral.get("dimensions", {})
    tier = viral.get("tier", "unknown")

    # 题材相关的分享钩子
    hooks_by_theme = {
        "avatar": ["生成专属头像后引导「换一张」并分享对比", "节日限定头像框，分享解锁"],
        "sticker": ["一键打包表情到微信", "热点梗表情，蹭话题传播"],
        "pet-talk": ["宠物配音视频一键分享到朋友圈", "邀请好友给同一只宠物配音 PK"],
        "funny-video": ["搞笑成片带话题标签分享到短视频平台", "合拍/接龙玩法"],
        "blessing-video": ["节日祝福视频带名字定制，转发给亲友", "群发祝福裂变"],
        "image-tool": ["处理前后对比图分享", "去水印需邀请解锁"],
        "text-tool": ["生成结果一键转发", "邀请得免费次数"],
        "general-tool": ["结果页一键分享", "邀请得额度"],
    }
    hooks = hooks_by_theme.get(theme, hooks_by_theme["general-tool"])

    low_friction = dims.get("low_friction", 0)
    watermark_advice = (
        "免费版结果带轻量水印（含小程序码），邀请 / 付费去水印——既保留传播入口又留变现空间"
        if low_friction >= 60
        else "降低门槛优先，水印仅放小程序码，不影响体验"
    )

    lines = [
        f"# {name} 分享策略（share-strategy）",
        "",
        f"> 题材：{theme_label} ｜ 传播力分层：{tier}",
        "",
        "## 一、分享钩子（Share Hooks）",
    ]
    for h in hooks:
        lines.append(f"- {h}")
    lines += [
        "",
        "## 二、激励策略（Incentive）",
        "- 邀请好友：每邀请 1 人 +1 次免费额度 / 解锁 1 个高级模板",
        "- 分享解锁：分享到朋友圈/群解锁本次高清/去水印结果",
        "- 连续使用：签到/连续生成累积积分兑换权益",
        "",
        "## 三、去水印 / 去广告建议",
        f"- {watermark_advice}",
        "- 分享卡片右下角固定小程序码，保证每次传播都能回流",
        "- 广告位避免打断「出结果 → 分享」主路径，放在结果已展示之后",
        "",
        "## 四、裂变传播路径",
        "1. 用户出结果 → 2. 结果页引导分享（钩子）→ 3. 好友点开小程序码 →",
        "4. 好友落地即出结果（低门槛）→ 5. 好友再次分享（回环）",
        "",
        "## 五、分享物料",
        "- 自动生成带结果 + 小程序码的分享卡片",
        "- 题材化文案模板（喜庆/搞笑/惊喜），一键带出",
        "",
        "> 本策略为规则版 v1，后续可由 LLM 按真实题材与平台规则细化。",
        "",
    ]
    return "\n".join(lines)
