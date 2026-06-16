# Prompt & Rules 说明

## 当前实现方式

主链路 `core/pipeline/runner.py` 使用本地规则，不依赖 LLM。

## 需求分析规则 (DemandAnalysisAgent)

位置: `core/pipeline/runner.py:demand_analysis_agent`

评分维度:
- 下载量 (0-30): >5M=30, >2M=25, >500K=18, >100K=12, else=5
- 评分 (0-20): rating * 4.2
- 评论数 (0-15): >10K=15, >3K=12, >500=8, else=4
- 变现验证 (0-15): subscription/freemium=15, paid=12, else=5
- 功能丰富度 (0-10): features.length * 2
- 更新频率 (固定10)

如果评分不准，改这个函数里的阈值和权重。

## 机会评分规则 (OpportunityScoreAgent)

位置: `core/pipeline/runner.py:opportunity_score_agent`

5维度:
- demand (25%): 来自 DemandAnalysis
- gap (25%): 缺失平台数 / 总平台数 * 100
- fit (20%): 是否轻工具 + 短流程 + 不依赖原生能力
- implementation (15%): 页面越少越高，支付-15，复杂-20
- risk (15%): 默认85，敏感品类降到45-50

如果评分不准，改权重 `weights` dict 或各维度的阈值。

## 覆盖检查规则 (GapCheckAgent)

位置: `core/pipeline/runner.py:gap_check_agent`

逻辑:
- 读取 platform-registry.json 中 status=active 的平台
- 对每个平台用本地规则判断覆盖（微信>5M下载=weak, 否则=missing）
- 检查产品类型是否匹配平台 fit_product_types

如果覆盖判断不准，需要接入真实搜索API。当前微信用搜狗搜索，支付宝/抖音用百度搜索代理。

## 代码生成模板 (CodegenAgent)

位置: `core/pipeline/runner.py:codegen_agent`
模板: `core/generator/src/templates/base/` + `core/generator/src/templates/ai-tool/`

逻辑:
1. 从 core/generator/src/templates/base 复制基础骨架
2. 从 core/generator/src/templates/ai-tool 复制功能页面
3. 定制 package.json (name, description)
4. 定制 manifest.json (appid, name)
5. 定制 pages.json (页面注册)
6. 生成 index.vue (应用名, 功能列表)
7. 生成 form.vue, result.vue, profile.vue (定制化)

如果代码不对，改模板文件或 codegen_agent 里的定制逻辑。

## LLM Agent（未接入主链路）

core/agents/ 目录下的 Agent 使用 LangChain + Claude API:
- core/agents/discovery/agent.py — 用 LLM 推荐 App + 评估
- core/agents/research/agent.py — 用 LLM 分析功能 + 生成 PRD
- core/agents/coding/agent.py — 用 LLM 增强页面代码

接入方式:
1. 配置 ANTHROPIC_API_KEY
2. 修改 core/pipeline/runner.py 对应步骤调用 core/agents/ 下的函数
3. 或切换到 core/agents/orchestrator/pipeline.py (LangGraph 版本)

## USE_LLM 开关（已接入：第 2 步需求分析）

`USE_LLM=true` 时，流水线第 2 步在规则评分之外，额外调用 LLM 生成可解释的需求分析
（`ai-demand-analysis.json`：目标用户/痛点/可复刻功能/不可复刻功能/MVP 范围/风险/置信度）。

- 默认 `USE_LLM=false`：只走规则分析（`demand_analysis_agent`），demo 离线稳定。
- `USE_LLM=true` 但 LLM 失败：自动 fallback 到规则分析，`analysis.json` 标记 `llm_fallback=true`，
  pipeline 不中断，下游 QA/构建不受影响。
- Prompt 原文与“分析不准改哪里”：见 [LLM_DEMAND_ANALYSIS_PROMPT.md](LLM_DEMAND_ANALYSIS_PROMPT.md)。
- 实现：`core/agents/research/demand_llm.py`（prompt+schema）、`core/pipeline/runner.py` → `_apply_llm_demand_analysis`。
