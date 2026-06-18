"""core.qa 三层质检回归：growth_qa（含生成代码传播链路）+ compliance_qa（含敏感词扫描）。"""

import json
from pathlib import Path

from core.qa.growth_qa import run_growth_qa
from core.qa.compliance_qa import run_compliance_qa


def _make_growth_artifacts(output_dir: Path):
    (output_dir / "growth-plan.md").write_text(
        "# 增长计划\n## 增长重心\n## 渠道\n## 裂变\n## 指标\n", encoding="utf-8"
    )
    (output_dir / "share-strategy.md").write_text(
        "# 分享\n## 分享钩子\n## 激励\n## 裂变\n## 去水印\n", encoding="utf-8"
    )
    (output_dir / "viral-score.json").write_text(
        json.dumps({"viral_score": 80}), encoding="utf-8"
    )


def _make_miniapp_with_propagation(miniapp_dir: Path):
    pages = miniapp_dir / "src" / "pages"
    (pages / "result").mkdir(parents=True, exist_ok=True)
    (pages / "result" / "result.vue").write_text(
        "<template><button @click=\"share\">保存并分享</button>"
        "<text>分享解锁高清，邀请好友去水印</text></template>",
        encoding="utf-8",
    )


def test_growth_qa_passes_with_propagation_chain(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    mini = tmp_path / "mini"
    mini.mkdir()
    _make_growth_artifacts(out)
    _make_miniapp_with_propagation(mini)

    result = run_growth_qa(out, miniapp_dir=mini)
    assert result["passed"], result["issues"]
    assert result["checks"]["code_has_share_cta"] is True
    assert result["checks"]["code_has_unlock_hook"] is True
    assert result["checks"]["code_has_result_page"] is True


def test_growth_qa_flags_missing_propagation(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    mini = tmp_path / "mini"
    (mini / "src" / "pages" / "index").mkdir(parents=True)
    (mini / "src" / "pages" / "index" / "index.vue").write_text(
        "<template><text>纯工具，无传播位</text></template>", encoding="utf-8"
    )
    _make_growth_artifacts(out)

    result = run_growth_qa(out, miniapp_dir=mini)
    assert result["checks"]["code_has_share_cta"] is False
    assert not result["passed"]


def test_compliance_qa_detects_marketing_and_sensitive_words(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    mini = tmp_path / "mini"
    docs = mini / "docs"
    docs.mkdir(parents=True)
    (docs / "privacy-policy.md").write_text(
        "信息收集\n信息使用\n信息存储\n", encoding="utf-8"
    )
    (docs / "user-agreement.md").write_text("用户协议", encoding="utf-8")
    pkg = out / "publish-package"
    pkg.mkdir()
    (pkg / "review-notes.md").write_text("审核备注", encoding="utf-8")
    # 上架文案含过度营销词 + 敏感词
    (out / "listing-materials.json").write_text(
        json.dumps({"slogan": "全网最好用，100% 永久免费", "desc": "支持贷款理财"},
                   ensure_ascii=False),
        encoding="utf-8",
    )

    result = run_compliance_qa(mini, out)
    # 硬性合规闸通过（材料齐全），但敏感词为 warning
    assert result["passed"], result["issues"]
    assert result["checks"]["no_overmarketing_words"] is False
    assert result["checks"]["no_sensitive_words"] is False
    assert any("营销" in w for w in result["warnings"])
    assert any("敏感" in w for w in result["warnings"])


def test_compliance_qa_clean_listing_has_no_warnings(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    mini = tmp_path / "mini"
    docs = mini / "docs"
    docs.mkdir(parents=True)
    (docs / "privacy-policy.md").write_text(
        "信息收集\n信息使用\n信息存储\n", encoding="utf-8"
    )
    (docs / "user-agreement.md").write_text("用户协议", encoding="utf-8")
    pkg = out / "publish-package"
    pkg.mkdir()
    (pkg / "review-notes.md").write_text("审核备注", encoding="utf-8")
    (out / "listing-materials.json").write_text(
        json.dumps({"slogan": "帮你快速生成头像", "desc": "AI 头像生成工具"},
                   ensure_ascii=False),
        encoding="utf-8",
    )

    result = run_compliance_qa(mini, out)
    assert result["passed"]
    assert result["warnings"] == []
