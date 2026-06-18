"""core.growth 测试：planner / share_strategy 产物含必要要素。"""

from core.growth.planner import build_growth_plan
from core.growth.share_strategy import build_share_strategy


_APP = {"name": "AI Avatar", "name_cn": "AI头像", "monetization": "freemium"}
_VIRAL = {"viral_score": 89.0, "tier": "high", "dimensions": {"reward_loop": 80, "low_friction": 90}}
_SEL = {"theme": "avatar", "theme_label": "AI 头像/写真", "selected_template": "ai-tool"}


def test_growth_plan_has_required_sections():
    md = build_growth_plan(_APP, _VIRAL, _SEL)
    for kw in ["增长重心", "渠道", "裂变", "指标"]:
        assert kw in md


def test_share_strategy_has_required_sections():
    md = build_share_strategy(_APP, _VIRAL, _SEL)
    for kw in ["分享钩子", "激励", "裂变", "水印"]:
        assert kw in md


def test_share_strategy_theme_specific_hooks():
    md = build_share_strategy(_APP, _VIRAL, _SEL)
    # avatar 题材应出现头像相关钩子
    assert "头像" in md
