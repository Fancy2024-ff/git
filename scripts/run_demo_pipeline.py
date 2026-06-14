"""
Demo Pipeline - 完整 MVP 闭环演示
从 data/samples/apps.json 选择高需求 App → 全流程产出文件 → 打印人工待办

运行方式:
    python scripts/run_demo_pipeline.py

不依赖 LLM，使用本地规则和模板。
"""

import sys
import os
import json
import uuid
import time
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
REAL_INPUTS_DIR = DATA_DIR / "real_inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"


def p(msg: str):
    print(msg, flush=True)


def step_header(num: int, title: str, agent: str):
    p(f"\n{'─' * 60}")
    p(f"  Step {num} │ {title}")
    p(f"  Agent │ {agent}")
    p(f"{'─' * 60}")


def step_done(output_path: str, duration: float):
    p(f"  ✓ 完成 │ {duration:.1f}s │ {output_path}")


def step_fail(reason: str):
    p(f"  ✗ 失败 │ {reason}")


# Pipeline report state (written incrementally)
_pipeline_steps: list[dict] = []
_pipeline_output_dir: Path = Path(".")
_pipeline_job_id: str = ""
_report_meta: dict = {
    "started_at": None,
    "finished_at": None,
    "total_passed": None,
    "error": None,
    "mode": "demo",
    "data_source": "demo_rule_based",
}


def _flush_pipeline_report():
    """Write current pipeline-report.json to disk (report-level + per-step state)."""
    report = {
        "job_id": _pipeline_job_id,
        "mode": _report_meta["mode"],
        "data_source": _report_meta["data_source"],
        "started_at": _report_meta["started_at"],
        "finished_at": _report_meta["finished_at"],
        "total_passed": _report_meta["total_passed"],
        "error": _report_meta["error"],
        "steps": _pipeline_steps,
    }
    report_path = _pipeline_output_dir / "pipeline-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2))


def finalize_pipeline_report(total_passed=None, error: str = None):
    """Mark the report finished. Always leaves a terminal state (never 'running')."""
    _report_meta["finished_at"] = datetime.now().isoformat()
    _report_meta["total_passed"] = total_passed
    _report_meta["error"] = error
    # Any step still marked running at finalize time is forced to failed.
    for entry in _pipeline_steps:
        if entry.get("status") == "running":
            entry["status"] = "failed"
            entry["finished_at"] = entry["finished_at"] or datetime.now().isoformat()
            entry["error"] = entry.get("error") or (error or "pipeline aborted")
    _flush_pipeline_report()


def step_start(step_id: str, name: str, agent: str):
    """Record step started and flush to disk."""
    if _report_meta["started_at"] is None:
        _report_meta["started_at"] = datetime.now().isoformat()
    entry = {
        "step": step_id,
        "name": name,
        "agent": agent,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "duration_ms": 0,
        "artifact": None,
        "error": None,
    }
    _pipeline_steps.append(entry)
    _flush_pipeline_report()
    # Also print structured event for WS parsing
    p(json.dumps({"event": "step_started", "job_id": _pipeline_job_id, "step": step_id, "agent": agent, "message": name, "status": "running", "started_at": entry["started_at"]}))


def step_end(artifact: str = None, error: str = None, error_code: str = None,
             user_message: str = None, developer_message: str = None):
    """Record step finished and flush to disk. Failure carries structured error info."""
    if not _pipeline_steps:
        return
    entry = _pipeline_steps[-1]
    entry["finished_at"] = datetime.now().isoformat()
    started = datetime.fromisoformat(entry["started_at"])
    entry["duration_ms"] = int((datetime.now() - started).total_seconds() * 1000)
    entry["artifact"] = artifact
    is_failed = bool(error or error_code)
    entry["status"] = "failed" if is_failed else "passed"
    if is_failed:
        entry["error"] = error or user_message or "步骤执行失败"
        entry["error_code"] = error_code or "step_error"
        entry["user_message"] = user_message or error or "该步骤执行失败"
        entry["developer_message"] = developer_message or error or ""
    else:
        entry["error"] = None
    _flush_pipeline_report()
    # Print structured event
    evt = {
        "event": "step_finished", "job_id": _pipeline_job_id, "step": entry["step"],
        "agent": entry["agent"], "status": entry["status"], "artifact": artifact or "",
        "finished_at": entry["finished_at"], "duration_ms": entry["duration_ms"],
        "error": entry.get("error") or "",
    }
    if is_failed:
        evt["error_code"] = entry.get("error_code", "step_error")
        evt["user_message"] = entry.get("user_message", "")
        evt["developer_message"] = entry.get("developer_message", "")
    p(json.dumps(evt))


# ═══════════════════════════════════════════════════════════════
# AGENTS
# ═══════════════════════════════════════════════════════════════

def _normalize_app(app: dict) -> dict:
    """Fill defaultable fields so downstream steps never hit a KeyError.

    Mirrors the backend RealAppInput normalization: name_cn<-name,
    description_cn<-description, features_cn<-features, numeric defaults, and a
    guaranteed non-empty features_cn (so `features_cn[0]` is always safe).
    """
    app = dict(app or {})
    app["name"] = app.get("name", "") or "Unnamed App"
    app["name_cn"] = app.get("name_cn") or app["name"]
    app["category"] = app.get("category", "") or "Utilities"
    app["description"] = app.get("description") or app.get("description_cn") or ""
    app["description_cn"] = app.get("description_cn") or app.get("description") or ""
    features = app.get("features") or app.get("features_cn") or []
    features_cn = app.get("features_cn") or app.get("features") or []
    if not features_cn:
        features_cn = ["核心功能"]
    if not features:
        features = features_cn
    app["features"] = features
    app["features_cn"] = features_cn
    app["downloads"] = app.get("downloads", 0) or 0
    app["rating"] = app.get("rating", 0) or 0
    app["review_count"] = app.get("review_count", 0) or 0
    app["monetization"] = app.get("monetization") or "unknown"
    return app


def market_input_agent(mode: str = "demo") -> list[dict]:
    """读取 App 数据。demo 模式用样例，real 模式用真实导入数据。"""
    if mode == "real":
        apps_file = REAL_INPUTS_DIR / "apps.json"
        if not apps_file.exists():
            raise FileNotFoundError(
                f"data/real_inputs/apps.json not found\n"
                f"请先导入真实 App 数据，参考模板: data/real_inputs/apps.example.json"
            )
    else:
        apps_file = SAMPLES_DIR / "apps.json"
        if not apps_file.exists():
            raise FileNotFoundError(f"样本数据不存在: {apps_file}")
    apps = json.loads(apps_file.read_text(encoding="utf-8-sig"))
    if not isinstance(apps, list) or not apps:
        raise ValueError(f"{apps_file} 必须是非空的 JSON 数组")
    return [_normalize_app(a) for a in apps]


def demand_analysis_agent(app: dict) -> dict:
    """需求分析：多维度评估需求强度。"""
    downloads = app.get("downloads", 0)
    rating = app.get("rating", 0)
    review_count = app.get("review_count", 0)
    monetization = app.get("monetization", "")
    features = app.get("features", [])

    # 下载量评分 (0-30)
    if downloads > 5_000_000: dl_score = 30
    elif downloads > 2_000_000: dl_score = 25
    elif downloads > 500_000: dl_score = 18
    elif downloads > 100_000: dl_score = 12
    else: dl_score = 5

    # 评分评分 (0-20)
    rating_score = int(min(20, rating * 4.2))

    # 评论数评分 (0-15)
    if review_count > 10000: rev_score = 15
    elif review_count > 3000: rev_score = 12
    elif review_count > 500: rev_score = 8
    else: rev_score = 4

    # 变现验证 (0-15)
    if monetization in ("subscription", "freemium"): mon_score = 15
    elif monetization == "paid": mon_score = 12
    else: mon_score = 5

    # 功能丰富度 (0-10)
    feat_score = min(10, len(features) * 2)

    # 持续更新（本地无法判断，给默认分）
    update_score = 10

    demand_score = dl_score + rating_score + rev_score + mon_score + feat_score + update_score

    return {
        "app_name": app["name"],
        "app_name_cn": app["name_cn"],
        "demand_score": min(100, demand_score),
        "score_breakdown": {
            "downloads_score": dl_score,
            "rating_score": rating_score,
            "review_count_score": rev_score,
            "monetization_score": mon_score,
            "feature_richness_score": feat_score,
            "update_frequency_score": update_score,
        },
        "target_users": f"需要{app['name_cn'].replace('AI ', '')}功能的移动用户",
        "pain_point": "原生 App 需要下载安装，小程序可即用即走",
        "market_validation": f"{downloads:,} 次下载、{rating} 分评分证明需求真实存在",
        "conclusion": "需求已被市场验证" if demand_score >= 60 else "需求待进一步验证",
    }


