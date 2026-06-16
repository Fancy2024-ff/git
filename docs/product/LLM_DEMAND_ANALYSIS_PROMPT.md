# LLM 需求分析 Prompt（路线 B · 第 2 步）

> 本文档与 `core/agents/research/demand_llm.py` 保持同步。
> 改 prompt / 改输出结构，先改代码再回来更新本文档。

## 1. 目标

当 `USE_LLM=true` 时，流水线第 2 步（需求分析）在规则评分之外，额外调用 LLM
对选中的 App 做**可解释的需求分析**，产出 `ai-demand-analysis.json`。

它回答的是老板那几个问题：
- 这个 App 的需求怎么来的？目标用户、痛点、核心需求是什么？
- 哪些功能能做成小程序，哪些不能，做不了的有什么替代方案？
- 小程序首版（MVP）该做哪些？
- 风险在哪？AI 自己有多大把握（confidence）？

## 2. 输入字段（喂给 LLM）

来自 `candidate`（选中的 App）：
`name` / `name_cn` / `source` / `category` / `description` / `description_cn` /
`downloads` / `rating` / `review_count` / `features` / `monetization`

## 3. 输出 JSON schema（固定）

```json
{
  "llm_used": true,
  "model": "claude-opus-4.8",
  "app_name": "",
  "source": "",
  "reasoning_summary": "一句话：为什么值得/不值得做成小程序",
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
  "confidence": 0.0
}
```

缺字段由 `demand_llm.SCHEMA_DEFAULTS` 补默认值；非 JSON 输出由 `_extract_json` 尝试抠取，
仍失败则抛异常 → 调用方 fallback 到规则分析。

## 4. Prompt 原文

System（见 `demand_llm._SYSTEM_PROMPT`）要求 LLM：
- 只输出 JSON，不要 Markdown / ```json 代码块 / 多余解释
- 不要编造下载量、评分（只用输入给的数字）
- 不确定的写进 `risk_notes`，不要硬编
- 区分 `replicable_features`（小程序可复刻）与 `non_replicable_features`（不适合/做不了）
- 对做不了的功能在 `workaround_features` 给替代方案
- `miniapp_mvp_scope` 给首版最小范围
- `confidence` 是 0-1 的置信度
- 考虑小程序限制：包体积 2-20MB、后台执行受限、平台 API 差异、部分平台无推送、本地存储有限

Human（见 `demand_llm._build_user_prompt`）把上面的输入字段拼进去，并重申输出键列表。

## 5. 分析不准 / 想改，改哪里？

| 想改什么 | 改哪里 |
|---|---|
| AI 怎么分析（措辞、侧重） | `core/agents/research/demand_llm.py` → `_SYSTEM_PROMPT` |
| 喂给 AI 的输入字段 | `demand_llm.py` → `_build_user_prompt` |
| 输出结构 / 字段 | `demand_llm.py` → `SCHEMA_DEFAULTS` + `_normalize` |
| 换模型 / 中转站 | `.env` 的 `LLM_MODEL` / `ANTHROPIC_BASE_URL` |
| 开关 AI | `.env` 的 `USE_LLM`（true/false） |

## 6. USE_LLM=false 时的规则兜底在哪？

- 规则版需求分析：`core/pipeline/runner.py` → `demand_analysis_agent`（多维度加权评分）
- 第 2 步永远先跑规则分析得到稳定 `demand_score`；`USE_LLM=true` 只是在其之上**追加** AI 解释，
  不改 `demand_score`。
- `USE_LLM=true` 但 LLM 失败 → `analysis.json` 标记 `llm_fallback=true`，pipeline 继续，
  下游 QA/构建不受影响。
