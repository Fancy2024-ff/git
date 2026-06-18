"""core.opportunity.viral_score — Viral Score（传播力评分）。

新产品方向核心：判断一个小程序机会是否"有传播力"。规则版 v1（可解释），
后续可换 LLM。产物 = viral-score.json。

8 个维度（各 0-100），加权得 viral_score：
  - share_trigger        分享动机（结果值得晒/有趣/有用）
  - social_proof         社交货币（晒出来有面子/能引发讨论）
  - low_friction         使用门槛（打开即用、无需注册/付费即出结果）
  - reward_loop          激励回环（邀请得额度/解锁，可设计裂变位）
  - emotion              情绪强度（好玩/惊喜/治愈/搞笑/祝福类高传播）
  - content_reusability  内容复用性（结果可反复生成/批量产出，持续供给传播素材）
  - watermark_tolerance  带品牌传播容忍度（结果适合带水印/品牌露出而不影响体验）
  - unlock_mechanism_fit 分享解锁适配度（适合"分享后解锁高清/去水印/更多模板"）
"""

from __future__ import annotations

_WEIGHTS = {
    "share_trigger": 0.20,
    "social_proof": 0.18,
    "low_friction": 0.10,
    "reward_loop": 0.12,
    "emotion": 0.12,
    "content_reusability": 0.10,
    "watermark_tolerance": 0.08,
    "unlock_mechanism_fit": 0.10,
}

# 高传播题材关键词（命中则情绪/分享动机加成）
_VIRAL_KW = [
    "avatar", "头像", "sticker", "表情", "pet", "宠物", "talk", "说话",
    "funny", "搞笑", "video", "视频", "blessing", "祝福", "art", "绘画",
    "face", "换脸", "meme", "卡通", "comic", "漫画", "photo", "写真",
]
# 强情绪题材（治愈/惊喜/搞笑/祝福）
_EMOTION_KW = ["funny", "搞笑", "blessing", "祝福", "pet", "宠物", "meme", "treasure", "惊喜", "cute", "萌"]
# 需要付费/注册才出结果 → 门槛高
_FRICTION_KW = ["subscription", "订阅", "login", "登录", "account", "注册"]


def _text(app: dict) -> str:
    parts = [
        app.get("name", ""), app.get("name_cn", ""),
        app.get("category", ""), app.get("description", ""),
        app.get("description_cn", ""),
        " ".join(app.get("features", []) or []),
        " ".join(app.get("features_cn", []) or []),
    ]
    return " ".join(parts).lower()