def gap_check_agent(app: dict) -> dict:
    """覆盖检查：从 platform-registry 动态获取 active 平台，评估覆盖情况。"""
    downloads = app.get("downloads", 0)
    category = app.get("category", "").lower()

    # Load active platforms from registry
    registry_file = DATA_DIR / "platforms" / "platform-registry.json"
    active_platforms = []
    research_platforms = []
    if registry_file.exists():
        reg_list = json.loads(registry_file.read_text(encoding="utf-8-sig"))
        for p in reg_list:
            if p["status"] == "active":
                active_platforms.append(p)
            elif p["status"] == "research_needed":
                research_platforms.append(p)
    else:
        # Fallback if registry doesn't exist
        active_platforms = [{"id": "wechat"}, {"id": "alipay"}, {"id": "douyin"}, {"id": "telegram"}]

    # Coverage rule (local heuristic). Order matters: check the higher
    # threshold first so the 'strong' branch is reachable.
    def _coverage_level(plat_id: str) -> str:
        if plat_id == "wechat" and downloads > 10_000_000:
            return "strong"
        if plat_id == "wechat" and downloads > 5_000_000:
            return "weak"
        return "missing"

    # Product type matching
    def _fits_product(plat: dict) -> bool:
        fit_types = [t.lower() for t in plat.get("fit_product_types", [])]
        not_fit = [t.lower() for t in plat.get("not_fit_product_types", [])]
        # Check if category matches fit types
        if not fit_types:
            return True  # No restriction
        cat_map = {"productivity": "工具", "photography": "图片", "education": "教育", "utilities": "工具", "health & fitness": "本地生活"}
        mapped = cat_map.get(category, category)
        if any(mapped in t or t in mapped for t in not_fit):
            return False
        return True

    platforms_checked = []
    missing_platforms = []
    recommended = []

    for plat in active_platforms:
        plat_id = plat["id"]
        level = _coverage_level(plat_id)
        fits = _fits_product(plat)

        platforms_checked.append({
            "platform": plat_id,
            "name_cn": plat.get("name_cn", plat_id),
            "coverage_level": level,
            "product_fit": fits,
            "competitors": [],
            "evidence": [],
            "notes": "" if level == "missing" else "本地规则推断，待接入真实搜索",
        })

        if level in ("missing", "weak") and fits:
            missing_platforms.append(plat_id)
            recommended.append(plat_id)

    # Gap score
    gap_score = len(missing_platforms) / max(len(active_platforms), 1) * 100

    return {
        "app_name": app["name"],
        "platforms_checked": platforms_checked,
        "missing_platforms": missing_platforms,
        "research_platforms": [p["id"] for p in research_platforms],
        "gap_score": round(gap_score, 1),
        "gap_summary": f"{len(missing_platforms)} 个 active 平台缺失或覆盖薄弱（共检查 {len(active_platforms)} 个）",
        "recommended_platforms": recommended[:5],  # Top 5
        "opportunity_level": "高" if len(missing_platforms) >= 4 else "中" if len(missing_platforms) >= 2 else "低",
    }


def opportunity_score_agent(app: dict, analysis: dict, gap: dict) -> dict:
    """机会评分：5 维度综合评估。"""
    features = app.get("features", [])
    features_cn = app.get("features_cn", [])

    # 1. 需求强度 demand_score (from analysis)
    demand_score = analysis["demand_score"]

    # 2. 小程序缺口 miniapp_gap_score (from gap check)
    miniapp_gap_score = gap["gap_score"]

    # 3. 小程序适配度 miniapp_fit_score
    # 轻工具 +20, 短流程 +20, 适合分享 +20, 不依赖原生能力 +20, 文本为主 +20
    fit_score = 0
    complex_kw = ["camera", "ar", "video", "real-time", "3d", "hardware"]
    is_complex = any(kw in " ".join(features).lower() for kw in complex_kw)
    fit_score += 0 if is_complex else 25  # 不依赖复杂原生能力
    fit_score += 25 if len(features) <= 5 else 15  # 短流程
    fit_score += 25  # 轻工具（默认 AI 工具适合）
    fit_score += 25 if app.get("category") in ("Productivity", "Education", "Utilities") else 15  # 适合分享
    miniapp_fit_score = min(100, fit_score)

    # 4. 实现难度 implementation_score (高分=容易实现)
    page_count = min(6, len(features_cn) + 1)
    needs_payment = app.get("monetization") in ("freemium", "subscription")
    impl_score = 100
    impl_score -= page_count * 8  # 页面越多越难
    impl_score -= 15 if needs_payment else 0  # 需要支付
    impl_score -= 20 if is_complex else 0
    implementation_score = max(20, impl_score)

    # 5. 风险 risk_score (高分=低风险=好)
    risk_score = 85  # 默认低风险
    risk_kw = ["health", "medical", "finance", "gambling", "dating", "children"]
    if any(kw in app.get("category", "").lower() or kw in app.get("description", "").lower() for kw in risk_kw):
        risk_score = 45
    if "Health" in app.get("category", ""):
        risk_score = 50

    # 综合评分
    weights = {"demand": 0.25, "gap": 0.25, "fit": 0.20, "impl": 0.15, "risk": 0.15}
    total_score = round(
        demand_score * weights["demand"]
        + miniapp_gap_score * weights["gap"]
        + miniapp_fit_score * weights["fit"]
        + implementation_score * weights["impl"]
        + risk_score * weights["risk"],
        1,
    )

    # 推荐
    if total_score >= 70:
        recommendation = "立即执行"
        next_action = "进入 PRD 生成阶段"
    elif total_score >= 50:
        recommendation = "值得尝试"
        next_action = "建议进一步人工确认后执行"
    else:
        recommendation = "暂缓"
        next_action = "风险或难度过高，建议换目标"

    reasons = []
    if demand_score >= 70: reasons.append(f"需求强度高（{demand_score}）")
    if miniapp_gap_score >= 70: reasons.append(f"小程序缺口大（{miniapp_gap_score}）")
    if miniapp_fit_score >= 70: reasons.append(f"适配度高（{miniapp_fit_score}）")
    if implementation_score >= 60: reasons.append(f"实现难度可控（{implementation_score}）")

    reject_reasons = []
    if risk_score < 60: reject_reasons.append(f"风险偏高（{risk_score}）")
    if implementation_score < 40: reject_reasons.append(f"实现难度过大（{implementation_score}）")
    if miniapp_fit_score < 50: reject_reasons.append(f"小程序适配度低（{miniapp_fit_score}）")

    return {
        "app_name": app["name"],
        "app_name_cn": app["name_cn"],
        "demand_score": demand_score,
        "demand_evidence": [
            f"下载量 {app.get('downloads', 0):,}",
            f"评分 {app.get('rating', 0)}/5",
            f"变现模式: {app.get('monetization', 'unknown')}",
        ],
        "miniapp_gap_score": miniapp_gap_score,
        "gap_evidence": [
            f"检查 {len(gap.get('platforms_checked', []))} 个平台",
            f"缺失/薄弱: {', '.join(gap.get('missing_platforms', []))}",
        ],
        "miniapp_fit_score": miniapp_fit_score,
        "fit_evidence": [
            "轻工具类" if not is_complex else "含复杂原生能力",
            f"功能数: {len(features)}",
            f"品类: {app.get('category', '')}",
        ],
        "implementation_score": implementation_score,
        "impl_evidence": [
            f"预计 {page_count} 个页面",
            "需要支付能力" if needs_payment else "无支付依赖",
        ],
        "risk_score": risk_score,
        "risk_evidence": [
            "无高风险品类" if risk_score >= 70 else "涉及敏感品类",
        ],
        "total_score": total_score,
        "opportunity_score": total_score,
        "recommendation": recommendation,
        "reasons": reasons,
        "reject_reasons": reject_reasons,
        "next_action": next_action,
        "target_platforms": gap["recommended_platforms"],
        "estimated_dev_days": max(3, page_count * 2),
        "data_source": "demo_rule_based",
    }


def prd_agent(app: dict, opportunity: dict) -> tuple[str, dict]:
    """PRD Agent：生成产品需求文档（Markdown + JSON）。"""
    features_md = "\n".join([f"- {f}" for f in app["features_cn"]])
    platforms_str = "、".join(opportunity["target_platforms"])

    prd_md = f"""# {app['name_cn']} 小程序 - 产品需求文档

## 产品概述

**产品名称**：{app['name_cn']}
**英文名**：{app['name']}
**产品形态**：小程序
**目标平台**：{platforms_str}
**机会评分**：{opportunity['opportunity_score']}/100

## 产品定位

将 {app['name']} 的核心功能以小程序形态提供给用户，实现即用即走、无需下载安装的轻量体验。

## 目标用户

{app['description_cn']}的目标人群，偏好在微信/支付宝/抖音生态内完成操作，不愿额外下载 App。

## 核心功能

{features_md}

## MVP 范围

首版聚焦以下功能：
1. {app['features_cn'][0]}（核心功能）
2. {app['features_cn'][1] if len(app['features_cn']) > 1 else '基础展示'}（辅助功能）
3. 用户输入表单
4. 结果展示页面
5. 历史记录（本地存储）

## 页面结构

- **首页** index：功能入口、快捷操作
- **表单页** form：用户输入核心信息
- **结果页** result：AI 处理结果展示、复制/分享
- **我的** profile：历史记录、设置

## 技术方案

- 框架：uni-app（跨端兼容微信/支付宝/抖音）
- 语言：Vue 3 + TypeScript
- 状态管理：Pinia
- API：RESTful，后端独立部署
- 存储：本地 Storage + 云端同步（Pro）

## 变现策略

- 免费版：每日 {3} 次使用额度
- Pro 版：¥{12}/月，无限使用
- 支付方式：微信支付 / 支付宝

## 开发周期

预计 {opportunity['estimated_dev_days']} 天完成 MVP。

## 风险评估

- 平台审核：需确保内容合规，不涉及敏感词
- 包大小：控制在 2MB 以内（微信主包限制）
- AI 依赖：后端 API 需保证 P95 < 2s 响应
"""

    prd_json = {
        "app_name": app["name"],
        "app_name_cn": app["name_cn"],
        "product_type": "miniapp",
        "target_platforms": opportunity["target_platforms"],
        "opportunity_score": opportunity["opportunity_score"],
        "core_features": app["features_cn"],
        "mvp_features": app["features_cn"][:2] + ["用户输入表单", "结果展示", "历史记录"],
        "pages": [
            {"path": "pages/index/index", "title": "首页", "type": "navigation"},
            {"path": "pages/form/form", "title": "表单", "type": "input"},
            {"path": "pages/result/result", "title": "结果", "type": "display"},
            {"path": "pages/profile/profile", "title": "我的", "type": "navigation"},
        ],
        "tech_stack": {
            "framework": "uni-app",
            "language": "Vue 3 + TypeScript",
            "state": "Pinia",
            "api": "RESTful",
        },
        "monetization": {"model": "freemium", "free_quota": 3, "pro_price": 12},
        "timeline_days": opportunity["estimated_dev_days"],
    }

    return prd_md, prd_json


