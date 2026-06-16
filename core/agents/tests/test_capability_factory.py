"""能力工厂架构测试：app_types 单一事实源 + registry + 6 类 adapter + 状态表达。"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ── app_types 单一事实源 ──

def test_six_app_types_defined():
    from capabilities.app_types import VALID_APP_TYPES
    assert set(VALID_APP_TYPES) == {
        "text_ai", "image_ai", "ocr_scan", "speech_ai", "video_light", "utility_tool",
    }


def test_app_type_has_all_authoritative_fields():
    from capabilities import app_types as at
    for t in at.VALID_APP_TYPES:
        assert at.display_name_for(t)               # display_name
        assert at.default_template_for(t) == t       # template = type
        assert at.capabilities_for(t)                # required_capabilities
        assert at.typical_operations_for(t)          # typical_operations
        assert at.feasibility_for(t) in ("high", "medium", "low")


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
    assert r["app_type_confidence"] <= 0.4


# ── registry ──

def test_registry_returns_all_six_capabilities():
    from capabilities.registry import get_capability_registry
    reg = get_capability_registry()
    assert set(reg.keys()) == {
        "text.generate", "image.process", "vision.ocr",
        "speech.tts", "video.process", "utility.execute",
    }


def test_required_capabilities_for_app_type():
    from capabilities.registry import required_capabilities_for_app_type
    assert required_capabilities_for_app_type("image_ai") == ["image.process"]
    assert "speech.tts" in required_capabilities_for_app_type("speech_ai")


def test_snapshot_splits_configured_missing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    from capabilities.registry import build_capability_snapshot
    s = build_capability_snapshot("image_ai")
    assert s["app_type"] == "image_ai"
    assert s["missing_capabilities"] == ["image.process"]
    assert s["runnable_level"] == "buildable"


def test_speech_asr_alias_resolves():
    from capabilities.registry import get_adapter
    assert get_adapter("speech.asr").capability_name == "speech.tts"


# ── text adapter（不回归）──

def test_text_adapter_configured_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    from capabilities.text import TextAdapter
    a = TextAdapter()
    assert a.configured is True
    assert a.runtime_ready() is True
    assert "generate" in a.supported_operations


def test_text_adapter_provider_missing_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from capabilities.text import TextAdapter
    spec = TextAdapter().get_spec()
    assert spec.configured is False
    assert spec.status == "provider_missing"
    assert "ANTHROPIC_API_KEY" in spec.missing_requirements


# ── image adapter（第一条复杂能力范式）──

def test_image_adapter_has_four_operations():
    from capabilities.image import ImageAdapter
    assert ImageAdapter().supported_operations == [
        "remove_background", "id_photo", "avatar_style", "enhance",
    ]


def test_image_provider_missing_without_config(monkeypatch):
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    from capabilities.image import ImageAdapter
    a = ImageAdapter()
    assert a.configured is False
    assert a.status() == "provider_missing"
    # create_task / poll_task 状态可用且诚实
    created = a.create_task("id_photo", "x.jpg")
    assert created.success is False
    assert created.error_code == "provider_missing"
    assert created.data["task_id"] is None
    polled = a.poll_task("any")
    assert polled.success is False


def test_image_configured_when_both_env_present(monkeypatch):
    monkeypatch.setenv("IMAGE_API_KEY", "k")
    monkeypatch.setenv("IMAGE_API_BASE", "https://img")
    from capabilities.image import ImageAdapter
    a = ImageAdapter()
    assert a.configured is True
    created = a.create_task("id_photo", "x.jpg")
    assert created.success is True
    assert created.data["task_id"]


# ── vision / speech / video stub + utility local ──

def test_stub_capabilities_provider_missing(monkeypatch):
    for env in ("VISION_API_KEY", "SPEECH_API_KEY", "VIDEO_API_KEY"):
        monkeypatch.delenv(env, raising=False)
    from capabilities.vision import VisionAdapter
    from capabilities.speech import SpeechAdapter
    from capabilities.video import VideoAdapter
    for A, ops in [(VisionAdapter, "ocr"), (SpeechAdapter, "tts"), (VideoAdapter, "summarize")]:
        a = A()
        assert a.configured is False
        assert a.status() == "provider_missing"
        assert ops in a.supported_operations


def test_utility_local_runtime_ready():
    from capabilities.utility import UtilityAdapter
    a = UtilityAdapter()
    assert a.configured is True
    assert a.runtime_ready() is True
    assert a.status() == "runtime_ready"
    res = a.execute("calculate", args={"a": 2, "b": 3, "op": "add"})
    assert res.success is True
    assert res.data["result"] == 5


# ── 端到端快照 ──

def test_snapshots_for_three_app_types(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.delenv("IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_API_BASE", raising=False)
    from capabilities.registry import build_capability_snapshot
    assert build_capability_snapshot("text_ai")["runnable_level"] == "runtime_ready"
    assert build_capability_snapshot("image_ai")["runnable_level"] == "buildable"
    assert build_capability_snapshot("utility_tool")["runnable_level"] == "runtime_ready"
