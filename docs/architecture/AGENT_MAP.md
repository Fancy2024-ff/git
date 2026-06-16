# Agent Map

本系统由 9 个 Agent 组成，按顺序执行。

| # | Agent | 作用 | 输入 | 输出 | 文件位置 | 实现方式 |
|---|-------|------|------|------|----------|----------|
| 1 | MarketInputAgent | 读取候选 App 数据 | apps.json | apps list | core/pipeline/runner.py:market_input_agent | 文件读取 |
| 2 | DemandAnalysisAgent | 评估需求强度 | app dict | demand_score | core/pipeline/runner.py:demand_analysis_agent | 规则评分 |
| 3 | GapCheckAgent | 检查小程序平台覆盖 | app + platform-registry | gap report | core/pipeline/runner.py:gap_check_agent | 规则 + 百度搜索 |
| 4 | OpportunityScoreAgent | 5维度综合评分 | app + analysis + gap | opportunity report | core/pipeline/runner.py:opportunity_score_agent | 规则评分 |
| 5 | PRDAgent | 生成产品需求文档 | app + opportunity | prd.md + prd.json | core/pipeline/runner.py:prd_agent | 模板填充 |
| 6 | CodegenAgent | 生成小程序代码 | prd + templates | miniapp project | core/pipeline/runner.py:codegen_agent | 模板复制 + 定制 |
| 7 | PublishMaterialsAgent | 生成上架材料 | app + prd | listing materials | core/pipeline/runner.py:publish_materials_agent | 模板填充 |
| 8 | PublishPackageAgent | 生成提交审核包 | all above | publish-package/ | core/pipeline/runner.py (inline) | 文件组织 |
| 9 | QACheckAgent | 构建验证 + 质检 | miniapp dir | qa-report.json | core/pipeline/runner.py:qa_check_agent | npm build + 检查 |

## 重要说明

当前主链路 `core/pipeline/runner.py` 主要使用 **规则 + 模板** 实现。

LLM Agent 文件已存在于 `core/agents/` 目录（使用 LangChain + Claude API），但尚未完全接入主链路：
- core/agents/discovery/agent.py — LLM 驱动的 Discovery Agent
- core/agents/research/agent.py — LLM 驱动的 Research Agent
- core/agents/coding/agent.py — LLM 增强的 Coding Agent
- core/agents/qa/agent.py — 增强版 QA Agent
- core/agents/publisher/agent.py — Publisher Agent
- core/agents/review/agent.py — Review Agent

接入 LLM 需要配置 ANTHROPIC_API_KEY。