def codegen_agent(app: dict, prd_json: dict, output_dir: Path) -> tuple[Path, dict]:
    """代码生成 Agent：从 generator/templates 复制基础骨架，再定制化。"""
    import shutil

    miniapp_dir = output_dir / "miniapp"
    templates_dir = PROJECT_ROOT / "generator" / "src" / "templates"
    base_template = templates_dir / "base"

    # Track generation source
    gen_source = {
        "source": "generator_templates",
        "template": "base",
        "fallback_used": False,
        "generated_files_count": 0,
    }

    # Primary: copy from generator/src/templates/base
    if base_template.exists() and (base_template / "package.json").exists():
        shutil.copytree(str(base_template), str(miniapp_dir), dirs_exist_ok=True)
        gen_source["source"] = "generator_templates"
        gen_source["fallback_used"] = False
    else:
        # Fallback: create dirs manually
        gen_source["source"] = "inline_fallback"
        gen_source["fallback_used"] = True

    # Ensure all dirs exist
    src_dir = miniapp_dir / "src"
    pages_dir = src_dir / "pages"
    utils_dir = src_dir / "utils"
    docs_dir = miniapp_dir / "docs"
    for d in [pages_dir / "index", pages_dir / "form", pages_dir / "result", pages_dir / "profile", utils_dir, docs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy ai-tool template pages if available
    ai_tool_template = templates_dir / "ai-tool"
    if ai_tool_template.exists():
        for sub in ai_tool_template.rglob("*"):
            if sub.is_file():
                dest = miniapp_dir / sub.relative_to(ai_tool_template)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(sub), str(dest))
        gen_source["template"] = "base/ai-tool"

    app_name = app["name_cn"]
    app_name_en = app["name"].lower().replace(" ", "-")

    # package.json
    _write(miniapp_dir / "package.json", json.dumps({
        "name": app_name_en,
        "version": "1.0.0",
        "description": app["description_cn"],
        "scripts": {"dev:mp-weixin": "uni -p mp-weixin", "build:mp-weixin": "uni build -p mp-weixin", "build:mp-alipay": "uni build -p mp-alipay"},
        "dependencies": {"vue": "^3.5.13", "pinia": "^2.1.7"},
        "devDependencies": {
            "@dcloudio/uni-app": "3.0.0-5000720260410001",
            "@dcloudio/uni-components": "3.0.0-5000720260410001",
            "@dcloudio/uni-h5": "3.0.0-5000720260410001",
            "@dcloudio/uni-mp-weixin": "3.0.0-5000720260410001",
            "@dcloudio/uni-mp-alipay": "3.0.0-5000720260410001",
            "@dcloudio/uni-mp-toutiao": "3.0.0-5000720260410001",
            "@dcloudio/vite-plugin-uni": "3.0.0-5000720260410001",
            "typescript": "^5.4.0",
            "vite": "^5.2.8",
        }
    }, ensure_ascii=False, indent=2))

    # README.md
    _write(miniapp_dir / "README.md", f"""# {app_name}

{app['description_cn']}

## 技术栈
- uni-app + Vue 3 + TypeScript
- 目标平台：{'、'.join(prd_json['target_platforms'])}

## 开发
```bash
npm install
npm run dev
```

## 构建
```bash
npm run build:mp-weixin
npm run build:mp-alipay
```
""")

    # manifest.json (in src/ for uni-app CLI)
    _write(src_dir / "manifest.json", json.dumps({
        "name": app_name,
        "appid": "",
        "description": app["description_cn"],
        "versionName": "1.0.0",
        "versionCode": "100",
        "mp-weixin": {"appid": "", "setting": {"urlCheck": False}, "usingComponents": True},
        "mp-alipay": {"appid": ""},
        "mp-toutiao": {"appid": ""},
    }, ensure_ascii=False, indent=2))

    # pages.json (in src/ for uni-app CLI) — MERGE with template if exists
    pages_json_path = src_dir / "pages.json"
    template_pages = []
    template_global = {}
    template_tabbar = {}
    if pages_json_path.exists():
        try:
            existing = json.loads(pages_json_path.read_text(encoding="utf-8"))
            template_pages = existing.get("pages", [])
            template_global = existing.get("globalStyle", {})
            template_tabbar = existing.get("tabBar", {})
        except Exception:
            pass

    prd_pages = [
        {"path": "pages/index/index", "style": {"navigationBarTitleText": "首页"}},
        {"path": "pages/form/form", "style": {"navigationBarTitleText": app["features_cn"][0]}},
        {"path": "pages/result/result", "style": {"navigationBarTitleText": "结果"}},
        {"path": "pages/profile/profile", "style": {"navigationBarTitleText": "我的"}},
    ]
    existing_paths = {p["path"] for p in template_pages}
    merged_pages = template_pages + [p for p in prd_pages if p["path"] not in existing_paths]

    if not any("index" in p["path"] for p in merged_pages):
        merged_pages.insert(0, {"path": "pages/index/index", "style": {"navigationBarTitleText": "首页"}})

    merged_config = {
        "pages": merged_pages,
        "globalStyle": template_global if template_global.get("navigationBarTextStyle") else {"navigationBarTextStyle": "black", "navigationBarBackgroundColor": "#ffffff", "backgroundColor": "#f5f5f5"},
        "tabBar": template_tabbar if template_tabbar.get("list") else {"color": "#999", "selectedColor": "#333", "list": [
            {"pagePath": "pages/index/index", "text": "首页"},
            {"pagePath": "pages/profile/profile", "text": "我的"},
        ]},
    }
    _write(pages_json_path, json.dumps(merged_config, ensure_ascii=False, indent=2))

    # Pages
    _write(pages_dir / "index" / "index.vue", f"""<template>
  <view class="container">
    <view class="hero">
      <text class="title">{app_name}</text>
      <text class="subtitle">{app['description_cn'][:40]}</text>
    </view>
    <view class="actions">
      <button class="btn-primary" @click="goToForm">开始使用</button>
    </view>
    <view class="features">
      <view class="feature-item" v-for="(f, i) in features" :key="i">
        <text class="feature-text">{{{{ f }}}}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const features = {json.dumps(app['features_cn'], ensure_ascii=False)}

function goToForm() {{
  uni.navigateTo({{ url: '/pages/form/form' }})
}}
</script>

<style scoped>
.container {{ padding: 40rpx; min-height: 100vh; background: #f8f8f8; }}
.hero {{ text-align: center; padding: 80rpx 0 40rpx; }}
.title {{ font-size: 44rpx; font-weight: bold; color: #1d1d1f; display: block; }}
.subtitle {{ font-size: 28rpx; color: #6e6e73; margin-top: 12rpx; display: block; }}
.actions {{ text-align: center; margin: 40rpx 0; }}
.btn-primary {{ background: #0071e3; color: #fff; border: none; border-radius: 12rpx; padding: 24rpx 60rpx; font-size: 30rpx; }}
.features {{ padding: 20rpx; }}
.feature-item {{ background: #fff; padding: 24rpx; margin-bottom: 16rpx; border-radius: 12rpx; }}
.feature-text {{ font-size: 28rpx; color: #333; }}
</style>
""")

    _write(pages_dir / "form" / "form.vue", f"""<template>
  <view class="container">
    <view class="form-card">
      <text class="form-title">{app['features_cn'][0]}</text>
      <textarea class="input-area" v-model="inputText" placeholder="请输入内容..." />
      <button class="btn-submit" @click="handleSubmit" :loading="loading">开始处理</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'

const inputText = ref('')
const loading = ref(false)

async function handleSubmit() {{
  if (!inputText.value.trim()) {{
    uni.showToast({{ title: '请输入内容', icon: 'none' }})
    return
  }}
  loading.value = true
  setTimeout(() => {{
    loading.value = false
    uni.navigateTo({{ url: '/pages/result/result?input=' + encodeURIComponent(inputText.value) }})
  }}, 1500)
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f7; }}
.form-card {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.form-title {{ font-size: 34rpx; font-weight: 600; color: #1d1d1f; margin-bottom: 24rpx; display: block; }}
.input-area {{ width: 100%; min-height: 240rpx; padding: 20rpx; border: 1rpx solid #e8e8ed; border-radius: 12rpx; font-size: 28rpx; }}
.btn-submit {{ margin-top: 32rpx; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }}
</style>
""")

    _write(pages_dir / "result" / "result.vue", """<template>
  <view class="container">
    <view class="result-card">
      <text class="result-title">处理结果</text>
      <view class="result-content">
        <text class="result-text">{{ resultText }}</text>
      </view>
      <view class="result-actions">
        <button class="btn-copy" @click="copyResult">复制结果</button>
        <button class="btn-back" @click="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const resultText = ref('AI 处理结果将在这里展示。连接后端 API 后将返回真实结果。')

onLoad((options: any) => {
  if (options?.input) {
    resultText.value = `已处理输入内容（${decodeURIComponent(options.input).length} 字）\\n\\nAI 分析结果将在后端 API 接入后展示。`
  }
})

function copyResult() {
  uni.setClipboardData({ data: resultText.value })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.result-card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.result-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; margin-bottom: 24rpx; display: block; }
.result-content { background: #f5f5f7; border-radius: 12rpx; padding: 24rpx; min-height: 200rpx; margin-bottom: 24rpx; }
.result-text { font-size: 28rpx; color: #333; white-space: pre-wrap; }
.result-actions { display: flex; gap: 16rpx; }
.btn-copy { flex: 1; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-back { flex: 1; background: #f5f5f7; color: #333; border: none; border-radius: 12rpx; font-size: 28rpx; }
</style>
""")

    _write(pages_dir / "profile" / "profile.vue", """<template>
  <view class="container">
    <view class="profile-header">
      <view class="avatar">
        <text class="avatar-text">U</text>
      </view>
      <text class="username">未登录</text>
      <button class="btn-login" @click="login">微信登录</button>
    </view>
    <view class="menu-list">
      <view class="menu-item"><text>历史记录</text><text class="arrow">→</text></view>
      <view class="menu-item"><text>使用额度</text><text class="quota">3/3 次</text></view>
      <view class="menu-item"><text>升级 Pro</text><text class="arrow">→</text></view>
      <view class="menu-item"><text>意见反馈</text><text class="arrow">→</text></view>
      <view class="menu-item"><text>关于</text><text class="arrow">→</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
function login() {
  uni.showToast({ title: '登录功能开发中', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.profile-header { background: #fff; border-radius: 16rpx; padding: 40rpx; text-align: center; margin-bottom: 24rpx; }
.avatar { width: 100rpx; height: 100rpx; background: #e8e8ed; border-radius: 50%; margin: 0 auto 16rpx; display: flex; align-items: center; justify-content: center; }
.avatar-text { font-size: 36rpx; color: #6e6e73; }
.username { font-size: 30rpx; color: #1d1d1f; display: block; margin-bottom: 16rpx; }
.btn-login { background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; padding: 16rpx 40rpx; }
.menu-list { background: #fff; border-radius: 16rpx; overflow: hidden; }
.menu-item { display: flex; justify-content: space-between; padding: 28rpx 32rpx; border-bottom: 1rpx solid #f0f0f0; font-size: 28rpx; color: #333; }
.menu-item:last-child { border-bottom: none; }
.arrow { color: #aeaeb2; }
.quota { color: #0071e3; font-size: 26rpx; }
</style>
""")

    # utils/request.ts
    _write(utils_dir / "request.ts", """const BASE_URL = ''

export interface RequestOptions {
  showLoading?: boolean
}

export function request<T = any>(
  url: string,
  method: 'GET' | 'POST' = 'GET',
  data?: any,
  options: RequestOptions = {}
): Promise<T> {
  const { showLoading = true } = options

  if (showLoading) uni.showLoading({ title: '加载中...' })

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          uni.showToast({ title: '请求失败', icon: 'none' })
          reject(new Error(`HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
      complete: () => { if (showLoading) uni.hideLoading() },
    })
  })
}
""")

    # vite.config.ts
    _write(miniapp_dir / "vite.config.ts", """import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
})
""")

    # tsconfig.json
    _write(miniapp_dir / "tsconfig.json", json.dumps({
        "compilerOptions": {
            "target": "ESNext",
            "module": "ESNext",
            "moduleResolution": "bundler",
            "strict": True,
            "jsx": "preserve",
            "sourceMap": True,
            "lib": ["ESNext", "DOM"],
            "types": ["@dcloudio/types"],
            "paths": {"@/*": ["./src/*"]},
        },
        "include": ["src/**/*.ts", "src/**/*.vue"],
    }, indent=2))

    # index.html
    _write(miniapp_dir / "index.html", """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title></title>
    <!--app-config-->
  </head>
  <body>
    <div id="app"><!--app-html--></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
""")

    # src/main.ts
    _write(src_dir / "main.ts", """import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

export function createApp() {
  const app = createSSRApp(App)
  app.use(createPinia())
  return { app }
}
""")

    # src/App.vue
    _write(src_dir / "App.vue", """<script setup lang="ts">
</script>

<template>
  <view>
    <page />
  </view>
</template>

<style>
page {
  background: #f5f5f7;
}
</style>
""")

    # docs
    _write(docs_dir / "privacy-policy.md", f"""# {app_name} 隐私政策

更新日期：{datetime.now().strftime('%Y年%m月%d日')}

## 信息收集

本小程序收集以下信息：
- 您主动输入的文本内容（仅用于 AI 处理，处理后不保留）
- 微信授权的昵称和头像（用于个人中心展示）
- 设备信息和操作日志（用于故障排查）

## 信息使用

收集的信息仅用于：
- 提供 AI 处理服务
- 改善产品体验
- 安全保障

## 信息存储

- 用户输入内容在处理完成后立即删除，不做存储
- 账户信息加密存储于中国大陆服务器
- 数据保留期限：账户注销后 30 天内彻底删除

## 第三方共享

我们不会将您的个人信息出售或提供给第三方。

## 用户权利

您有权：
- 查看、更正个人信息
- 删除账户及所有数据
- 撤回授权

## 联系我们

如有疑问，请通过小程序内「意见反馈」联系我们。
""")

    _write(docs_dir / "user-agreement.md", f"""# {app_name} 用户服务协议

更新日期：{datetime.now().strftime('%Y年%m月%d日')}

## 服务说明

{app_name}是一款 AI 辅助工具类小程序，提供{app['description_cn'][:20]}等功能。

## 使用规范

用户不得：
- 输入违法违规内容
- 利用本服务生成虚假信息
- 对服务进行逆向工程
- 超出合理使用频率

## 免责声明

- AI 生成内容仅供参考，不构成专业建议
- 因网络原因导致的服务中断，不承担责任
- 用户对自身输入和使用行为负责

## 知识产权

- 本小程序的代码和设计归开发者所有
- 用户通过本服务生成的内容归用户所有

## 协议变更

我们有权对本协议进行修改，修改后将通过小程序内通知。
""")

    _write(docs_dir / "publish-guide.md", f"""# {app_name} 上架操作指南

## 微信小程序上架步骤

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入「开发管理」→「开发设置」获取 AppID
3. 打开微信开发者工具，导入本项目
4. 填写 AppID 至 manifest.json 的 mp-weixin.appid
5. 点击「上传」将代码上传至管理后台
6. 回到微信公众平台，进入「版本管理」
7. 将上传的代码提交审核
8. 审核通过后点击「发布」

## 支付宝小程序上架步骤

1. 登录 [支付宝开放平台](https://open.alipay.com)
2. 创建小程序应用，获取 AppID
3. 使用支付宝小程序开发者工具上传代码
4. 提交审核

## 抖音小程序上架步骤

1. 登录 [抖音开放平台](https://developer.open-douyin.com)
2. 创建小程序，获取 AppID
3. 使用抖音开发者工具上传
4. 提交审核
""")

    gen_source["generated_files_count"] = len([f for f in miniapp_dir.rglob("*") if f.is_file()])
    return miniapp_dir, gen_source


