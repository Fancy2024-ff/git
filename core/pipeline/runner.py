"""
Demo Pipeline - 完整 MVP 闭环演示
从 data/inputs/demo/apps.json 选择高需求 App → 全流程产出文件 → 打印人工待办

运行方式:
    python core/pipeline/runner.py --mode demo

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

# This file lives at core/pipeline/runner.py → parent.parent.parent = repo root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
# New structure: data/inputs/demo + data/inputs/real
# Legacy fallback: data/samples + data/real_inputs (kept for compatibility)
SAMPLES_DIR = DATA_DIR / "inputs" / "demo"
REAL_INPUTS_DIR = DATA_DIR / "inputs" / "real"
LEGACY_SAMPLES_DIR = DATA_DIR / "samples"
LEGACY_REAL_INPUTS_DIR = DATA_DIR / "real_inputs"
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
    p(json.dumps({"event": "step_started", "job_id": _pipeline_job_id, "step": step_id, "agent": agent, "name": name, "message": name, "status": "running", "started_at": entry["started_at"]}))


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
        "agent": entry["agent"], "name": entry["name"], "status": entry["status"],
        "artifact": artifact or "",
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
    """读取 App 数据。demo=样例, real=导入数据, live=实时抓取 App Store + Google Play。"""
    if mode == "live":
        return _fetch_live_apps()
    elif mode == "real":
        # New path first, fall back to legacy data/real_inputs
        apps_file = REAL_INPUTS_DIR / "apps.json"
        if not apps_file.exists():
            apps_file = LEGACY_REAL_INPUTS_DIR / "apps.json"
        if not apps_file.exists():
            raise FileNotFoundError(
                "data/inputs/real/apps.json not found\n"
                "请先导入真实 App 数据，参考模板: data/inputs/real/apps.example.json"
            )
    else:
        # New path first, fall back to legacy data/samples
        apps_file = SAMPLES_DIR / "apps.json"
        if not apps_file.exists():
            apps_file = LEGACY_SAMPLES_DIR / "apps.json"
        if not apps_file.exists():
            raise FileNotFoundError(f"样本数据不存在: {apps_file}")
    apps = json.loads(apps_file.read_text(encoding="utf-8-sig"))
    if not isinstance(apps, list) or not apps:
        raise ValueError(f"{apps_file} 必须是非空的 JSON 数组")
    return [_normalize_app(a) for a in apps]


def _fetch_live_apps() -> list[dict]:
    """实时从 App Store + Google Play 抓取 AI 类 App。"""
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT / "core" / "agents"))
    from discovery.scrapers.appstore import fetch_ai_apps_appstore
    from discovery.scrapers.googleplay import fetch_ai_apps_googleplay

    print("  [Live] 正在从 App Store 抓取...")
    appstore_apps = fetch_ai_apps_appstore(category="ai", limit=20)
    print(f"  [Live] App Store: 获取 {len(appstore_apps)} 个 App")

    print("  [Live] 正在从 Google Play 抓取...")
    gp_apps = fetch_ai_apps_googleplay(category="ai", limit=20)
    print(f"  [Live] Google Play: 获取 {len(gp_apps)} 个 App")

    # Merge and dedup
    seen = set()
    all_apps = []
    for app in appstore_apps + gp_apps:
        name_lower = app.name.lower()
        if name_lower in seen:
            continue
        seen.add(name_lower)
        all_apps.append({
            "name": app.name,
            "name_cn": app.name,  # Will be translated by LLM later
            "app_id": app.app_id,
            "source": app.source.value if hasattr(app.source, 'value') else str(app.source),
            "category": app.category,
            "description": (app.description or "")[:300],
            "description_cn": (app.description or "")[:300],
            "downloads": app.downloads or 0,
            "rating": app.rating or 0.0,
            "review_count": 0,
            "features": app.features if hasattr(app, 'features') else [],
            "monetization": "freemium",
        })

    # Sort by downloads, take top 10 (coerce None to 0 defensively)
    all_apps.sort(key=lambda a: a.get("downloads") or 0, reverse=True)
    top_apps = all_apps[:10]
    print(f"  [Live] 合并去重后 Top 10:")
    for a in top_apps:
        print(f"    {a['name']} | {a['downloads']:,} downloads | {a['rating']:.1f}⭐")

    return [_normalize_app(a) for a in top_apps]


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
            # Registry is external/editable data — tolerate entries missing
            # status/id rather than crashing the whole pipeline.
            if not p.get("id"):
                continue
            status = p.get("status")
            if status == "active":
                active_platforms.append(p)
            elif status == "research_needed":
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

    # 综合评分 需求 25% + 缺口 25% + 适配度 20% + 实现难度 15% + 风险 15% 
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


def _build_feature_pages(app_type: str, feature_label: str) -> tuple[str, str]:
    """按 app_type 返回 (form.vue, result.vue) 内容。

    每类都含 5 态：空状态/输入/处理中/成功/失败。
    text_ai 保持原文本逻辑（不回归）；其余类型生成各自能力骨架。
    所有类型的"真实处理"都通过 utils/request.ts 调后端；未接入时显示明确提示，绝不假成功。
    """
    builders = {
        "text_ai": _pages_text_ai,
        "image_ai": _pages_image_ai,
        "ocr_scan": _pages_ocr_scan,
        "speech_ai": _pages_speech_ai,
        "video_light": _pages_video_light,
        "utility_tool": _pages_utility_tool,
    }
    return builders.get(app_type, _pages_text_ai)(feature_label)


def _pages_text_ai(label: str) -> tuple[str, str]:
    form = f"""<template>
  <view class="container">
    <view class="form-card">
      <text class="form-title">{label}</text>
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
  if (!inputText.value.trim()) {{ uni.showToast({{ title: '请输入内容', icon: 'none' }}); return }}
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
"""
    result = """<template>
  <view class="container">
    <view class="result-card">
      <text class="result-title">处理结果</text>
      <view class="result-content"><text class="result-text">{{ resultText }}</text></view>
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
function copyResult() { uni.setClipboardData({ data: resultText.value }) }
function goBack() { uni.navigateBack() }
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
"""
    return form, result


# 其余 app_type 的页面生成器在下方 append（占位，下一步填充）
def _pages_image_ai(label: str) -> tuple[str, str]:
    """图像类：选图→选参数→上传→轮询→预览→保存。5 态完整。
    真实处理走 utils/request.ts 调后端能力 API；未接入时明确提示，绝不假成功。"""
    form = f"""<template>
  <view class="container">
    <view class="card">
      <text class="title">{label}</text>
      <view class="upload-area" @click="chooseImage">
        <image v-if="imageUrl" :src="imageUrl" mode="aspectFit" class="preview" />
        <view v-else class="upload-empty">
          <text class="upload-plus">+</text>
          <text class="upload-hint">点击选择图片</text>
        </view>
      </view>
      <view class="params">
        <text class="param-label">处理方式</text>
        <view class="param-options">
          <view v-for="op in operations" :key="op.value"
                class="param-chip" :class="{{ active: op.value === operation }}"
                @click="operation = op.value">{{{{ op.label }}}}</view>
        </view>
      </view>
      <button class="btn-submit" :disabled="!imageUrl || processing" @click="submit">
        {{{{ processing ? '处理中...' : '开始处理' }}}}
      </button>
      <text v-if="errorMsg" class="error-line">{{{{ errorMsg }}}}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'
