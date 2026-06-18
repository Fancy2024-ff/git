"""core.opportunity 测试：scoring / viral_score / classifier。"""

from core.opportunity.scoring import compute_opportunity_score
from core.opportunity.viral_score import compute_viral_score
from core.opportunity.classifier import classify


def _app(**kw):
    base = {
        "name": "AI Avatar Maker", "name_cn": "AI头像生成",
        "category": "Photo & Video",
        "description": "ai avatar generator", "description_cn": "AI 头像生成",
        "features": ["avatar"], "features_cn": ["头像生成", "表情包"],
        "downloads": 1000000, "rating": 4.6, "monetization": "freemium",
    }
    base.update(kw)
    return base


def test_opportunity_score_shape():
    app = _app()
    analysis = {"demand_score": 80}
    gap = {"gap_score": 70, "recommended_platforms": ["wechat"], "missing_platforms": ["wechat"], "platforms_checked": ["wechat", "alipay"]}
    r = compute_opportunity_score(app, analysis, gap)
    assert 0 <= r["opportunity_score"] <= 100
    assert r["total_score"] == r["opportunity_score"]
    assert r["viral_score"] == 50
    assert r["viral_weight"] > 0
    assert r["recommendation"] in ("立即执行", "值得尝试", "暂缓")
    assert r["target_platforms"] == ["wechat"]


def test_opportunity_score_uses_viral_dimension():
    app = _app()
    analysis = {"demand_score": 70}
    gap = {"gap_score": 70, "recommended_platforms": ["wechat"], "missing_platforms": ["wechat"], "platforms_checked": ["wechat"]}
    low = compute_opportunity_score(app, analysis, gap, viral={"viral_score": 30})
    high = compute_opportunity_score(app, analysis, gap, viral={"viral_score": 90})
    assert high["opportunity_score"] > low["opportunity_score"]
    assert high["viral_score"] == 90


def test_viral_score_high_for_avatar():
    r = compute_viral_score(_app())
    assert 0 <= r["viral_score"] <= 100
    assert r["tier"] in ("high", "medium", "low")
    assert set(r["dimensions"]) == {
        "share_trigger", "social_proof", "low_friction", "reward_loop", "emotion",
        "content_reusability", "watermark_tolerance", "unlock_mechanism_fit",
    }
    # avatar + photo/video 应判为高传播
    assert r["tier"] == "high"


def test_viral_score_lower_for_plain_tool():
    tool = _app(name="Invoice Tool", name_cn="发票工具", category="Productivity",
                description="invoice management", description_cn="发票管理",
                features=["invoice"], features_cn=["发票管理"], monetization="subscription")
    r = compute_viral_score(tool)
    assert r["viral_score"] < compute_viral_score(_app())["viral_score"]


def test_classifier_maps_theme_and_template():
    v = compute_viral_score(_app())
    s = classify(_app(), v)
    assert s["theme"] == "avatar"
    # avatar 题材必须映射到真实的传播型模板，不能再统一落到 ai-tool
    assert s["selected_template"] == "avatar-viral"
    assert s["priority"] in ("high", "medium", "normal")


def test_classifier_viral_themes_map_to_real_templates():
    """传播型题材映射到已落地的 *-viral 模板目录（不再统统落 ai-tool）。"""
    cases = [
        (dict(name="Avatar AI", name_cn="头像", description="avatar", description_cn="头像",
              features=["avatar"], features_cn=["头像"]), "avatar-viral"),
        (dict(name="Sticker AI", name_cn="表情", description="sticker meme", description_cn="表情包",
              features=["sticker"], features_cn=["表情包"]), "sticker-viral"),
        (dict(name="Pet Talk", name_cn="宠物说话", description="pet talk voice", description_cn="宠物配音",
              features=["pet"], features_cn=["宠物说话"]), "pet-talk-viral"),
        (dict(name="Funny Clip AI", name_cn="搞笑视频", description="funny video clip", description_cn="搞笑短视频",
              features=["funny video"], features_cn=["搞笑视频"]), "funny-video-viral"),
        (dict(name="Blessing Video", name_cn="祝福视频", description="blessing greeting video", description_cn="节日祝福视频",
              features=["blessing video"], features_cn=["祝福视频"]), "blessing-video-viral"),
    ]
    for overrides, expected in cases:
        app = _app(**overrides)
        s = classify(app, compute_viral_score(app))
        assert s["selected_template"] == expected, f"{overrides['name']} -> {s['selected_template']}"



def test_classifier_default_for_unknown():
    app = _app(name="Mystery", name_cn="神秘", category="Other",
               description="xyz", description_cn="无关键词",
               features=["x"], features_cn=["功能"])
    s = classify(app, compute_viral_score(app))
    assert s["theme"] == "general-tool"
    assert s["selected_template"] == "ai-tool"
