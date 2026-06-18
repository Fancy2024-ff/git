"""Regression guard for miniapp generation.

Canonical execution source of the miniapp project is
core/generator/codegen.py (generate_miniapp); skeleton fact source is
core/generator/src/templates/base. generate_miniapp must only copy that
template + overlay + inject app data — it must NOT re-author skeleton files.
These tests fail if generation drifts away from the template source.
"""

import json
from pathlib import Path

import pytest

from core.generator.codegen import generate_miniapp

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASE_TEMPLATE = PROJECT_ROOT / "core" / "generator" / "src" / "templates" / "base"


@pytest.fixture
def sample_app():
    return {
        "name": "AI Writing Assistant",
        "name_cn": "AI 写作助手",
        "description_cn": "支持文章、邮件、社交文案的 AI 写作助手，提供语法纠正与翻译。",
        "features_cn": ["语法纠正", "语气调整", "翻译"],
    }


@pytest.fixture
def sample_prd():
    return {"target_platforms": ["wechat", "alipay"]}


@pytest.fixture
def generated(sample_app, sample_prd, tmp_path):
    miniapp_dir, gen_source = generate_miniapp(sample_app, sample_prd, tmp_path)
    return miniapp_dir, gen_source


def test_canonical_vite_config_ts_only(generated):
    miniapp_dir, _ = generated
    assert (miniapp_dir / "vite.config.ts").exists()
    # .mjs would silently break the build (uni is not a function).
    assert not (miniapp_dir / "vite.config.mjs").exists()


def test_manifest_and_pages_under_src(generated):
    miniapp_dir, _ = generated
    assert (miniapp_dir / "src" / "manifest.json").exists()
    assert (miniapp_dir / "src" / "pages.json").exists()
    # NOT at project root
    assert not (miniapp_dir / "manifest.json").exists()
    assert not (miniapp_dir / "pages.json").exists()


def test_key_skeleton_files_present(generated):
    miniapp_dir, _ = generated
    for rel in [
        "package.json", "tsconfig.json", "index.html", "vite.config.ts",
        "src/main.ts", "src/App.vue", "src/uni.scss", "src/utils/request.ts",
        "src/pages/index/index.vue", "src/pages/form/form.vue",
        "src/pages/result/result.vue", "src/pages/profile/profile.vue",
    ]:
        assert (miniapp_dir / rel).exists(), f"missing {rel}"


def test_no_unfilled_tokens(generated):
    """Token contract must be fully substituted — no __APP_*__ left behind."""
    miniapp_dir, _ = generated
    for f in miniapp_dir.rglob("*"):
        if f.is_file() and f.suffix in (".vue", ".json", ".ts", ".md", ".html"):
            text = f.read_text(encoding="utf-8")
            assert "__APP_" not in text, f"unfilled token in {f.relative_to(miniapp_dir)}"


def test_app_data_injected(generated, sample_app):
    miniapp_dir, _ = generated
    index = (miniapp_dir / "src" / "pages" / "index" / "index.vue").read_text(encoding="utf-8")
    assert sample_app["name_cn"] in index
    for feat in sample_app["features_cn"]:
        assert feat in index
    pkg = json.loads((miniapp_dir / "package.json").read_text(encoding="utf-8"))
    assert pkg["description"] == sample_app["description_cn"]


def test_deps_come_from_template(generated):
    """package.json deps/scripts must equal the template's — no Python-side copy."""
    miniapp_dir, _ = generated
    template_pkg = json.loads((BASE_TEMPLATE / "package.json").read_text(encoding="utf-8-sig"))
    gen_pkg = json.loads((miniapp_dir / "package.json").read_text(encoding="utf-8"))
    assert gen_pkg["devDependencies"] == template_pkg["devDependencies"]
    assert gen_pkg["dependencies"] == template_pkg["dependencies"]
    assert gen_pkg["scripts"] == template_pkg["scripts"]


def test_vite_config_matches_template_exactly(generated):
    """The build-critical config must be byte-identical to the canonical template."""
    miniapp_dir, _ = generated
    template_cfg = (BASE_TEMPLATE / "vite.config.ts").read_text(encoding="utf-8")
    gen_cfg = (miniapp_dir / "vite.config.ts").read_text(encoding="utf-8")
    assert gen_cfg == template_cfg


def test_all_generated_text_is_clean_utf8(generated):
    """No mojibake / non-UTF-8 in generated text artifacts."""
    miniapp_dir, _ = generated
    for f in miniapp_dir.rglob("*"):
        if f.is_file() and f.suffix in (".vue", ".json", ".ts", ".md", ".html"):
            raw = f.read_bytes()
            if raw[:3] == b"\xef\xbb\xbf":
                raw = raw[3:]
            text = raw.decode("utf-8")  # raises on non-UTF-8
            assert "�" not in text, f"replacement char in {f.name}"