import {{ request }} from '../../utils/request'

// 状态机：idle / creating / processing / succeeded / failed / provider_missing
const imageUrl = ref('')
const operation = ref('remove_background')
const status = ref('idle')
const errorMsg = ref('')
const operations = [
  {{ value: 'remove_background', label: '抠图换底' }},
  {{ value: 'id_photo', label: '证件照' }},
  {{ value: 'avatar_style', label: '头像风格化' }},
  {{ value: 'enhance', label: '画质增强' }},
]
const processing = ref(false)

function chooseImage() {{
  uni.chooseImage({{ count: 1, success: (res: any) => {{ imageUrl.value = res.tempFilePaths[0]; errorMsg.value = ''; status.value = 'idle' }} }})
}}

function sleep(ms: number) {{ return new Promise(r => setTimeout(r, ms)) }}

async function submit() {{
  if (!imageUrl.value) return
  processing.value = true
  errorMsg.value = ''
  status.value = 'creating'
  try {{
    // 1) 创建 runtime 任务（真实后端，绝不本地假处理）
    const created: any = await request('/api/runtime/image/tasks', 'POST', {{ operation: operation.value, source: imageUrl.value }})
    if (created.error_code === 'provider_missing') {{
      status.value = 'provider_missing'
      errorMsg.value = created.message || '图像能力未接入（需配置图像 API）'
      return
    }}
    if (!created.task_id || created.error_code) {{
      status.value = 'failed'
      errorMsg.value = created.message || '任务创建失败'
      return
    }}
    // 2) 轮询任务状态
    status.value = 'processing'
    const taskId = created.task_id
    for (let i = 0; i < 30; i++) {{
      const polled: any = await request('/api/runtime/image/tasks/' + taskId, 'GET')
      if (polled.status === 'succeeded') break
      if (polled.status === 'failed' || polled.status === 'timeout') {{
        status.value = 'failed'
        errorMsg.value = polled.message || '处理失败'
        return
      }}
      await sleep(1000)
    }}
    // 3) 取结果
    const res: any = await request('/api/runtime/image/tasks/' + taskId + '/result', 'GET')
    const url = res.result && res.result.result_url
    if (res.status === 'succeeded' && url) {{
      status.value = 'succeeded'
      uni.navigateTo({{ url: '/pages/result/result?img=' + encodeURIComponent(url) }})
    }} else {{
      status.value = 'failed'
      errorMsg.value = res.message || '未取得结果'
    }}
  }} catch (e: any) {{
    status.value = 'failed'
    errorMsg.value = '调用失败：' + (e?.message || '未知错误')
  }} finally {{
    processing.value = false
  }}
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f7; }}
.card {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.title {{ font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }}
.upload-area {{ width: 100%; height: 360rpx; border: 2rpx dashed #d2d2d7; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
.preview {{ width: 100%; height: 100%; }}
.upload-empty {{ display: flex; flex-direction: column; align-items: center; }}
.upload-plus {{ font-size: 64rpx; color: #c7c7cc; }}
.upload-hint {{ font-size: 26rpx; color: #8e8e93; }}
.params {{ margin: 28rpx 0; }}
.param-label {{ font-size: 26rpx; color: #6e6e73; }}
.param-options {{ display: flex; flex-wrap: wrap; gap: 16rpx; margin-top: 12rpx; }}
.param-chip {{ padding: 12rpx 24rpx; background: #f5f5f7; border-radius: 999rpx; font-size: 26rpx; color: #333; }}
.param-chip.active {{ background: #0071e3; color: #fff; }}
.btn-submit {{ background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }}
.btn-submit[disabled] {{ opacity: 0.5; }}
.error-line {{ display: block; margin-top: 20rpx; font-size: 24rpx; color: #ff3b30; }}
</style>
"""
    result = """<template>
  <view class="container">
    <view class="card">
      <text class="title">处理结果</text>
      <image v-if="imgUrl" :src="imgUrl" mode="widthFix" class="result-img" />
      <view v-else class="empty"><text>暂无结果图</text></view>
      <view class="actions">
        <button v-if="imgUrl" class="btn-save" @click="save">保存到相册</button>
        <button class="btn-back" @click="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
const imgUrl = ref('')
onLoad((options: any) => { if (options?.img) imgUrl.value = decodeURIComponent(options.img) })
function save() {
  if (!imgUrl.value) return
  uni.downloadFile({ url: imgUrl.value, success: (r) => {
    uni.saveImageToPhotosAlbum({ filePath: r.tempFilePath,
      success: () => uni.showToast({ title: '已保存' }),
      fail: () => uni.showToast({ title: '保存失败', icon: 'none' }) })
  }})
}
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.result-img { width: 100%; border-radius: 12rpx; }
.empty { min-height: 200rpx; display: flex; align-items: center; justify-content: center; color: #8e8e93; font-size: 26rpx; }
.actions { display: flex; gap: 16rpx; margin-top: 24rpx; }
.btn-save { flex: 1; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-back { flex: 1; background: #f5f5f7; color: #333; border: none; border-radius: 12rpx; font-size: 28rpx; }
</style>
"""
    return form, result

def _pages_ocr_scan(label: str) -> tuple[str, str]:
    """OCR：拍照/上传 → 识别 → 结果可复制。"""
    form = f"""<template>
  <view class="container">
    <view class="card">
      <text class="title">{label}</text>
      <view class="upload-area" @click="chooseImage">
        <image v-if="imageUrl" :src="imageUrl" mode="aspectFit" class="preview" />
        <text v-else class="upload-hint">点击拍照 / 选择图片</text>
      </view>
      <button class="btn-submit" :disabled="!imageUrl || processing" @click="submit">
        {{{{ processing ? '识别中...' : '开始识别' }}}}
      </button>
      <text v-if="errorMsg" class="error-line">{{{{ errorMsg }}}}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'
import {{ request }} from '../../utils/request'
const imageUrl = ref('')
const processing = ref(false)
const errorMsg = ref('')
function chooseImage() {{
  uni.chooseImage({{ count: 1, sourceType: ['album', 'camera'],
    success: (res: any) => {{ imageUrl.value = res.tempFilePaths[0]; errorMsg.value = '' }} }})
}}
async function submit() {{
  processing.value = true; errorMsg.value = ''
  try {{
    const res: any = await request('/api/vision/ocr', {{ image: imageUrl.value }})
    if (res && res.text) uni.navigateTo({{ url: '/pages/result/result?text=' + encodeURIComponent(res.text) }})
    else errorMsg.value = (res && res.message) || 'OCR 能力未接入（需配置视觉 API）'
  }} catch (e: any) {{ errorMsg.value = 'OCR 能力未接入或失败：' + (e?.message || '') }}
  finally {{ processing.value = false }}
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f7; }}
.card {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.title {{ font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }}
.upload-area {{ width: 100%; height: 320rpx; border: 2rpx dashed #d2d2d7; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
.preview {{ width: 100%; height: 100%; }}
.upload-hint {{ font-size: 26rpx; color: #8e8e93; }}
.btn-submit {{ margin-top: 28rpx; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }}
.btn-submit[disabled] {{ opacity: 0.5; }}
.error-line {{ display: block; margin-top: 20rpx; font-size: 24rpx; color: #ff3b30; }}
</style>
"""
    result = """<template>
  <view class="container">
    <view class="card">
      <text class="title">识别结果</text>
      <view class="result-content"><text class="result-text">{{ resultText || '暂无识别结果' }}</text></view>
      <view class="actions">
        <button class="btn-copy" @click="copy">复制结果</button>
        <button class="btn-back" @click="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
const resultText = ref('')
onLoad((o: any) => { if (o?.text) resultText.value = decodeURIComponent(o.text) })
function copy() { if (resultText.value) uni.setClipboardData({ data: resultText.value }) }
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.result-content { background: #f5f5f7; border-radius: 12rpx; padding: 24rpx; min-height: 200rpx; margin-bottom: 24rpx; }
.result-text { font-size: 28rpx; color: #333; white-space: pre-wrap; }
.actions { display: flex; gap: 16rpx; }
.btn-copy { flex: 1; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-back { flex: 1; background: #f5f5f7; color: #333; border: none; border-radius: 12rpx; font-size: 28rpx; }
</style>
"""
    return form, result


def _pages_speech_ai(label: str) -> tuple[str, str]:
    """语音：文本输入 → TTS 合成 → 音频播放（未接入时提示）。"""
    form = f"""<template>
  <view class="container">
    <view class="card">
      <text class="title">{label}</text>
      <textarea class="input-area" v-model="text" placeholder="输入要合成语音的文本..." />
      <button class="btn-submit" :disabled="!text || processing" @click="submit">
        {{{{ processing ? '合成中...' : '生成语音' }}}}
      </button>
      <text v-if="errorMsg" class="error-line">{{{{ errorMsg }}}}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'
import {{ request }} from '../../utils/request'
const text = ref('')
const processing = ref(false)
const errorMsg = ref('')
async function submit() {{
  if (!text.value.trim()) return
  processing.value = true; errorMsg.value = ''
  try {{
    const res: any = await request('/api/speech/tts', {{ text: text.value }})
    if (res && res.audio_url) uni.navigateTo({{ url: '/pages/result/result?audio=' + encodeURIComponent(res.audio_url) }})
    else errorMsg.value = (res && res.message) || '语音能力未接入（需配置语音 API）'
  }} catch (e: any) {{ errorMsg.value = '语音能力未接入或失败：' + (e?.message || '') }}
  finally {{ processing.value = false }}
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f7; }}
.card {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.title {{ font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }}
.input-area {{ width: 100%; min-height: 220rpx; padding: 20rpx; border: 1rpx solid #e8e8ed; border-radius: 12rpx; font-size: 28rpx; }}
.btn-submit {{ margin-top: 28rpx; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }}
.btn-submit[disabled] {{ opacity: 0.5; }}
.error-line {{ display: block; margin-top: 20rpx; font-size: 24rpx; color: #ff3b30; }}
</style>
"""
    result = """<template>
  <view class="container">
    <view class="card">
      <text class="title">合成结果</text>
      <view v-if="audioUrl" class="audio-box">
        <button class="btn-play" @click="play">▶ 播放语音</button>
      </view>
      <view v-else class="empty"><text>暂无音频</text></view>
      <button class="btn-back" @click="goBack">返回</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
const audioUrl = ref('')
let ctx: any = null
onLoad((o: any) => { if (o?.audio) audioUrl.value = decodeURIComponent(o.audio) })
function play() {
  if (!audioUrl.value) return
  ctx = ctx || uni.createInnerAudioContext()
  ctx.src = audioUrl.value
  ctx.play()
}
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.audio-box { margin-bottom: 24rpx; }
.btn-play { background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.empty { min-height: 160rpx; display: flex; align-items: center; justify-content: center; color: #8e8e93; font-size: 26rpx; }
.btn-back { background: #f5f5f7; color: #333; border: none; border-radius: 12rpx; font-size: 28rpx; }
</style>
"""
    return form, result

def _pages_video_light(label: str) -> tuple[str, str]:
    """轻视频：输入视频链接 → 异步处理 → 结果入口（未接入时提示）。"""
    form = f"""<template>
  <view class="container">
    <view class="card">
      <text class="title">{label}</text>
      <input class="input-line" v-model="videoUrl" placeholder="粘贴视频链接..." />
      <view class="ops">
        <view v-for="op in ops" :key="op.value" class="op-chip"
              :class="{{ active: op.value === operation }}" @click="operation = op.value">{{{{ op.label }}}}</view>
      </view>
      <button class="btn-submit" :disabled="!videoUrl || processing" @click="submit">
        {{{{ processing ? '处理中...' : '开始处理' }}}}
      </button>
      <text v-if="errorMsg" class="error-line">{{{{ errorMsg }}}}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'
import {{ request }} from '../../utils/request'
const videoUrl = ref('')
const operation = ref('summarize')
const processing = ref(false)
const errorMsg = ref('')
const ops = [
  {{ value: 'summarize', label: '视频摘要' }},
  {{ value: 'cover', label: '封面生成' }},
  {{ value: 'script', label: '脚本提取' }},
]
async function submit() {{
  if (!videoUrl.value) return
  processing.value = true; errorMsg.value = ''
  try {{
    const res: any = await request('/api/video/process', {{ operation: operation.value, url: videoUrl.value }})
    if (res && res.result) uni.navigateTo({{ url: '/pages/result/result?text=' + encodeURIComponent(res.result) }})
    else errorMsg.value = (res && res.message) || '视频能力未接入（需配置视频 API）'
  }} catch (e: any) {{ errorMsg.value = '视频能力未接入或失败：' + (e?.message || '') }}
  finally {{ processing.value = false }}
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f7; }}
.card {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.title {{ font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }}
.input-line {{ width: 100%; padding: 20rpx; border: 1rpx solid #e8e8ed; border-radius: 12rpx; font-size: 28rpx; }}
.ops {{ display: flex; gap: 16rpx; margin: 24rpx 0; }}
.op-chip {{ padding: 12rpx 24rpx; background: #f5f5f7; border-radius: 999rpx; font-size: 26rpx; color: #333; }}
.op-chip.active {{ background: #0071e3; color: #fff; }}
.btn-submit {{ background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }}
.btn-submit[disabled] {{ opacity: 0.5; }}
.error-line {{ display: block; margin-top: 20rpx; font-size: 24rpx; color: #ff3b30; }}
</style>
"""
    # 复用 text 的结果页（文本结果展示）
    _, result = _pages_text_ai(label)
    return form, result


def _pages_utility_tool(label: str) -> tuple[str, str]:
    """工具：结构化输入表单 → 结果卡片（本地能力，无需外部 API）。"""
    form = f"""<template>
  <view class="container">
    <view class="card">
      <text class="title">{label}</text>
      <input class="input-line" v-model="a" type="number" placeholder="输入数值 A" />
      <input class="input-line" v-model="b" type="number" placeholder="输入数值 B" />
      <button class="btn-submit" @click="submit">计算</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'
const a = ref('')
const b = ref('')
function submit() {{
  const sum = (Number(a.value) || 0) + (Number(b.value) || 0)
  uni.navigateTo({{ url: '/pages/result/result?text=' + encodeURIComponent('结果: ' + sum) }})
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f7; }}
.card {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.title {{ font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }}
.input-line {{ width: 100%; padding: 20rpx; margin-bottom: 16rpx; border: 1rpx solid #e8e8ed; border-radius: 12rpx; font-size: 28rpx; }}
.btn-submit {{ margin-top: 12rpx; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }}
</style>
"""
    _, result = _pages_text_ai(label)
    return form, result



def codegen_agent(app: dict, prd_json: dict, output_dir: Path, app_type: str = "text_ai") -> tuple[Path, dict]:
    """代码生成 Agent：复制 base 骨架 + 按 app_type 叠加对应能力模板，再定制化。

    模板矩阵（registry 驱动，不写死）：
      app_type → core/generator/src/templates/{app_type}/
    text_ai 保持与历史等价（不回归）；其余类型叠加各自的能力页面骨架。
    """
    import shutil

    miniapp_dir = output_dir / "miniapp"
    templates_dir = PROJECT_ROOT / "core" / "generator" / "src" / "templates"
    base_template = templates_dir / "base"

    # 由单一事实源决定该 app_type 用哪个模板目录
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "core"))
        from capabilities.app_types import template_for
        template_name = template_for(app_type)
    except Exception:
        template_name = "text_ai"

    # Track generation source
    gen_source = {
        "source": "generator_templates",
        "template": "base",
        "app_type": app_type,
        "fallback_used": False,
        "generated_files_count": 0,
    }

    # Primary: copy from core/generator/src/templates/base
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

    # 叠加 app_type 专属模板（若存在）。模板目录已统一为 6 类正式名（旧 ai-tool/ai-chat/ai-image 已迁移删除）。
    overlay_candidates = [templates_dir / template_name]
    applied = []
    for tmpl in overlay_candidates:
        if tmpl.exists():
            for sub in tmpl.rglob("*"):
                if sub.is_file():
                    dest = miniapp_dir / sub.relative_to(tmpl)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(sub), str(dest))
            applied.append(tmpl.name)
    if applied:
        gen_source["template"] = "base/" + "+".join(applied)
    else:
        gen_source["template"] = "base"

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

    # 第 2、3 页（功能页 + 结果页）按 app_type 生成不同的能力骨架。
    # text_ai 保持原文本表单逻辑（不回归）；image_ai/ocr_scan/speech_ai/video_light/
    # utility_tool 各自生成对应交互（选图/上传/轮询/结果等），含 5 态视图。
    feature_label = app["features_cn"][0] if app.get("features_cn") else app_name
    form_vue, result_vue = _build_feature_pages(app_type, feature_label)
    _write(pages_dir / "form" / "form.vue", form_vue)
    _write(pages_dir / "result" / "result.vue", result_vue)

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
        "telegram": ["bot_token"],
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

    # 平台元数据唯一来源：core/platforms/registry.py（其内部以 data 文件为 legacy backing）
    sys.path.insert(0, str(PROJECT_ROOT / "core"))
    from platforms import registry as plat_registry
    from platforms.common import readiness as plat_readiness

    platform_readiness = []
    rejected_platforms = []
    any_configured = False

    for plat in opportunity["target_platforms"]:
        status = plat_registry.get_status(plat)
        if status in ("not_supported", "research_needed"):
            rejected_platforms.append({
                "platform": plat,
                "reason": (plat_registry.get_platform(plat).get("notes", "平台不支持")
                           if status == "not_supported" else "待调研，暂不可提交"),
            })
            continue

        configured, missing_fields = _platform_auth_status(plat)
        any_configured = any_configured or configured
        upload_path = str(output_dir / "generated" / "miniapp" / plat_registry.get_upload_target(plat))

        # 单平台 readiness 由平台公共层统一构造（can_upload/uploaded/upload_status 语义一致）
        platform_readiness.append(plat_readiness.normalize_platform_readiness(
            platform_id=plat, status=status, configured=configured,
            missing_fields=missing_fields, qa_passed=qa_passed, dist_exists=dist_exists,
            upload_path=upload_path,
        ))

    # Global blocking / warning issues
    blocking_issues = []
    if not qa_passed:
        blocking_issues.append("QA 未通过或构建失败，不能提交审核")
    if not dist_exists:
        blocking_issues.append("构建产物 dist/build/mp-weixin 缺失")
    if not any_configured:
        blocking_issues.append("尚未配置任何平台授权（缺 AppID/密钥）")
    # 人工阻塞项（始终需要，且无法自动产出）—— 单独列出供 review_ready 判定
    human_blockers = [
        "缺少真机测试截图，需人工准备",
        "未在目标平台真机测试",
    ]
    blocking_issues.extend(human_blockers)

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

    # L5：读已生成的 runtime 状态，给出分阶段就绪表达（code/build/qa/materials/upload/review/runtime）
    runtime_ready = False
    runnable_level = "buildable"
    try:
        rt_path = output_dir / "runtime-capability-status.json"
        if rt_path.exists():
            rt = json.loads(rt_path.read_text(encoding="utf-8"))
            runtime_ready = bool(rt.get("runtime_ready"))
            runnable_level = rt.get("runnable_level", "buildable")
    except Exception:
        pass

    materials_ready = (output_dir / "listing-materials.json").exists()
    # 顶层就绪度由平台公共层聚合（upload_ready=可上传 / upload_completed=已上传 / review_ready）
    summary = plat_readiness.build_submission_readiness_summary(
        platform_readiness, qa_passed=qa_passed,
        materials_ready=materials_ready, human_blockers=human_blockers)

    return {
        "job_id": _pipeline_job_id,
        "app_name": best_app["name_cn"],
        "ready_to_submit": len(blocking_issues) == 0,
        # Back-compat alias for older web clients; same value as ready_to_submit.
        "is_ready_to_submit": len(blocking_issues) == 0,
        "blocking_issues": blocking_issues,
        "warning_issues": warning_issues,
        "human_actions": human_actions,
        "qa_passed": qa_passed,
        "build_dist_exists": dist_exists,
        "target_platforms": [p["platform"] for p in platform_readiness],
        "rejected_platforms": rejected_platforms,
        "platform_readiness": platform_readiness,
        # —— L5 分阶段就绪（每一档独立语义，见 PLATFORM_READINESS_CONTRACT.md）——
        "code_generated": True,
        "build_passed": bool(qa.get("checks", {}).get("build_passed")),
        "qa_passed": qa_passed,
        "materials_ready": materials_ready,
        "upload_ready": summary["upload_ready"],            # 是否具备上传条件（∃ can_upload）
        "upload_completed": summary["upload_completed"],    # 是否已上传成功（∃ uploaded）
        "review_ready": summary["review_ready"],            # 是否可进入审核提交阶段（平台层判定）
        "runtime_ready": runtime_ready,
        "runnable_level": runnable_level,
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


def _safe_error(e: Exception) -> str:
    """脱敏的错误摘要：不回显 key/url 等敏感串，截断长度。"""
    msg = f"{type(e).__name__}: {e}"
    return msg[:300]


def _use_llm() -> bool:
    """运行时读 USE_LLM（便于测试 monkeypatch settings）。"""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "core" / "agents"))
        from config import settings
        return bool(getattr(settings, "USE_LLM", False))
    except Exception:
        return False


def _run_product_decision(best_app: dict, app_type: str, opportunity: dict, gap: dict,
                          analysis: dict, output_dir: Path) -> None:
    """成熟需求分析框架：8 维度 + MVP 拆解 + 决策，写 5 个 artifact，回写 analysis 关键字段。永不抛异常。"""
    sys.path.insert(0, str(PROJECT_ROOT / "core" / "agents"))
    sys.path.insert(0, str(PROJECT_ROOT / "core"))
    try:
        from capabilities.registry import build_capability_snapshot
        from research.product_research import analyze_product
        from research.artifacts import write_research_artifacts
        cap_snapshot = build_capability_snapshot(app_type)
        result = analyze_product(best_app, app_type=app_type, opportunity=opportunity,
                                 gap=gap, cap_snapshot=cap_snapshot, use_llm=_use_llm())
        write_research_artifacts(output_dir, result)
        dec = result["decision"]
        # 回写 analysis 关键决策字段（兼容现有 analysis.json 消费）
        analysis["market_opportunity_score"] = dec["market_opportunity_score"]
        analysis["miniapp_feasibility_score"] = dec["miniapp_feasibility_score"]
        analysis["recommendation"] = dec["recommendation"]
        analysis["execution_confidence"] = dec["execution_confidence"]
        analysis["blocking_reasons"] = dec["blocking_reasons"]
        analysis["recommended_mvp_name"] = result["split_plan"]["recommended_mvp"].get("name", "")
        analysis["recommended_app_type"] = result["split_plan"]["recommended_mvp"].get("app_type", app_type)
        # 决策字段在 analysis.json 写盘之后产生，这里回写一次保持磁盘一致
        _write(output_dir / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2))
        p(f"  决策: {dec['recommendation']} | 市场 {dec['market_opportunity_score']} / 落地 {dec['miniapp_feasibility_score']}"
          + (f" | 阻塞 {len(dec['blocking_reasons'])}" if dec['blocking_reasons'] else ""))
    except Exception as e:
        analysis["recommendation"] = analysis.get("recommendation", "research_only")
        _write(output_dir / "execution-decision.json",
               json.dumps({"recommendation": "research_only", "confidence": 0.0,
                           "reason": f"decision error: {_safe_error(e)}",
                           "blocking_reasons": [], "next_action": "人工复核"},
                          ensure_ascii=False, indent=2))


def _classify_and_write(best_app: dict, output_dir: Path) -> dict:
    """L1 分类：判断 app_type，写 app-classification.json。永不抛异常。"""
    sys.path.insert(0, str(PROJECT_ROOT / "core" / "agents"))
    sys.path.insert(0, str(PROJECT_ROOT / "core"))
    try:
        from classification.classifier import classify_app
        result = classify_app(best_app, use_llm=_use_llm())
    except Exception as e:
        # 分类层本身永不应抛，但兜底：回退到 text_ai
        from capabilities.app_types import get_app_type
        spec = get_app_type("text_ai")
        result = {
            "app_type": "text_ai", "app_type_confidence": 0.3,
            "miniapp_feasibility": spec["default_feasibility"],
            "required_capabilities": list(spec["capabilities"]),
            "blocking_constraints": list(spec["constraints"]),
            "reasons": ["分类异常，回退 text_ai"], "reasoning_summary": "",
            "recommended_platforms": ["wechat"], "llm_used": False,
            "llm_fallback": True, "classify_error": _safe_error(e),
        }
    _write(output_dir / "app-classification.json",
           json.dumps(result, ensure_ascii=False, indent=2))
    return result


def _write_capability_reports(app_type: str, required_caps: list[str],
                              template: str, fallback_used: bool, output_dir: Path) -> dict:
    """L2/L3/L4：写 capability-registry-snapshot / generator-capability-report /
    runtime-capability-status 三个 artifact，返回 runtime 状态字典。永不抛异常。"""
    sys.path.insert(0, str(PROJECT_ROOT / "core"))
    try:
        from capabilities.registry import snapshot, split_configured
        configured, missing = split_configured(required_caps)
        snap = snapshot()
    except Exception as e:
        configured, missing, snap = [], list(required_caps), {"error": _safe_error(e)}

    _write(output_dir / "capability-registry-snapshot.json",
           json.dumps(snap, ensure_ascii=False, indent=2))

    # runnable_level：能力是否齐 → 决定运行等级
    # shell_only < buildable < submit_ready < partially_runtime_ready < runtime_ready
    if not required_caps:
        runnable = "buildable"
    elif not missing:
        runnable = "runtime_ready"          # 全部能力就位
    elif configured:
        runnable = "partially_runtime_ready"  # 部分就位
    else:
        runnable = "buildable"               # 骨架可构建，但能力未接入

    gen_report = {
        "selected_app_type": app_type,
        "selected_template": template,
        "required_capabilities": list(required_caps),
        "configured_capabilities": configured,
        "missing_capabilities": missing,
        "runnable_level": runnable,
        "fallback_used": fallback_used,
    }
    _write(output_dir / "generator-capability-report.json",
           json.dumps(gen_report, ensure_ascii=False, indent=2))

    blocking = [f"能力未接入: {c}" for c in missing]
    runtime = {
        "app_type": app_type,
        "runtime_ready": runnable == "runtime_ready",
        "runnable_level": runnable,
        "configured_capabilities": configured,
        "missing_capabilities": missing,
        "blocking_issues": blocking,
        "warnings": [] if not missing else ["部分能力未配置 provider，生成的小程序可上架但运行能力不完整"],
        "next_action_owner": "human" if missing else "agent",
        "next_action": (f"配置缺失能力 provider: {', '.join(missing)}" if missing
                        else "能力就绪，可接真实运行链路"),
    }
    _write(output_dir / "runtime-capability-status.json",
           json.dumps(runtime, ensure_ascii=False, indent=2))

    # L4 runtime 执行层：写 runtime-execution-report.json（capability_runtime vs app_runtime 诚实区分）
    try:
        from runtime.status import build_execution_report
        exec_report = build_execution_report(app_type)
        _write(output_dir / "runtime-execution-report.json",
               json.dumps(exec_report, ensure_ascii=False, indent=2))
    except Exception as e:
        _write(output_dir / "runtime-execution-report.json",
               json.dumps({"app_type": app_type, "error": _safe_error(e)},
                          ensure_ascii=False, indent=2))
    return runtime


def _apply_llm_demand_analysis(best_app: dict, analysis: dict, output_dir: Path) -> None:
    """路线 B：USE_LLM=true 时调用 LLM 增强需求分析，写 ai-demand-analysis.json，
    并把 llm_used/llm_fallback/ai_summary/ai_analysis_path 写回 analysis（就地修改）。

    设计原则（老板要的"稳定优先"）：
    - USE_LLM=false：标记 llm_used=false，不调 LLM，不生成 ai 文件
    - 成功：写 ai-demand-analysis.json，analysis 带上 ai_summary
    - 失败：标记 llm_fallback=true + 错误，但 pipeline 继续，demand_score 不动
    本函数永不抛异常。
    """
    # 默认值：无论哪条路径，analysis 都带上这组字段，前端/下游字段稳定。
    analysis.setdefault("llm_used", False)
    analysis.setdefault("llm_fallback", False)
    analysis.setdefault("ai_summary", "")
    analysis.setdefault("ai_analysis_path", None)

    # 读 USE_LLM（运行时读，便于测试 monkeypatch settings）
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "core" / "agents"))
        from config import settings
        use_llm = bool(getattr(settings, "USE_LLM", False))
    except Exception:
        use_llm = False

    if not use_llm:
        # USE_LLM=false：生成一个轻量标记文件，明确说明（文档里有约定）
        _write(output_dir / "ai-demand-analysis.json",
               json.dumps({"llm_used": False, "reason": "USE_LLM=false"},
                          ensure_ascii=False, indent=2))
        return

    try:
        from research.demand_llm import run_llm_demand_analysis
        ai = run_llm_demand_analysis(best_app)
        _write(output_dir / "ai-demand-analysis.json",
               json.dumps(ai, ensure_ascii=False, indent=2))
        analysis["llm_used"] = True
        analysis["llm_fallback"] = False
        analysis["ai_summary"] = ai.get("reasoning_summary", "")
        analysis["ai_analysis_path"] = "ai-demand-analysis.json"
        # 用 AI 的解释增强 reasons（保守：只补，不改 demand_score）
        if ai.get("reasoning_summary"):
            analysis.setdefault("reasons", [])
            analysis["reasons"] = list(analysis.get("reasons", [])) + [f"AI: {ai['reasoning_summary']}"]
        p(f"  [LLM] 需求分析完成（model={ai.get('model','')}, confidence={ai.get('confidence',0)}）")
    except Exception as e:
        err = _safe_error(e)
        analysis["llm_used"] = False
        analysis["llm_fallback"] = True
        analysis["ai_summary"] = "LLM failed, fallback to rule-based analysis"
        analysis["ai_analysis_path"] = None
        analysis["llm_error"] = err
        _write(output_dir / "ai-demand-analysis.json",
               json.dumps({"llm_used": False, "llm_fallback": True, "error": err,
                           "reason": "LLM failed, fallback to rule-based analysis"},
                          ensure_ascii=False, indent=2))
        p(f"  [LLM] 调用失败，已 fallback 到规则分析：{err}")


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["demo", "real", "live"], default="demo", help="demo: sample data, real: imported data, live: scrape App Store + Google Play")
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
        # Structured failure event for the web client WS.
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
    step_done("data/inputs/{mode}/apps.json", time.time() - t0)

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

    # --- 路线 B：USE_LLM=true 时用 LLM 增强需求分析（仅补解释，不改 demand_score）---
    # 失败必 fallback 到上面的规则分析，绝不让 pipeline 崩。
    _apply_llm_demand_analysis(best_app, best_analysis, output_dir)

    # --- L1 产品分类：判断 app_type，写 app-classification.json ---
    classification = _classify_and_write(best_app, output_dir)
    app_type = classification["app_type"]
    p(f"  产品类型: {app_type}（{classification['miniapp_feasibility']} 可行性, "
      f"置信度 {classification['app_type_confidence']}）")

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

    # === Step 4.5: 产品决策（成熟需求分析框架）===
    step_header(4, "产品决策分析", "ProductDecisionAgent")
    step_start("product_decision", "产品决策分析", "ProductDecisionAgent")
    t0 = time.time()
    _run_product_decision(best_app, app_type, opportunity, gap, best_analysis, output_dir)
    step_end(artifact="execution-decision.json")
    step_done(f"data/outputs/{job_id}/execution-decision.json", time.time() - t0)

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
    miniapp_dir, gen_source = codegen_agent(best_app, prd_json, gen_dir, app_type=app_type)
    _write(output_dir / "generator-source.json", json.dumps(gen_source, ensure_ascii=False, indent=2))
    file_count = gen_source["generated_files_count"]
    p(f"  项目路径: {miniapp_dir}")
    p(f"  生成文件: {file_count} 个")
    p(f"  模板来源: {gen_source['source']} ({gen_source['template']})")
    # L2/L3/L4：写能力快照 / 生成报告 / 运行状态三个 artifact
    runtime_status = _write_capability_reports(
        app_type=app_type,
        required_caps=classification.get("required_capabilities", []),
        template=gen_source.get("template", app_type),
        fallback_used=gen_source.get("fallback_used", False),
        output_dir=output_dir,
    )
    p(f"  运行能力等级: {runtime_status['runnable_level']}"
      + (f"（缺: {', '.join(runtime_status['missing_capabilities'])}）"
         if runtime_status['missing_capabilities'] else ""))
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

    # === Step 12: Telegram 自动部署 ===
    tg_deploy_result = None
    if "telegram" in opportunity.get("target_platforms", []):
        _tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        _cf_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
        if _tg_token and _cf_token:
            step_header(12, "Telegram 自动部署", "TelegramDeployAgent")
            step_start("telegram_deploy", "Telegram 部署", "TelegramDeployAgent")
            t0 = time.time()
            try:
                # telegram deploy lives in core/publisher
                sys.path.insert(0, str(PROJECT_ROOT / "core" / "publisher"))
                from telegram_deploy import deploy_telegram
                tg_deploy_result = deploy_telegram(job_id, output_dir, best_app, opportunity)
                _write(output_dir / "telegram-deploy.json",
                       json.dumps(tg_deploy_result, ensure_ascii=False, indent=2))
                if tg_deploy_result.get("status") == "deployed":
                    p(f"  ✅ Telegram 部署成功!")
                    p(f"  URL: {tg_deploy_result.get('webapp_url', '')}")
                    p(f"  Bot: {tg_deploy_result.get('bot_link', '')}")
                    step_end(artifact="telegram-deploy.json")
                else:
                    p(f"  ⚠️ 部署状态: {tg_deploy_result.get('status', 'unknown')}")
                    p(f"  原因: {tg_deploy_result.get('reason', tg_deploy_result.get('error', ''))}")
                    step_end(artifact="telegram-deploy.json",
                             error=tg_deploy_result.get("error", "deploy issue"))
            except Exception as e:
                p(f"  ❌ Telegram 部署失败: {e}")
                tg_deploy_result = {"status": "error", "error": str(e)}
                _write(output_dir / "telegram-deploy.json",
                       json.dumps(tg_deploy_result, ensure_ascii=False, indent=2))
                step_end(artifact="telegram-deploy.json", error=str(e))
            step_done(f"data/outputs/{job_id}/telegram-deploy.json", time.time() - t0)
        else:
            p(f"\n  [Telegram] 跳过自动部署（未配置 TELEGRAM_BOT_TOKEN 或 CLOUDFLARE_API_TOKEN）")

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
    if tg_deploy_result and tg_deploy_result.get("status") == "deployed":
        p(f"  ✅ Telegram 已自动上线: {tg_deploy_result.get('bot_link', '')}")
        p(f"  1. 阅读 prd.md 确认产品方案")
        p(f"  2. 微信/支付宝/抖音如需上架，阅读 human-actions.md")
    else:
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