def qa_check_agent(miniapp_dir: Path, output_dir: Path) -> dict:
    """质量检查 Agent：验证项目完整性、编码、路径、内容，并自动执行 npm install + build。"""
    import shutil
    import subprocess as sp

    GARBLED_PATTERNS = ["鈹", "鍥", "绋", "鐢", "涓", "鍙", "杩", "閰", "椤"]

    issues = []

    # --- 1. 文件存在性检查 ---
    required_files = [
        "package.json", "README.md", "vite.config.ts", "tsconfig.json", "index.html",
        "src/manifest.json", "src/pages.json", "src/main.ts", "src/App.vue",
        "src/pages/index/index.vue", "src/pages/form/form.vue",
        "src/pages/result/result.vue", "src/pages/profile/profile.vue",
        "src/utils/request.ts",
        "docs/privacy-policy.md", "docs/user-agreement.md", "docs/publish-guide.md",
    ]
    file_checks = []
    files_pass = True
    for f in required_files:
        exists = (miniapp_dir / f).exists()
        file_checks.append({"file": f, "exists": exists})
        if not exists:
            files_pass = False
            issues.append(f"文件缺失: {f}")

    # --- 2. 中文乱码检查 ---
    encoding_pass = True
    garbled_files = []
    all_text_files = [f for f in miniapp_dir.rglob("*") if f.is_file() and f.suffix in (".json", ".md", ".vue", ".ts") and "node_modules" not in str(f)]
    output_text_files = [f for f in output_dir.iterdir() if f.is_file() and f.suffix in (".json", ".md")]
    for f in list(all_text_files) + list(output_text_files):
        try:
            content = f.read_text(encoding="utf-8-sig")
            for pattern in GARBLED_PATTERNS:
                if pattern in content:
                    encoding_pass = False
                    garbled_files.append(str(f.name))
                    issues.append(f"乱码检测: {f.name} 包含 '{pattern}'")
                    break
        except Exception:
            pass

    # --- 3. human-actions.md 路径检查 ---
    path_pass = True
    human_actions_file = output_dir / "human-actions.md"
    if human_actions_file.exists():
        ha_content = human_actions_file.read_text(encoding="utf-8-sig")
        expected_path = str(output_dir / "generated" / "miniapp").replace("\\", "/")
        expected_path_win = str(output_dir / "generated" / "miniapp")
        if expected_path not in ha_content and expected_path_win not in ha_content:
            path_pass = False
            issues.append("human-actions.md 中小程序导入路径不正确")
    else:
        path_pass = False
        issues.append("human-actions.md 不存在")

    # --- 4. listing-materials.md 必要字段检查 ---
    listing_pass = True
    listing_file = output_dir / "listing-materials.md"
    required_listing_fields = ["中文名", "英文名", "一句话简介", "服务类目", "关键词", "隐私政策", "审核备注"]
    if listing_file.exists():
        listing_content = listing_file.read_text(encoding="utf-8-sig")
        for field in required_listing_fields:
            if field not in listing_content:
                listing_pass = False
                issues.append(f"listing-materials.md 缺少字段: {field}")
    else:
        listing_pass = False
        issues.append("listing-materials.md 不存在")

    # --- 5. README 必要步骤检查 ---
    readme_pass = True
    readme_file = miniapp_dir / "README.md"
    if readme_file.exists():
        readme_content = readme_file.read_text(encoding="utf-8-sig")
        for keyword in ["npm install", "npm run"]:
            if keyword not in readme_content:
                readme_pass = False
                issues.append(f"README.md 缺少: {keyword}")
    else:
        readme_pass = False
        issues.append("README.md 不存在")

    # --- 6. package.json build 脚本检查 ---
    build_scripts_pass = True
    pkg_file = miniapp_dir / "package.json"
    if pkg_file.exists():
        try:
            pkg = json.loads(pkg_file.read_text(encoding="utf-8-sig"))
            scripts = pkg.get("scripts", {})
            if "build:mp-weixin" not in scripts and "build" not in scripts:
                build_scripts_pass = False
                issues.append("package.json 缺少 build 脚本")
        except Exception:
            build_scripts_pass = False
            issues.append("package.json 无法解析")
    else:
        build_scripts_pass = False

    # --- 7. JSON 合法性检查 ---
    json_valid = True
    for json_file in ["package.json", "src/manifest.json", "src/pages.json"]:
        try:
            json.loads((miniapp_dir / json_file).read_text(encoding="utf-8-sig"))
        except Exception:
            json_valid = False
            issues.append(f"JSON 格式无效: {json_file}")

    # --- 8. 包大小检查（不含 node_modules） ---
    src_files = [f for f in miniapp_dir.rglob("*") if f.is_file() and "node_modules" not in str(f) and "dist" not in str(f)]
    total_size = sum(f.stat().st_size for f in src_files)
    size_check = total_size < 2 * 1024 * 1024

    # --- 9. 自动执行 npm install ---
    install_verified = False
    install_passed = False
    install_command = "npm install"
    install_duration_ms = 0
    install_error = ""

    npm_path = shutil.which("npm")
    install_timeout = int(os.environ.get("QA_INSTALL_TIMEOUT", "180"))
    build_timeout = int(os.environ.get("QA_BUILD_TIMEOUT", "180"))
    if not npm_path:
        issues.append("npm 不可用，无法执行 install 和 build")
        install_error = "npm not found in PATH"
    else:
        install_verified = True
        t_start = time.time()
        try:
            result = sp.run(
                [npm_path, "install"],
                cwd=str(miniapp_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=install_timeout,
            )
            install_duration_ms = int((time.time() - t_start) * 1000)
            if result.returncode == 0:
                install_passed = True
            else:
                install_passed = False
                install_error = (result.stderr or result.stdout)[-500:]
                issues.append(f"npm install 失败 (exit {result.returncode}): {install_error[:200]}")
        except sp.TimeoutExpired:
            install_duration_ms = install_timeout * 1000
            install_error = f"npm install timed out ({install_timeout}s)"
            issues.append(install_error)
        except Exception as e:
            install_error = str(e)
            issues.append(f"npm install 异常: {e}")

    # --- 10. 自动执行 npm run build:mp-weixin ---
    build_verified = False
    build_passed = False
    build_command = "npm run build:mp-weixin"
    build_duration_ms = 0
    build_output_summary = ""
    build_error_summary = ""
    dist_path = ""

    if install_passed and npm_path:
        build_verified = True
        dist_dir = miniapp_dir / "dist" / "build" / "mp-weixin"
        t_start = time.time()
        try:
            result = sp.run(
                [npm_path, "run", "build:mp-weixin"],
                cwd=str(miniapp_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=build_timeout,
            )
            build_duration_ms = int((time.time() - t_start) * 1000)
            output_text = result.stdout + result.stderr
            build_output_summary = output_text[-500:]
            # Success is determined by exit code + real build artifacts,
            # NOT by matching log text like "Build complete".
            key_files = [dist_dir / "app.json", dist_dir / "app.js", dist_dir / "app.wxss"]
            has_key_files = any(f.exists() for f in key_files) or (
                dist_dir.exists() and any(dist_dir.iterdir())
            )
            if result.returncode == 0 and dist_dir.exists() and has_key_files:
                build_passed = True
                dist_path = str(dist_dir)
            else:
                build_passed = False
                build_error_summary = output_text[-500:]
                issues.append(f"build 失败 (exit {result.returncode}): {build_error_summary[:200]}")
        except sp.TimeoutExpired:
            build_duration_ms = build_timeout * 1000
            build_error_summary = f"npm run build:mp-weixin timed out ({build_timeout}s)"
            issues.append(build_error_summary)
        except Exception as e:
            build_error_summary = str(e)
            issues.append(f"build 异常: {e}")

    # --- 11. 验证 dist 目录存在 ---
    dist_exists = Path(dist_path).exists() if dist_path else False
    if build_passed and not dist_exists:
        build_passed = False
        issues.append("build 报告成功但 dist 目录不存在")

    # --- 综合判定 ---
    passed = all([
        files_pass,
        encoding_pass,
        path_pass,
        listing_pass,
        readme_pass,
        build_scripts_pass,
        json_valid,
        size_check,
        install_passed,
        build_verified,
        build_passed,
        dist_exists,
    ])

    return {
        "passed": passed,
        "total_files": len(src_files),
        "total_size_bytes": total_size,
        "total_size_readable": f"{total_size / 1024:.1f} KB",
        "checks": {
            "files_exist": files_pass,
            "encoding_passed": encoding_pass,
            "path_passed": path_pass,
            "listing_fields_passed": listing_pass,
            "readme_passed": readme_pass,
            "build_scripts_passed": build_scripts_pass,
            "json_valid": json_valid,
            "size_within_limit": size_check,
            "install_verified": install_verified,
            "install_passed": install_passed,
            "install_command": install_command,
            "install_duration_ms": install_duration_ms,
            "build_verified": build_verified,
            "build_passed": build_passed,
            "build_command": build_command,
            "build_duration_ms": build_duration_ms,
            "build_output_summary": build_output_summary,
            "build_error_summary": build_error_summary,
            "dist_path": dist_path,
            "dist_exists": dist_exists,
        },
        "file_checks": file_checks,
        "garbled_files": garbled_files,
        "issues": issues,
    }


def publish_materials_agent(app: dict, prd_json: dict) -> tuple[str, dict]:
    """上架材料 Agent：生成完整的上架所需文案和配置。"""
    platforms_str = "、".join(prd_json["target_platforms"])

    materials_json = {
        "app_name_cn": app["name_cn"],
        "app_name_en": app["name"],
        "one_liner": f"{app['name_cn']} - {app['features_cn'][0]}，即用即走",
        "description": app["description_cn"] + f"\n\n核心功能：\n" + "\n".join([f"• {f}" for f in app["features_cn"]]),
        "category_suggestion": f"工具 > {'效率' if app['category'] == 'Productivity' else '生活' if app['category'] == 'Health & Fitness' else '图片' if app['category'] == 'Photography' else '教育' if app['category'] == 'Education' else '其他'}",
        "keywords": app["features_cn"][:5],
        "version_note": "v1.0.0 首次发布：支持核心 AI 功能、用户输入、结果展示、历史记录。",
        "privacy_summary": "收集用户输入文本（处理后不保留）、微信授权昵称头像、设备信息。不收集位置、通讯录等敏感信息。",
        "user_agreement_summary": "AI 辅助工具，生成内容仅供参考。用户对输入内容负责。",
        "screenshot_copywriting": [
            f"{app['name_cn']} - 首页",
            f"核心功能 - {app['features_cn'][0]}",
            "AI 处理结果展示",
            "个人中心 & 历史记录",
        ],
        "review_notes": f"本小程序为 AI 工具类应用，提供{app['features_cn'][0]}功能。所有 AI 处理在服务端完成，不涉及敏感内容生成。已配置内容安全过滤。",
        "risk_warnings": [
            "AI 生成内容需做内容安全审核",
            "免费额度限制需在页面明确展示",
            "隐私政策需在首次使用前展示并获得同意",
        ],
    }

    materials_md = f"""# {app['name_cn']} 上架材料

## 基本信息

| 项目 | 内容 |
|------|------|
| 中文名 | {materials_json['app_name_cn']} |
| 英文名 | {materials_json['app_name_en']} |
| 一句话简介 | {materials_json['one_liner']} |
| 服务类目 | {materials_json['category_suggestion']} |
| 版本号 | 1.0.0 |

## 详细简介

{materials_json['description']}

## 关键词

{', '.join(materials_json['keywords'])}

## 版本说明

{materials_json['version_note']}

## 隐私政策摘要

{materials_json['privacy_summary']}

## 用户协议摘要

{materials_json['user_agreement_summary']}

## 截图文案

1. {materials_json['screenshot_copywriting'][0]}
2. {materials_json['screenshot_copywriting'][1]}
3. {materials_json['screenshot_copywriting'][2]}
4. {materials_json['screenshot_copywriting'][3]}

## 审核备注

{materials_json['review_notes']}

## 风险提示

{"".join([f'- {r}' + chr(10) for r in materials_json['risk_warnings']])}
"""

    return materials_md, materials_json


def generate_human_actions(app: dict, job_id: str, output_dir: Path) -> str:
    """生成人工操作指南。"""
    platforms_str = "、".join(["微信小程序", "支付宝小程序"])

    return f"""# 人工操作清单 - {app['name_cn']}

> Job ID: {job_id}
> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 你现在需要做什么

系统已自动完成：需求分析、覆盖检查、PRD 生成、代码生成、质量检查、上架材料准备。
以下步骤需要你手动操作：

---

### 步骤 1：登录微信公众平台

1. 打开浏览器访问 https://mp.weixin.qq.com
2. 使用管理员微信扫码登录
3. 如果还没有小程序账号，点击「前往注册」注册一个

---

### 步骤 2：创建或选择小程序

- 如果是新项目：左侧菜单 →「开发管理」→「开发设置」→ 复制 AppID
- 如果已有小程序：直接进入对应小程序后台

---

### 步骤 3：上传代码

1. 下载并安装「微信开发者工具」
2. 打开开发者工具，选择「导入项目」
3. 项目目录选择：
   ```
   {output_dir / 'generated' / 'miniapp'}
   ```
4. 填入 AppID（从公众平台复制）
5. 点击「上传」按钮，填写版本号 1.0.0

---

### 步骤 4：填写小程序资料

在微信公众平台填写以下信息：

- **小程序名称**：{app['name_cn']}
- **简介**：参考 `listing-materials.md` 中的一句话简介
- **服务类目**：参考 `listing-materials.json` 中的 category_suggestion
- **关键词**：参考 `listing-materials.json` 中的 keywords

---

### 步骤 5：上传截图

准备 4-5 张小程序截图（750×1334 或 1125×2436）：
1. 首页截图
2. 核心功能页截图
3. 结果展示页截图
4. 个人中心截图

截图文案参考 `listing-materials.md`。

---

### 步骤 6：配置隐私政策和用户协议

1. 在公众平台「设置」→「用户隐私保护指引」中填写
2. 内容参考：`docs/privacy-policy.md`
3. 用户协议参考：`docs/user-agreement.md`

---

### 步骤 7：提交审核

1. 回到「版本管理」页面
2. 在「开发版本」中找到刚上传的代码
3. 点击「提交审核」
4. 填写审核备注（参考 listing-materials.md 中的审核备注）
5. 确认提交

---

### 步骤 8：记录审核结果

审核通常 1-7 个工作日，结果出来后请：
- 如果通过：在公众平台点击「发布」
- 如果拒绝：记录拒绝原因，反馈至系统进行复盘迭代

---

## 文件清单

本次生成的所有文件位于：
```
{output_dir}
```

| 文件 | 用途 |
|------|------|
| candidate.json | 选中的候选 App 信息 |
| analysis.json | 需求分析报告 |
| gap-check.json | 小程序平台覆盖检查 |
| opportunity-report.json | 机会评分 |
| prd.md | 产品需求文档（可读版） |
| prd.json | 产品需求文档（结构化） |
| miniapp/ | 生成的小程序项目代码 |
| qa-report.json | 质量检查报告 |
| listing-materials.md | 上架材料（可读版） |
| listing-materials.json | 上架材料（结构化） |
| human-actions.md | 本文件 |

---

*如有疑问，请联系技术负责人。*
"""


def _platform_auth_status(plat: str) -> tuple[bool, list[str]]:
    """Return (configured, missing_fields) by reading data/platform-auth/<plat>.json."""
    required = {
        "wechat": ["appid", "private_key_path"],
        "alipay": ["appid"],
        "douyin": ["appid"],
    }.get(plat, ["appid"])
    cf = DATA_DIR / "platform-auth" / f"{plat}.json"
    if not cf.exists():
        return False, required[:]
    try:
        cfg = json.loads(cf.read_text(encoding="utf-8-sig"))
    except Exception:
        return False, required[:]
    missing = [f for f in required if not cfg.get(f)]
    return (len(missing) == 0), missing


def build_submission_readiness(best_app: dict, opportunity: dict, qa: dict,
                               output_dir: Path, mode: str) -> dict:
    """Honest answer to: can we submit for review TODAY?

    ready_to_submit is True only when there are zero blocking issues — which
    means: QA/build passed, dist exists, platform auth (AppID) configured,
    screenshots prepared, and real-device testing done.
    """
    qa_passed = bool(qa.get("passed"))
    dist_exists = bool(qa.get("checks", {}).get("dist_exists"))

    registry_file = DATA_DIR / "platforms" / "platform-registry.json"
    registry = {}
    if registry_file.exists():
        try:
            registry = {p["id"]: p for p in json.loads(registry_file.read_text(encoding="utf-8-sig"))}
        except Exception:
            registry = {}

    platform_readiness = []
    rejected_platforms = []
    any_configured = False

    for plat in opportunity["target_platforms"]:
        reg = registry.get(plat, {})
        status = reg.get("status", "unknown")
        if status in ("not_supported", "research_needed"):
            rejected_platforms.append({
                "platform": plat,
                "reason": reg.get("notes", "平台不支持") if status == "not_supported" else "待调研，暂不可提交",
            })
            continue

        configured, missing_fields = _platform_auth_status(plat)
        can_upload = configured and reg.get("automation_level", "manual") != "manual"
        any_configured = any_configured or configured

        plat_blocking = []
        if not configured:
            plat_blocking.append(f"未配置 {plat} 平台授权（缺: {', '.join(missing_fields) or 'AppID'}）")
        if not qa_passed:
            plat_blocking.append("QA/构建未通过")
        if not dist_exists:
            plat_blocking.append("构建产物缺失")

        platform_readiness.append({
            "platform": plat,
            "name_cn": reg.get("name_cn", plat),
            "name_en": reg.get("name_en", plat),
            "ready": status == "active" and configured and qa_passed and dist_exists,
            "configured": configured,
            "can_upload": can_upload,
            "missing_fields": missing_fields,
            "next_action": (
                "上传代码并提交审核" if (configured and qa_passed and dist_exists)
                else f"先解决: {'; '.join(plat_blocking)}"
            ),
            "submit_url": reg.get("submit_url", reg.get("developer_url", "")),
            "upload_path": str(output_dir / "generated" / "miniapp" / (reg.get("upload_target", "") or "dist/build/mp-weixin")),
            "automation_level": reg.get("automation_level", "manual"),
        })

    # Global blocking / warning issues
    blocking_issues = []
    if not qa_passed:
        blocking_issues.append("QA 未通过或构建失败，不能提交审核")
    if not dist_exists:
        blocking_issues.append("构建产物 dist/build/mp-weixin 缺失")
    if not any_configured:
        blocking_issues.append("尚未配置任何平台授权（缺 AppID/密钥）")
    # These are always required for a real submission and never auto-produced:
    blocking_issues.append("缺少真机测试截图，需人工准备")
    blocking_issues.append("未在目标平台真机测试")

    warning_issues = [
        "生成代码为 MVP 模板，建议人工 review 业务逻辑",
        "AI 处理结果为占位，需接入真实后端 API",
    ]

    human_actions = [
        "在对应平台后台创建小程序并获取 AppID",
        "将 AppID/密钥写入 data/platform-auth/<platform>.json",
        "用开发者工具导入 dist/build/mp-weixin 并真机预览",
        "准备 4-5 张截图（参考 listing-materials.md）",
        "提交审核并记录结果",
    ]

    return {
        "job_id": _pipeline_job_id,
        "app_name": best_app["name_cn"],
        "ready_to_submit": len(blocking_issues) == 0,
        # Back-compat alias for older dashboards; same value as ready_to_submit.
        "is_ready_to_submit": len(blocking_issues) == 0,
        "blocking_issues": blocking_issues,
        "warning_issues": warning_issues,
        "human_actions": human_actions,
        "qa_passed": qa_passed,
        "build_dist_exists": dist_exists,
        "target_platforms": [p["platform"] for p in platform_readiness],
        "rejected_platforms": rejected_platforms,
        "platform_readiness": platform_readiness,
        "next_action": (
            "可以提交审核" if len(blocking_issues) == 0
            else "当前不能提交审核，请先解决上方 blocking_issues"
        ),
        "data_source": "demo_rule_based" if mode == "demo" else "real_import_manual",
    }


def build_artifact_manifest(output_dir: Path, qa: dict, readiness: dict) -> dict:
    """Describe each artifact with purpose, status and next action for the UI."""
    qa_passed = bool(qa.get("passed"))
    dist_exists = bool(qa.get("checks", {}).get("dist_exists"))
    ready = bool(readiness.get("ready_to_submit"))

    miniapp_status = "ready" if (qa_passed and dist_exists) else "blocked"
    pkg_status = "ready" if ready else "blocked"

    items = [
        {"path": "candidate.json", "title": "候选 App", "purpose": "选中的候选应用信息",
         "status": "ready", "affects_submission": False, "next_action": "无"},
        {"path": "analysis.json", "title": "需求分析", "purpose": "需求强度评分",
         "status": "ready", "affects_submission": False, "next_action": "无"},
        {"path": "gap-check.json", "title": "覆盖检查", "purpose": "小程序平台覆盖缺口",
         "status": "ready", "affects_submission": False, "next_action": "无"},
        {"path": "opportunity-report.json", "title": "机会评分", "purpose": "综合机会评分",
         "status": "ready", "affects_submission": False, "next_action": "无"},
        {"path": "prd.md", "title": "PRD（可读）", "purpose": "产品需求文档",
         "status": "needs_review", "affects_submission": True, "next_action": "人工确认产品方案"},
        {"path": "prd.json", "title": "PRD（结构化）", "purpose": "结构化 PRD",
         "status": "ready", "affects_submission": False, "next_action": "无"},
        {"path": "generated/miniapp", "title": "小程序项目", "purpose": "生成的 uni-app 项目",
         "status": miniapp_status, "affects_submission": True,
         "next_action": "无" if miniapp_status == "ready" else "修复 QA/构建问题"},
        {"path": "qa-report.json", "title": "QA 报告", "purpose": "质量检查 + 构建验证",
         "status": "ready" if qa_passed else "needs_review", "affects_submission": True,
         "next_action": "无" if qa_passed else "查看 issues 并修复"},
        {"path": "listing-materials.md", "title": "上架材料（可读）", "purpose": "上架文案",
         "status": "needs_review", "affects_submission": True, "next_action": "人工 review 文案"},
        {"path": "listing-materials.json", "title": "上架材料（结构化）", "purpose": "结构化上架材料",
         "status": "ready", "affects_submission": False, "next_action": "无"},
        {"path": "human-actions.md", "title": "人工操作指南", "purpose": "上架步骤说明",
         "status": "ready", "affects_submission": False, "next_action": "按指南操作"},
        {"path": "submission-readiness-report.json", "title": "提交就绪报告",
         "purpose": "是否可提交审核的真实判断",
         "status": "ready", "affects_submission": True, "next_action": "查看 blocking_issues"},
        {"path": "publish-package", "title": "提交审核包", "purpose": "各平台提交材料",
         "status": pkg_status, "affects_submission": True,
         "next_action": "无" if ready else "解决提交阻塞项后再使用"},
    ]
    return {"job_id": _pipeline_job_id, "items": items}


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Use BOM only for .md files (Windows Notepad compatibility)
    # JSON/TS/Vue/HTML must NOT have BOM (breaks parsers)
    encoding = "utf-8-sig" if path.suffix == ".md" else "utf-8"
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "real"], default="demo", help="demo: sample data, real: imported data")
    parser.add_argument("--job-id", default=None, help="Pre-assigned job ID (from server)")
    args = parser.parse_args()
    mode = args.mode

    p("=" * 60)
    p(f"  Mini App Factory - Pipeline ({mode} mode)")
    p(f"  从市场数据到可上架小程序")
    p("=" * 60)

    # Generate job_id early so all steps can reference it
    global _pipeline_steps, _pipeline_output_dir, _pipeline_job_id
    if args.job_id:
        job_id = args.job_id
    else:
        job_id = datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6]
    output_dir = OUTPUTS_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _pipeline_steps = []
    _pipeline_output_dir = output_dir
    _pipeline_job_id = job_id
    _report_meta["mode"] = mode
    _report_meta["data_source"] = "demo_rule_based" if mode == "demo" else "real_import_manual"
    _report_meta["started_at"] = None
    _report_meta["finished_at"] = None
    _report_meta["total_passed"] = None
    _report_meta["error"] = None
    p(f"  Job ID: {job_id}")
    p(f"  输出目录: {output_dir}")

    try:
        qa = _run_pipeline_steps(mode, job_id, output_dir)
        finalize_pipeline_report(total_passed=bool(qa.get("passed")))
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        failed_step = _pipeline_steps[-1]["step"] if _pipeline_steps else "unknown"
        user_msg = f"流水线在「{failed_step}」步骤失败: {e}"
        # Close the in-flight step as failed (finalize also forces running->failed).
        if _pipeline_steps and _pipeline_steps[-1].get("status") == "running":
            step_end(error=str(e), error_code="pipeline_exception",
                     user_message=user_msg, developer_message=tb[-1500:])
        finalize_pipeline_report(total_passed=False, error=str(e))
        # Structured failure event for the dashboard WS.
        p(json.dumps({
            "event": "pipeline_failed",
            "job_id": _pipeline_job_id,
            "step": failed_step,
            "user_message": user_msg,
            "developer_message": str(e),
            "success": False,
        }))
        p(f"\n{'═' * 60}")
        p(f"  ✗ Pipeline 失败: {e}")
        p(f"{'═' * 60}")
        sys.exit(1)


