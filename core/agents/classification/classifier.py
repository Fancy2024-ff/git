"""产品分类层（L1）：判断热门 App 属于 6 类中的哪一类。

- USE_LLM=false：纯规则分类（classify_by_rules）
- USE_LLM=true：LLM 分类 + 解释；失败自动 fallback 到规则，绝不中断 pipeline
产出 app-classification.json。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 让 capabilities 包可导入（core/ 加入 path）
_CORE = Path(__file__).resolve().parent.parent.parent  # core/agents/classification → core
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from capabilities.app_types import (  # noqa: E402
    classify_by_rules, APP_TYPES, VALID_APP_TYPES, get_app_type,
)


def _recommended_platforms(app_type: str) -> list[str]:
    """按类型给推荐平台（保守默认；真实推荐仍以 gap-check 为准）。"""
    base = ["wechat"]
    if app_type in ("text_ai", "utility_tool"):
        return ["wechat", "alipay", "douyin"]
    if app_type == "image_ai":
        return ["wechat", "douyin"]
    if app_type in ("ocr_scan", "speech_ai"):
        return ["wechat", "alipay"]
    if app_type == "video_light":
        return ["douyin", "wechat"]
    return base


def _rule_classification(app: dict) -> dict:
    r = classify_by_rules(app)
    r["recommended_platforms"] = _recommended_platforms(r["app_type"])
    r["llm_used"] = False
    r["llm_fallback"] = False
    r["app_name"] = app.get("name", "")
    r["reasoning_summary"] = r["reasons"][0] if r.get("reasons") else ""
    return r


def _llm_classification(app: dict) -> dict:
    """用 LLM 分类。只在 USE_LLM=true 时调用；失败由 classify_app 兜底。"""
    from shared.llm import get_llm
    from config.settings import LLM_MODEL

    types_desc = "\n".join(f"- {k}: {v['name_cn']}（{','.join(v['keywords'][:4])}…）"
                           for k, v in APP_TYPES.items())
    system = f"""你是产品架构师。把给定 App 分到下面 6 类之一，并判断它做成小程序是否可行。
可选类型：
{types_desc}

只输出 JSON，不要 Markdown，不要解释。字段：
app_type(必须是 {VALID_APP_TYPES} 之一),
app_type_confidence(0-1 小数),
miniapp_feasibility(high/medium/low),
reasoning_summary(一句话：为什么是这类、适不适合小程序),
reasons(字符串数组),
blocking_constraints(字符串数组，小程序限制)。"""
    human = f"""App:
名称: {app.get('name','')} / {app.get('name_cn','')}
分类: {app.get('category','')}
描述: {app.get('description','')} {app.get('description_cn','')}
功能: {', '.join(app.get('features', []) or app.get('features_cn', []))}"""

    llm = get_llm(max_tokens=1024)
    resp = llm.invoke([("system", system), ("human", human)])
    content = resp.content if hasattr(resp, "content") else str(resp)
    if isinstance(content, list):
        content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)

    s = content.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    try:
        raw = json.loads(s)
    except (json.JSONDecodeError, ValueError):
        start, end = s.find("{"), s.rfind("}")
        raw = json.loads(s[start:end + 1])

    app_type = raw.get("app_type")
    if app_type not in VALID_APP_TYPES:
        raise ValueError(f"LLM 返回非法 app_type: {app_type}")

    spec = get_app_type(app_type)
    return {
        "app_type": app_type,
        "app_type_confidence": float(raw.get("app_type_confidence", 0.7)),
        "miniapp_feasibility": raw.get("miniapp_feasibility", spec["default_feasibility"]),
        "required_capabilities": list(spec["capabilities"]),  # 能力由类型决定，不让 LLM 编
        "blocking_constraints": raw.get("blocking_constraints", list(spec["constraints"])),
        "reasons": raw.get("reasons", []),
        "reasoning_summary": raw.get("reasoning_summary", ""),
        "recommended_platforms": _recommended_platforms(app_type),
        "matched_keywords": [],
        "llm_used": True,
        "llm_fallback": False,
        "model": LLM_MODEL,
        "app_name": app.get("name", ""),
    }


def classify_app(app: dict, use_llm: bool = False) -> dict:
    """对外入口。返回 app-classification.json 的内容字典。永不抛异常。"""
    if not use_llm:
        return _rule_classification(app)
    try:
        return _llm_classification(app)
    except Exception as e:
        result = _rule_classification(app)
        result["llm_used"] = False
        result["llm_fallback"] = True
        result["llm_error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return result
