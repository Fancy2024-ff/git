"""core.opportunity.classifier — 题材归类 + 模板类型选择。

职责：根据候选 App 的题材，判断"该做什么方向"以及"用哪个模板类型"。
产物 = template-selection.json（由 pipeline 写盘）。

模板类型与 core/generator 对齐：当前生成真源支持 base/ai-tool 骨架与
avatar / sticker / pet-talk / funny-video / blessing-video 五类传播型模板。
新增题材只需在这里新增映射 + 在 generator 注册模板，pipeline 不改。
"""

from __future__ import annotations

# 题材 -> 模板类型。template 字段是传给 generator 的模板名，必须与
# core/generator/src/templates/ 下的真实目录一致。
# 传播型题材落到对应的 *-viral 模板（已落地）；其余落到通用 ai-tool。
# funny-video / blessing-video 已落地到真实 *-viral 模板。
_THEME_RULES = [
    # (关键词, 题材标签, 目标模板, 说明)
    (["avatar", "头像", "face", "换脸", "写真", "portrait"], "avatar", "avatar-viral", "AI 头像/写真"),
    (["sticker", "表情", "meme", "emoji", "卡通"], "sticker", "sticker-viral", "表情包/贴纸"),
    (["pet", "宠物", "talk", "说话", "voice", "配音"], "pet-talk", "pet-talk-viral", "宠物说话/配音"),
    (["blessing", "祝福", "greeting", "新年", "节日"], "blessing-video", "blessing-video-viral", "祝福视频/贺卡"),
    (["funny", "搞笑", "video", "视频", "clip"], "funny-video", "funny-video-viral", "搞笑短视频"),
    (["photo", "图片", "image", "art", "绘画", "draw"], "image-tool", "ai-image", "图像处理/生成"),
    (["writing", "写作", "translate", "翻译", "text", "summarize", "摘要"], "text-tool", "ai-tool", "文本/写作类"),
]
_DEFAULT = ("general-tool", "ai-tool", "通用 AI 工具")


def _text(app: dict) -> str:
    parts = [
        app.get("name", ""), app.get("name_cn", ""),
        app.get("category", ""), app.get("description", ""),
        app.get("description_cn", ""),
        " ".join(app.get("features", []) or []),
        " ".join(app.get("features_cn", []) or []),
    ]
    return " ".join(parts).lower()


def classify(app: dict, viral: dict | None = None) -> dict:
    """归类题材并选择模板类型。返回 template-selection.json 内容。

    采用「命中数最多者胜」的打分匹配，而非「第一个命中即胜」：题材描述常常
    同时命中多条规则（如搞笑视频也含 meme），按命中关键词数量择优更稳健，
    数量相同则按 _THEME_RULES 顺序作为优先级 tiebreaker。
    """
    text = _text(app)

    theme, template, theme_label = _DEFAULT
    matched_keywords: list[str] = []

    best_score = 0
    for keywords, t_theme, t_template, label in _THEME_RULES:
        hits = [kw for kw in keywords if kw in text]
        if len(hits) > best_score:
            best_score = len(hits)
            theme = t_theme
            template = t_template
            theme_label = label
            matched_keywords = hits

    viral_tier = (viral or {}).get("tier", "unknown")
    # 传播力高的题材建议优先排期
    priority = "high" if viral_tier == "high" else ("medium" if viral_tier == "medium" else "normal")

    return {
        "app_name": app.get("name", ""),
        "app_name_cn": app.get("name_cn", ""),
        "theme": theme,
        "theme_label": theme_label,
        "selected_template": template,
        "matched_keywords": matched_keywords,
        "viral_tier": viral_tier,
        "priority": priority,
        "rationale": f"题材归类为「{theme_label}」，选用模板 {template}；传播力 {viral_tier}，排期优先级 {priority}。",
        "data_source": "demo_rule_based",
    }