def _run_pipeline_steps(mode: str, job_id: str, output_dir: Path) -> dict:
    """Execute all pipeline steps. Returns the QA report. Raises on any failure."""
    # === Step 1: Market Input ===
    t0 = time.time()
    step_header(1, "读取市场数据", "MarketInputAgent")
    step_start("market_input", "读取市场数据", "MarketInputAgent")
    apps = market_input_agent(mode=mode)
    p(f"  已加载 {len(apps)} 个候选应用")
    for a in apps:
        p(f"    • {a['name_cn']} ({a['name']}) - {a['downloads']:,} 下载")
    step_end(artifact="candidate.json")
    step_done("data/samples/apps.json", time.time() - t0)

    # === Step 2: Select best candidate ===
    step_header(2, "选择最优候选", "DemandAnalysisAgent")
    step_start("demand_analysis", "选择最优候选", "DemandAnalysisAgent")
    t0 = time.time()

    # Score all apps and pick the best
    scored = []
    for app in apps:
        analysis = demand_analysis_agent(app)
        scored.append((app, analysis))
        p(f"    {app['name_cn']}: 需求评分 {analysis['demand_score']}")

    scored.sort(key=lambda x: x[1]["demand_score"], reverse=True)
    best_app, best_analysis = scored[0]
    p(f"\n  ★ 选中：{best_app['name_cn']}（评分 {best_analysis['demand_score']}）")

    _write(output_dir / "candidate.json", json.dumps(best_app, ensure_ascii=False, indent=2))
    _write(output_dir / "analysis.json", json.dumps(best_analysis, ensure_ascii=False, indent=2))
    step_end(artifact="analysis.json")
    step_done(f"data/outputs/{job_id}/analysis.json", time.time() - t0)

    # === Step 3: Gap Check ===
    step_header(3, "小程序覆盖检查", "GapCheckAgent")
    step_start("gap_check", "覆盖检查", "GapCheckAgent")
    t0 = time.time()
    gap = gap_check_agent(best_app)
    p(f"  缺失平台: {gap['missing_platforms']}")
    p(f"  缺口评分: {gap['gap_score']}")
    p(f"  推荐平台: {gap['recommended_platforms']}")
    p(f"  机会等级: {gap['opportunity_level']}")
    _write(output_dir / "gap-check.json", json.dumps(gap, ensure_ascii=False, indent=2))
    step_end(artifact="gap-check.json")
    step_done(f"data/outputs/{job_id}/gap-check.json", time.time() - t0)

    # === Step 4: Opportunity Score ===
    step_header(4, "机会评分", "OpportunityScoreAgent")
    step_start("opportunity_score", "机会评分", "OpportunityScoreAgent")
    t0 = time.time()
    opportunity = opportunity_score_agent(best_app, best_analysis, gap)
    p(f"  综合评分: {opportunity['opportunity_score']}/100")
    p(f"  推荐动作: {opportunity['recommendation']}")
    p(f"  预计开发: {opportunity['estimated_dev_days']} 天")
    _write(output_dir / "opportunity-report.json", json.dumps(opportunity, ensure_ascii=False, indent=2))
    step_end(artifact="opportunity-report.json")
    step_done(f"data/outputs/{job_id}/opportunity-report.json", time.time() - t0)

    # === Step 5: Generate PRD ===
    step_header(5, "生成 PRD", "PRDAgent")
    step_start("prd_generation", "生成 PRD", "PRDAgent")
    t0 = time.time()
    prd_md, prd_json = prd_agent(best_app, opportunity)
    _write(output_dir / "prd.md", prd_md)
    _write(output_dir / "prd.json", json.dumps(prd_json, ensure_ascii=False, indent=2))
    p(f"  功能数: {len(prd_json['core_features'])}")
    p(f"  页面数: {len(prd_json['pages'])}")
    p(f"  技术栈: {prd_json['tech_stack']['framework']}")
    step_end(artifact="prd.json")
    step_done(f"data/outputs/{job_id}/prd.json", time.time() - t0)

    # === Step 6: Generate Code ===
    step_header(6, "生成小程序代码", "CodegenAgent")
    step_start("code_generation", "生成代码", "CodegenAgent")
    t0 = time.time()
    gen_dir = output_dir / "generated"
    gen_dir.mkdir(exist_ok=True)
    miniapp_dir, gen_source = codegen_agent(best_app, prd_json, gen_dir)
    _write(output_dir / "generator-source.json", json.dumps(gen_source, ensure_ascii=False, indent=2))
    file_count = gen_source["generated_files_count"]
    p(f"  项目路径: {miniapp_dir}")
    p(f"  生成文件: {file_count} 个")
    p(f"  模板来源: {gen_source['source']} ({gen_source['template']})")
    step_end(artifact="generated/miniapp/")
    step_done(f"data/outputs/{job_id}/generated/miniapp/", time.time() - t0)

    # === Step 7: Publish Materials ===
    step_header(7, "生成上架材料", "PublishMaterialsAgent")
    step_start("publish_materials", "上架材料", "PublishMaterialsAgent")
    t0 = time.time()
    listing_md, listing_json = publish_materials_agent(best_app, prd_json)
    _write(output_dir / "listing-materials.md", listing_md)
    _write(output_dir / "listing-materials.json", json.dumps(listing_json, ensure_ascii=False, indent=2))
    p(f"  小程序名: {listing_json['app_name_cn']}")
    p(f"  服务类目: {listing_json['category_suggestion']}")
    p(f"  关键词: {', '.join(listing_json['keywords'])}")
    step_end(artifact="listing-materials.json")
    step_done(f"data/outputs/{job_id}/listing-materials.json", time.time() - t0)

    # === Step 8: Human Actions + Publish Package ===
    step_header(8, "生成提交审核包", "PublishPackageAgent")
    step_start("submit_package", "提交审核包", "PublishPackageAgent")
    t0 = time.time()
    human_md = generate_human_actions(best_app, job_id, output_dir)
    _write(output_dir / "human-actions.md", human_md)

    # Generate publish-package directory
    pkg_dir = output_dir / "publish-package"
    pkg_dir.mkdir(exist_ok=True)
    _write(pkg_dir / "listing-materials.md", listing_md)
    _write(pkg_dir / "privacy-summary.md", f"# 隐私政策摘要\n\n{listing_json['privacy_summary']}")
    _write(pkg_dir / "user-agreement-summary.md", f"# 用户协议摘要\n\n{listing_json['user_agreement_summary']}")
    _write(pkg_dir / "review-notes.md", f"# 审核备注\n\n{listing_json['review_notes']}")
    _write(pkg_dir / "human-submit-guide.md", human_md)
    _write(pkg_dir / "platform-checklist.json", json.dumps({
        "platforms": [
            {"platform": plat, "status": "pending", "submitted_at": None, "review_result": None}
            for plat in opportunity["target_platforms"]
        ]
    }, ensure_ascii=False, indent=2))

    # Per-platform submit packages
    platform_guides = {
        "wechat": "1. 登录 mp.weixin.qq.com\n2. 打开微信开发者工具导入 dist/build/mp-weixin\n3. 上传代码\n4. 填写资料\n5. 提交审核",
        "alipay": "1. 登录 open.alipay.com\n2. 创建应用\n3. 上传代码\n4. 填写资料\n5. 提交审核",
        "douyin": "1. 登录 developer.open-douyin.com\n2. 创建小程序\n3. 上传代码\n4. 提交审核",
        "telegram": "1. 联系 @BotFather 创建 Bot\n2. 使用 /newapp 创建 Web App\n3. 部署前端到 HTTPS URL\n4. 配置 WebApp URL\n5. 无需审核，部署即上线",
        "discord": "1. 创建 Discord Application\n2. 配置 Activity URL\n3. 集成 Discord SDK\n4. 提交审核",
        "reddit": "1. 安装 devvit CLI\n2. 创建 Devvit App\n3. 本地开发调试\n4. 发布到社区",
        "line": "1. 创建 LINE Channel\n2. 配置 LIFF App\n3. 部署 Web App\n4. 提交审核",
    }
    for plat in opportunity["target_platforms"]:
        plat_dir = pkg_dir / plat
        plat_dir.mkdir(exist_ok=True)
        guide = platform_guides.get(plat, f"平台 {plat} 提交指南待补充")
        _write(plat_dir / "submit-guide.md", f"# {plat} 提交指南\n\n{guide}")
        _write(plat_dir / "required-materials.json", json.dumps({"platform": plat, "materials": listing_json.get("keywords", [])}, ensure_ascii=False, indent=2))
        _write(plat_dir / "review-notes.md", f"# {plat} 审核备注\n\n{listing_json['review_notes']}")

    # Generate submit-status.json
    submit_status = {
        "job_id": job_id,
        "platforms": [
            {
                "platform_id": plat,
                "configured": _platform_auth_status(plat)[0],
                "can_upload": False,
                "upload_status": "not_started",
                "review_status": "not_submitted",
                "release_status": "not_released",
                "last_action_by": "system",
                "last_action_at": datetime.now().isoformat(),
                "next_action_owner": "human",
                "next_action": f"配置 {plat} 平台授权后自动上传",
            }
            for plat in opportunity["target_platforms"]
        ],
    }
    _write(output_dir / "submit-status.json", json.dumps(submit_status, ensure_ascii=False, indent=2))

    p(f"  publish-package/ 已生成")
    p(f"  目标平台: {', '.join(opportunity['target_platforms'])}")
    step_end(artifact="publish-package/")
    step_done(f"data/outputs/{job_id}/publish-package/", time.time() - t0)

    # === Step 10: QA Check (runs last, includes npm install + build) ===
    step_header(10, "质量检查 + 构建验证", "QACheckAgent")
    step_start("build_qa", "构建+质检", "QACheckAgent")
    t0 = time.time()
    p(f"  执行 npm install + npm run build:mp-weixin...")
    qa = qa_check_agent(miniapp_dir, output_dir)
    checks = qa["checks"]
    p(f"  文件存在:   {'通过' if checks['files_exist'] else '失败'}")
    p(f"  编码检查:   {'通过' if checks['encoding_passed'] else '失败 - 发现乱码'}")
    p(f"  路径检查:   {'通过' if checks['path_passed'] else '失败'}")
    p(f"  上架字段:   {'通过' if checks['listing_fields_passed'] else '失败'}")
    p(f"  README:     {'通过' if checks['readme_passed'] else '失败'}")
    p(f"  构建脚本:   {'通过' if checks['build_scripts_passed'] else '失败'}")
    p(f"  JSON 合法:  {'通过' if checks['json_valid'] else '失败'}")
    p(f"  包大小:     {qa['total_size_readable']}（{'合规' if checks['size_within_limit'] else '超限'}）")
    p(f"  npm install: {'通过' if checks['install_passed'] else '失败'} ({checks['install_duration_ms']}ms)")
    p(f"  build 验证:  {'通过' if checks['build_passed'] else '失败'} ({checks['build_duration_ms']}ms)")
    p(f"  dist 存在:   {'是' if checks['dist_exists'] else '否'}")
    if checks.get('dist_path'):
        p(f"  dist 路径:   {checks['dist_path']}")
    p(f"  QA 结果:    {'✓ 全部通过' if qa['passed'] else '✗ 未通过'}")
    if qa["issues"]:
        for issue in qa["issues"][:5]:
            p(f"    ▸ {issue}")
    _write(output_dir / "qa-report.json", json.dumps(qa, ensure_ascii=False, indent=2))
    # Mark step as failed if QA didn't pass, so pipeline-report stays consistent
    if qa["passed"]:
        step_end(artifact="qa-report.json")
    else:
        qa_fail_reason = "; ".join(qa["issues"][:3]) if qa["issues"] else "QA 检查未通过"
        step_end(artifact="qa-report.json", error=qa_fail_reason,
                 error_code="qa_failed", user_message=f"QA 未通过: {qa_fail_reason}")
    step_done(f"data/outputs/{job_id}/qa-report.json", time.time() - t0)

    # === Step 11: Honest submission readiness + artifact manifest (post-QA) ===
    step_header(11, "提交就绪评估 + 产物清单", "ReadinessAgent")
    step_start("readiness", "提交就绪评估", "ReadinessAgent")
    t0 = time.time()
    readiness = build_submission_readiness(best_app, opportunity, qa, output_dir, mode)
    _write(output_dir / "submission-readiness-report.json", json.dumps(readiness, ensure_ascii=False, indent=2))
    manifest = build_artifact_manifest(output_dir, qa, readiness)
    _write(output_dir / "artifact-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    p(f"  可提交审核: {'是' if readiness['ready_to_submit'] else '否'}")
    if not readiness["ready_to_submit"]:
        p(f"  阻塞项:")
        for b in readiness["blocking_issues"]:
            p(f"    ▸ {b}")
    step_end(artifact="submission-readiness-report.json")
    step_done(f"data/outputs/{job_id}/submission-readiness-report.json", time.time() - t0)

    # === SUMMARY ===
    p("\n" + "=" * 60)
    p("  ✓ Pipeline 完成")
    p("=" * 60)
    p(f"\n  选中应用: {best_app['name_cn']} ({best_app['name']})")
    p(f"  机会评分: {opportunity['opportunity_score']}/100")
    p(f"  QA 结果: {'通过 ✓' if qa['passed'] else '未通过 ✗'}")
    p(f"  可提交审核: {'是' if readiness['ready_to_submit'] else '否（见 submission-readiness-report.json）'}")
    p(f"  Job ID:  {job_id}")
    p(f"  输出目录: {output_dir}")
    p(f"\n  产物清单:")
    for f in sorted(output_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(output_dir)
            p(f"    {rel}")

    p(f"\n{'─' * 60}")
    p(f"  ⚡ 下一步人工动作:")
    p(f"{'─' * 60}")
    p(f"  1. 阅读 prd.md 确认产品方案")
    p(f"  2. 阅读 human-actions.md 了解上架步骤")
    p(f"  3. 使用微信开发者工具导入 generated/miniapp/")
    p(f"  4. 上传代码并提交审核")
    p(f"  5. 审核通过后发布上线")
    p(f"\n  详细指南: {output_dir / 'human-actions.md'}")
    p("")
    return qa


if __name__ == "__main__":
    main()
