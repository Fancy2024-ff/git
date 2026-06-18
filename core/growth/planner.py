"""core.growth.planner — 增长策略，产出 growth-plan.md。

职责：基于候选 + viral score + 模板选择，生成可执行的增长计划正文。
规则版 v1。产物 = growth-plan.md。
"""

from __future__ import annotations


def build_growth_plan(app: dict, viral: dict, selection: dict) -> str:
    """生成 growth-plan.md 正文（markdown）。"""
    name = app.get("name_cn") or app.get("name", "小程序")
    tier = viral.get("tier", "unknown")
    score = viral.get("viral_score", 0)
    theme_label = selection.get("theme_label", "通用工具")
    dims = viral.get("dimensions", {})

    # 按传播力分层给不同的增长重心
    if tier == "high":
        focus = "以裂变拉新为主引擎，分享即增长"
        channels = ["微信社群裂变", "朋友圈晒结果", "短视频平台话题挑战", "小程序互推"]
    elif tier == "medium":
        focus = "分享钩子 + 内容种草并重"
        channels = ["微信社群", "小红书种草", "朋友圈", "公众号导流"]
    else:
        focus = "工具价值留存为主，增长靠口碑与复用"
        channels = ["搜索流量", "公众号", "工具类聚合导流"]

    reward_hint = "高" if dims.get("reward_loop", 0) >= 70 else "中"

    lines = [
        f"# {name} 增长计划（growth-plan）",
        "",
        f"> 题材：{theme_label} ｜ Viral Score：{score}（{tier}）",
        "",
        "## 一、增长重心",
        f"- {focus}",
        f"- 裂变位适配度：{reward_hint}（reward_loop={dims.get('reward_loop', 0)}）",
        "",
        "## 二、冷启动（0 → 1000 用户）",
        "1. 种子用户：在 3-5 个精准社群投放可晒结果的样例",
        "2. 首屏即出结果：降低门槛，让用户 10 秒内产出可分享内容",
        "3. 结果页内置「分享得额度/解锁」钩子（见 share-strategy.md）",
        "",
        "## 三、增长渠道",
    ]
    for c in channels:
        lines.append(f"- {c}")
    lines += [
        "",
        "## 四、裂变回环设计",
        "- 邀请 N 位好友 → 解锁高级模板/去水印/额外次数",
        "- 结果页一键生成分享卡片，带小程序码回流",
        "- 排行榜/挑战赛激发二次创作与传播",
        "",
        "## 五、留存与变现",
        f"- 变现模式参考：{app.get('monetization', 'freemium')}",
        "- 免费出基础结果，付费/邀请解锁高级能力",
        "- 推送节日/热点题材，唤醒沉默用户",
        "",
        "## 六、关键指标",
        "- K 因子（每用户带来的新用户数）目标 > 1.0",
        "- 分享率（分享用户 / 出结果用户）目标 > 30%",
        "- 次日留存目标 > 25%",
        "",
        "> 本计划为规则版 v1，后续可由 LLM 按真实题材细化。",
        "",
    ]
    return "\n".join(lines)
