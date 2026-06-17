"""需求分析框架（规则驱动的 8 维度分析）。

主体规则驱动：USE_LLM=false 也能产出完整决策。输入候选 App + app_type + opportunity + gap +
capability snapshot，输出各维度结构化结果。LLM 仅作可选增强（见 agent.py）。

核心判断（回应 Canva 类）：平台型/复杂编辑产品 → miniapp_fit 低 → 不可 immediate_execute。
"""

from __future__ import annotations

# 复杂画布/编辑类信号词（命中→不适合小程序轻交互闭环）
_COMPLEX_KEYWORDS = [
    "canvas", "画布", "editor", "编辑器", "timeline", "时间轴", "layer", "图层",
    "drag", "拖拽", "design", "设计", "video edit", "视频剪辑", "剪辑", "3d",
    "matting", "多轨", "工程文件",
]
# 平台型信号词（大而全）
_PLATFORM_KEYWORDS = ["platform", "平台", "all-in-one", "suite", "全能", "工作室", "studio", "套件"]
# 品牌/商标风险词（知名品牌名直接做小程序有商标风险）
_BRAND_KEYWORDS = [
    "canva", "photoshop", "figma", "capcut", "剪映", "notion", "chatgpt", "midjourney",
    "office", "wps", "adobe", "tiktok", "instagram",
]


def _text_blob(app: dict) -> str:
    return " ".join([
        str(app.get("name", "")), str(app.get("name_cn", "")), str(app.get("category", "")),
        str(app.get("description", "")), str(app.get("description_cn", "")),
        " ".join(app.get("features", []) or []), " ".join(app.get("features_cn", []) or []),
    ]).lower()


def _hits(blob: str, words: list[str]) -> list[str]:
    return [w for w in words if w.lower() in blob]


def analyze_market_demand(app: dict, opportunity: dict) -> dict:
    downloads = app.get("downloads", 0) or 0
    rating = app.get("rating", 0) or 0
    demand_score = opportunity.get("demand_score", 0)
    gap_score = opportunity.get("miniapp_gap_score", 0)
    freq = "high" if downloads > 2_000_000 else "medium" if downloads > 300_000 else "low"
    comp = "high" if gap_score < 30 else "medium" if gap_score < 70 else "low"
    # market_opportunity = 需求 + 缺口 的加权（市场维度，不含落地性）
    market_score = round(min(100, demand_score * 0.6 + gap_score * 0.4), 1)
    return {
        "pain_point_frequency": freq,
        "long_term": downloads > 500_000,
        "trend_sustainable": "热度可持续" if downloads > 1_000_000 else "需进一步验证",
        "competition_level": comp,
        "evidence": [f"下载量 {downloads:,}", f"评分 {rating}", f"需求分 {demand_score}", f"缺口分 {gap_score}"],
        "_market_opportunity_score": market_score,
    }


def analyze_scenario_granularity(app: dict) -> dict:
    blob = _text_blob(app)
    features = app.get("features", []) or app.get("features_cn", []) or []
    is_platform = bool(_hits(blob, _PLATFORM_KEYWORDS)) or len(features) > 6
    is_complex = bool(_hits(blob, _COMPLEX_KEYWORDS))
    product_type = "platform" if is_platform else ("tool" if not is_complex else "tool")
    # 平台型/复杂 → 可拆但不可原样；纯工具 → 可直接裁 MVP
    splittable = is_platform or is_complex
    steps = 4 if is_platform else (3 if is_complex else 2)
    return {
        "product_type": "platform" if is_platform else "tool",
        "splittable_to_mvp": splittable,
        "steps_to_core_task": steps,
        "notes": ("平台型/大而全，需拆成垂直子场景" if is_platform
                  else "含复杂编辑能力，建议聚焦单任务" if is_complex
                  else "工具型，可直接裁成单任务 MVP"),
        "_is_platform": is_platform,
        "_is_complex": is_complex,
    }


def analyze_miniapp_fit(app: dict, scenario: dict) -> dict:
    is_complex = scenario.get("_is_complex")
    is_platform = scenario.get("_is_platform")
    needs_canvas = bool(is_complex)
    # fit 评分：复杂画布/平台型显著降分
    score = 80
    if needs_canvas:
        score -= 40
    if is_platform:
        score -= 25
    score = max(10, min(100, score))
    return {
        "light_interaction": not needs_canvas,
        "short_flow": not is_platform,
        "needs_complex_canvas": needs_canvas,
        "closed_loop_in_miniapp": not (needs_canvas or is_platform),
        "score": score,
    }


def analyze_capability_feasibility(app_type: str, cap_snapshot: dict) -> dict:
    required = cap_snapshot.get("required_capabilities", [])
    configured = cap_snapshot.get("configured_capabilities", [])
    missing = cap_snapshot.get("missing_capabilities", [])
    level = cap_snapshot.get("runnable_level", "buildable")
    supported = bool(required) and not missing
    notes = ("能力齐备" if supported
             else f"缺能力 provider: {', '.join(missing)}" if missing
             else "无所需能力声明")
    return {
        "required_capabilities": required,
        "configured_capabilities": configured,
        "missing_capabilities": missing,
        "runnable_level_estimate": level,
        "supported": supported,
        "notes": notes,
    }


def analyze_generation_feasibility(app_type: str, cap_feas: dict) -> dict:
    supported = cap_feas.get("supported")
    missing = cap_feas.get("missing_capabilities", [])
    likely_shell = not supported
    risks = []
    if missing:
        risks.append(f"缺 provider，生成后运行能力不完整: {', '.join(missing)}")
    if likely_shell:
        risks.append("生成大概率为可上架空壳，runtime 未接通")
    return {
        "template_available": True,   # 6 类模板均有目录（base + app_type）
        "runtime_supported": supported,
        "likely_shell_only": likely_shell,
        "risks": risks,
    }


def analyze_compliance_review_risk(app: dict) -> dict:
    blob = _text_blob(app)
    brand_hits = _hits(blob, _BRAND_KEYWORDS)
    brand_risk = 80 if brand_hits else 20
    category = (app.get("category", "") or "").lower()
    content_hits = any(k in blob or k in category for k in
                       ["health", "medical", "finance", "gambling", "dating", "医疗", "金融", "赌"])
    review_risk = 70 if content_hits else 30
    return {
        "brand_risk_score": brand_risk,
        "review_risk_score": review_risk,
        "naming_brand_risk": (f"含知名品牌词({', '.join(brand_hits)})，直接命名有商标风险" if brand_hits
                              else "无明显品牌冲突"),
        "content_risk": "涉敏感行业，审核严格" if content_hits else "内容风险低",
        "privacy_risk": "如收集用户输入/图片，需隐私说明" ,
        "wechat_review_friendly": "需规避品牌词与敏感内容" if (brand_hits or content_hits) else "较友好",
    }


def analyze_business_competition(app: dict, market: dict) -> dict:
    monetization = app.get("monetization", "")
    fit = []
    if monetization in ("subscription", "freemium"):
        fit += ["subscription", "credits"]
    fit.append("one_time")
    if market.get("competition_level") == "low":
        fit.append("lead_gen")
    return {
        "monetization_fit": fit,
        "miniapp_differentiation": "即用即走、免下载，适合轻量高频场景",
        "worth_grabbing_gap": market.get("competition_level") in ("low", "medium"),
    }