def compute_viral_score(app: dict, opportunity: dict | None = None) -> dict:
    """计算 Viral Score。app 为归一化后的候选；opportunity 可选（用于交叉印证）。"""
    text = _text(app)
    hit_viral = [kw for kw in _VIRAL_KW if kw in text]
    hit_emotion = [kw for kw in _EMOTION_KW if kw in text]
    hit_friction = [kw for kw in _FRICTION_KW if kw in text]

    # 1. share_trigger：有可晒结果（图像/视频/趣味产出）越强
    share_trigger = 55 + min(35, len(hit_viral) * 12)
    if any(k in text for k in ("video", "视频", "avatar", "头像", "art", "绘画", "photo", "写真")):
        share_trigger = min(100, share_trigger + 10)

    # 2. social_proof：娱乐/创意类社交货币高，工具类偏低
    category = app.get("category", "")
    if category in ("Entertainment", "Photo & Video", "Graphics & Design"):
        social_proof = 85
    elif category in ("Productivity", "Utilities", "Education"):
        social_proof = 55
    else:
        social_proof = 65
    social_proof = min(100, social_proof + min(15, len(hit_viral) * 5))

    # 3. low_friction：默认高（小程序即点即用），命中付费/注册关键词则扣
    low_friction = 90
    low_friction -= 25 if hit_friction else 0
    monetization = app.get("monetization", "")
    if monetization in ("subscription", "freemium"):
        low_friction -= 10
    low_friction = max(30, low_friction)

    # 4. reward_loop：是否容易设计"邀请得额度/解锁"裂变位
    #    工具/额度型(freemium)天然适合；娱乐型靠分享解锁
    reward_loop = 60
    if monetization == "freemium":
        reward_loop += 20
    if any(k in text for k in ("unlock", "解锁", "额度", "credit", "invite", "邀请")):
        reward_loop += 15
    reward_loop = min(100, reward_loop)

    # 5. emotion：强情绪题材加成
    emotion = 50 + min(45, len(hit_emotion) * 18)
    emotion = min(100, emotion)

    # 6. content_reusability：内容是否可反复生成/批量产出（持续供给传播素材）。
    #    图像/视频/表情包类天然可批量产出；单次型工具复用性低。
    is_media = any(k in text for k in (
        "avatar", "头像", "sticker", "表情", "video", "视频", "photo", "写真",
        "art", "绘画", "meme", "卡通", "pack", "套图", "模板", "template",
    ))
    content_reusability = 80 if is_media else 50
    if any(k in text for k in ("template", "模板", "pack", "套图", "batch", "批量")):
        content_reusability = min(100, content_reusability + 15)

    # 7. watermark_tolerance：结果是否适合带品牌水印传播而不毁体验。
    #    视觉/视频成品适合（水印自然）；纯文本/工具结果带水印体验差。
    if any(k in text for k in ("avatar", "头像", "video", "视频", "photo", "写真", "art", "绘画", "sticker", "表情")):
        watermark_tolerance = 85
    elif any(k in text for k in ("writing", "写作", "text", "翻译", "translate", "摘要")):
        watermark_tolerance = 40
    else:
        watermark_tolerance = 60

    # 8. unlock_mechanism_fit：适合"分享后解锁高清/去水印/更多模板"。
    #    = 有可分级的成品（高低清/水印/模板数）+ freemium 适配。
    unlock_mechanism_fit = 55
    if is_media:
        unlock_mechanism_fit += 20
    if monetization == "freemium":
        unlock_mechanism_fit += 15
    if any(k in text for k in ("hd", "高清", "watermark", "水印", "unlock", "解锁", "premium", "高级")):
        unlock_mechanism_fit += 10
    unlock_mechanism_fit = min(100, unlock_mechanism_fit)

    viral_score = round(
        share_trigger * _WEIGHTS["share_trigger"]
        + social_proof * _WEIGHTS["social_proof"]
        + low_friction * _WEIGHTS["low_friction"]
        + reward_loop * _WEIGHTS["reward_loop"]
        + emotion * _WEIGHTS["emotion"]
        + content_reusability * _WEIGHTS["content_reusability"]
        + watermark_tolerance * _WEIGHTS["watermark_tolerance"]
        + unlock_mechanism_fit * _WEIGHTS["unlock_mechanism_fit"],
        1,
    )

    if viral_score >= 72:
        tier = "high"
        verdict = "高传播潜力：优先做，重点设计分享位与裂变回环"
    elif viral_score >= 55:
        tier = "medium"
        verdict = "中等传播潜力：可做，需强化分享钩子"
    else:
        tier = "low"
        verdict = "低传播潜力：靠工具价值留存，不依赖裂变"

    return {
        "app_name": app.get("name", ""),
        "app_name_cn": app.get("name_cn", ""),
        "viral_score": viral_score,
        "tier": tier,
        "verdict": verdict,
        "dimensions": {
            "share_trigger": share_trigger,
            "social_proof": social_proof,
            "low_friction": low_friction,
            "reward_loop": reward_loop,
            "emotion": emotion,
            "content_reusability": content_reusability,
            "watermark_tolerance": watermark_tolerance,
            "unlock_mechanism_fit": unlock_mechanism_fit,
        },
        "weights": _WEIGHTS,
        "signals": {
            "viral_keywords": hit_viral,
            "emotion_keywords": hit_emotion,
            "friction_keywords": hit_friction,
        },
        "data_source": "demo_rule_based",
    }
