"""产品决策 artifacts 写出：5 个文件。

demand-analysis.json / miniapp-feasibility-report.json / mvp-split-plan.json /
execution-decision.json / demand-analysis.md
"""

from __future__ import annotations

import json
from pathlib import Path


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_markdown(result: dict) -> str:
    d = result["demand"]
    dec = result["decision"]
    feas = result["feasibility"]
    plan = result["split_plan"]
    rec_cn = {
        "immediate_execute": "立即执行", "split_then_execute": "拆分后执行",
        "research_only": "仅调研", "reject": "不建议做",
    }.get(dec["recommendation"], dec["recommendation"])
    lines = [
        f"# 产品决策摘要：{d.get('app_name_cn') or d.get('app_name')}",
        "",
        f"- **执行建议**：{rec_cn}（{dec['recommendation']}），置信度 {dec['confidence']}",
        f"- **市场机会分**：{dec['market_opportunity_score']} / 100",
        f"- **小程序落地性分**：{dec['miniapp_feasibility_score']} / 100",
        f"- **品牌风险**：{dec['brand_risk_score']}　**审核风险**：{dec['review_risk_score']}",
        f"- **下一步**：{dec['next_action']}",
    ]
    if dec.get("blocking_reasons"):
        lines.append(f"- **阻塞项**：{'；'.join(dec['blocking_reasons'])}")
    lines += [
        "", "## 判断理由", dec.get("reason", ""),
        "", "## 推荐 MVP",
        f"- 名称：{plan['recommended_mvp'].get('name')}",
        f"- 类型：{plan['recommended_mvp'].get('app_type')}",
        f"- 首版范围：{'、'.join(plan['recommended_mvp'].get('first_version_scope', []))}",
        f"- 理由：{plan['recommended_mvp'].get('reason')}",
    ]
    if plan.get("non_replicable_features"):
        lines.append("")
        lines.append("## 不可迁移功能 + 替代")
        for nf in plan["non_replicable_features"]:
            lines.append(f"- ✗ {nf}")
        for s in plan.get("substitution_strategies", []):
            lines.append(f"- ↳ 替代：{s}")
    cap = feas["capability_feasibility"]
    lines += ["", "## 能力可实现性",
              f"- 需要：{', '.join(cap.get('required_capabilities', []))}",
              f"- 缺失：{', '.join(cap.get('missing_capabilities', [])) or '无'}",
              f"- 运行等级预估：{cap.get('runnable_level_estimate')}"]
    return "\n".join(lines) + "\n"


def write_research_artifacts(output_dir: Path, result: dict) -> None:
    """写 5 个 artifact。永不抛异常。"""
    try:
        output_dir = Path(output_dir)
        _write_json(output_dir / "demand-analysis.json", result["demand"])
        _write_json(output_dir / "miniapp-feasibility-report.json", result["feasibility"])
        _write_json(output_dir / "mvp-split-plan.json", result["split_plan"])
        _write_json(output_dir / "execution-decision.json", result["decision"])
        (output_dir / "demand-analysis.md").write_text(
            _build_markdown(result), encoding="utf-8-sig")
    except Exception:
        pass
