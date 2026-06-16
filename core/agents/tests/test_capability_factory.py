"""能力工厂架构测试：分类层 + 能力注册表 + app_types 单一事实源。"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ---- app_types 单一事实源 ----

def test_six_app_types_defined():
    from capabilities.app_types import VALID_APP_TYPES
    assert set(VALID_APP_TYPES) == {
        "text_ai", "image_ai", "ocr_scan", "speech_ai", "video_light", "utility_tool",
    }


def test_template_and_capabilities_consistent():
    from capabilities.app_types import APP_TYPES, template_for, capabilities_for
    for atype in APP_TYPES:
        assert template_for(atype) == atype  # 模板名 = 类型名
        assert capabilities_for(atype)       # 每类都有所需能力


# ---- 规则分类：6 类典型输入 ----

@pytest.mark.parametrize("app,expected", [
    ({"name": "AI Writer", "description": "writing grammar translate summarize"}, "text_ai"),
    ({"name": "ID Photo", "name_cn": "证件照", "description": "id photo remove background"}, "image_ai"),
    ({"name": "Scanner", "description": "ocr scan document recognize text extract"}, "ocr_scan"),
    ({"name": "Voice Dub", "description": "tts text to speech voice 配音 朗读"}, "speech_ai"),
    ({"name": "Video Tool", "description": "video 封面 cover script 摘要 剪辑入口"}, "video_light"),
    ({"name": "Calc", "description": "calculator convert 单位 汇率 工具"}, "utility_tool"),
])
def test_rule_classification_six_types(app, expected):
    from capabilities.app_types import classify_by_rules
    assert classify_by_rules(app)["app_type"] == expected


def test_unknown_falls_back_to_text_ai():
    from capabilities.app_types import classify_by_rules
    r = classify_by_rules({"name": "zzz", "description": "完全无关键词的描述"})
    assert r["app_type"] == "text_ai"
    assert r["app_type_confidence"] <= 0.4  # 低置信回退


# ---- classifier 层：use_llm=False / LLM 失败 fallback ----

def test_classify_app_rule_mode():
    from classification.classifier import classify_app
    r = classify_app({"name": "ID Photo", "name_cn": "证件照", "description": "id photo remove background"}, use_llm=False)
    assert r["app_type"] == "image_ai"
    assert r["llm_used"] is False
    assert r["llm_fallback"] is False
    assert "image.process" in r["required_capabilities"]


def test_classify_app_llm_failure_falls_back(monkeypatch):
    # USE_LLM=true 但 LLM 抛错 → 必须 fallback 到规则，不抛异常
    from classification import classifier
    def boom(app):
        raise RuntimeError("llm down")
    monkeypatch.setattr(classifier, "_llm_classification", boom)
    r = classifier.classify_app({"name": "Writer", "description": "writing"}, use_llm=True)
    assert r["llm_used"] is False
    assert r["llm_fallback"] is True
    assert r["app_type"] == "text_ai"
    assert "llm_error" in r


# ---- 能力注册表：诚实状态 ----

def test_registry_text_configured_image_missing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")  # text 可配置
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    # 重新导入 registry 以反映 env（adapter 在 is_configured 时读 env，无需重载）
    from capabilities.registry import capability_status, split_configured
    assert capability_status("text.generate")["configured"] is True
    img = capability_status("image.process")
    assert img["configured"] is False
    assert img["status"] == "provider_missing"
    conf, miss = split_configured(["image.process"])
    assert miss == ["image.process"]


def test_utility_always_configured():
    from capabilities.registry import capability_status
    assert capability_status("utility.execute")["configured"] is True


def test_image_adapter_unconfigured_returns_honest_result(monkeypatch):
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    from capabilities.image_adapter import ImageAdapter
    res = ImageAdapter().run("id_photo", image_ref="x.jpg")
    assert res.ok is False
    assert res.configured is False
    assert "未接入" in res.error
