"""LLM 需求分析（路线 B，第 2 步增强）。

目标：让"需求是怎么分析出来的"可解释、可追溯、可修改。
- prompt 原文见 docs/product/LLM_DEMAND_ANALYSIS_PROMPT.md（与本文件保持同步）
- 失败时由调用方 fallback 到规则版 demand_analysis_agent，绝不让 pipeline 崩
- 输出 schema 固定，缺字段补默认值，非 JSON 时抛错交给 fallback

改这里 = 改"AI 怎么分析需求"：
- 改 prompt → _build_prompt()
- 改输出结构 → SCHEMA_DEFAULTS / _normalize()
"""

import json
import re

# 固定输出 schema 与默认值。LLM 缺字段时用这些兜底，保证下游字段稳定。
SCHEMA_DEFAULTS: dict = {
    "reasoning_summary": "",
    "target_users": [],
    "user_pain_points": [],
    "core_needs": [],
    "usage_scenarios": [],
    "replicable_features": [],
    "non_replicable_features": [],
    "workaround_features": [],
    "miniapp_mvp_scope": [],
    "monetization_insights": [],
    "risk_notes": [],
    "confidence": 0.0,
}

_SYSTEM_PROMPT = """你是资深产品经理，专精移动 App 与小程序（微信/支付宝/抖音/Telegram）。
你的任务：分析给定 App，判断它做成小程序的需求是否成立、首版该做什么。

严格遵守：
- 只输出 JSON，不要 Markdown，不要 ```json 代码块，不要任何多余解释。
- 不要编造下载量、评分等数字；只能基于我给你的输入。
- 不确定的判断写进 risk_notes，不要硬编。
- 必须区分"小程序可复刻的功能"(replicable_features) 与"小程序不适合/做不了的功能"(non_replicable_features)。
- 对做不了的功能，在 workaround_features 给替代方案。
- miniapp_mvp_scope 给出首版最小范围（别堆功能）。
- confidence 是你对本次分析的置信度，0-1 的小数。

考虑小程序限制：包体积 2-20MB、后台执行受限、平台 API 差异、部分平台无推送、本地存储有限。"""

_OUTPUT_KEYS_HINT = """输出 JSON，键固定为：
reasoning_summary(一句话说明为什么这个 App 值得/不值得做成小程序),
target_users[], user_pain_points[], core_needs[], usage_scenarios[],
replicable_features[], non_replicable_features[], workaround_features[],
miniapp_mvp_scope[], monetization_insights[], risk_notes[], confidence(0-1 小数)。"""


def _build_user_prompt(app: dict) -> str:
    return f"""分析这个 App，判断做成小程序的需求与首版范围：

名称(EN): {app.get('name', '')}
名称(CN): {app.get('name_cn', '')}
来源: {app.get('source', '')}
分类: {app.get('category', '')}
描述(EN): {app.get('description', '')}
描述(CN): {app.get('description_cn', '')}
下载量: {app.get('downloads', 0)}
评分: {app.get('rating', 0)}
评论数: {app.get('review_count', 0)}
功能: {', '.join(app.get('features', []) or app.get('features_cn', []))}
变现: {app.get('monetization', '')}

{_OUTPUT_KEYS_HINT}"""


def _extract_json(text: str) -> dict:
    """从 LLM 文本里抠出 JSON。容忍 ```json 包裹和首尾杂字符。"""
    s = text.strip()
    # 去掉可能的代码块围栏
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError):
        # 退一步：抓第一个 { 到最后一个 } 之间
        start, end = s.find("{"), s.rfind("}")
        if start >= 0 and end > start:
            return json.loads(s[start:end + 1])
        raise


def _normalize(raw: dict) -> dict:
    """按固定 schema 补默认值，类型不对则纠正。"""
    out = dict(SCHEMA_DEFAULTS)
    for key, default in SCHEMA_DEFAULTS.items():
        val = raw.get(key, default)
        if isinstance(default, list):
            out[key] = val if isinstance(val, list) else ([val] if val else [])
        elif isinstance(default, float):
            try:
                out[key] = float(val)
            except (TypeError, ValueError):
                out[key] = 0.0
        else:
            out[key] = val if isinstance(val, str) else (str(val) if val is not None else "")
    return out


def run_llm_demand_analysis(app: dict) -> dict:
    """调用 LLM 做需求分析，返回符合 schema 的结构化结果。

    复用 shared.llm.get_llm（读 settings 里的 key/base_url/model）。
    任何失败都向上抛，由调用方 fallback —— 本函数不吞异常。
    """
    from shared.llm import get_llm  # 延迟导入，避免 USE_LLM=false 时引入 langchain
    from config.settings import LLM_MODEL

    llm = get_llm(max_tokens=2048)
    messages = [
        ("system", _SYSTEM_PROMPT),
        ("human", _build_user_prompt(app)),
    ]
    resp = llm.invoke(messages)
    content = resp.content if hasattr(resp, "content") else str(resp)
    if isinstance(content, list):  # 某些客户端返回 content blocks
        content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)

    result = _normalize(_extract_json(content))
    result["llm_used"] = True
    result["model"] = LLM_MODEL
    result["app_name"] = app.get("name", "")
    result["source"] = app.get("source", "")
    return result
