# Agent Map

本系统由 9 个 Agent 组成，按顺序执行。

| # | Agent | 作用 | 输入 | 输出 | 文件位置 | 实现方式 |
|---|-------|------|------|------|----------|----------|
| 1 | MarketInputAgent | 读取候选 App 数据 | apps.json | apps list | scripts/run_demo_pipeline.py:market_input_agent | 文件读取 |
| 2 | DemandAnalysisAgent | 评估需求强度 | app dict | demand_score | scripts/run_demo_pipeline.py:demand_analysis_agent | 规则评分 |
| 3 | GapCheckAgent | 检查小程序平台覆盖 | app + platform-registry | gap report | scripts/run_demo_pipeline.py:gap_check_agent | 规则 + 百度搜索 |
| 4 | OpportunityScoreAgent | 5维度综合评分 | app + analysis + gap | opportunity report | scripts/run_demo_pipeline.py:opportunity_score_agent | 规则评分 |
| 5 | PRDAgent | 生成产品需求文档 | app + opportunity | prd.md + prd.json | scripts/run_demo_pipeline.py:prd_agent | 模板填充 |
| 6 | CodegenAgent | 生成小程序代码 | prd + templates | miniapp project | scripts/run_demo_pipeline.py:codegen_agent | 模板复制 + 定制 |
| 7 | PublishMaterialsAgent | 生成上架材料 | app + prd | listing materials | scripts/run_demo_pipeline.py:publish_materials_agent | 模板填充 |
| 8 | PublishPackageAgent | 生成提交审核包 | all above | publish-package/ | scripts/run_demo_pipeline.py (inline) | 文件组织 |
| 9 | QACheckAgent | 构建验证 + 质检 | miniapp dir | qa-report.json | scripts/run_demo_pipeline.py:qa_check_agent | npm build + 检查 |

## 重要说明

当前主链路 `scripts/run_demo_pipeline.py` 主要使用 **规则 + 模板** 实现。

LLM Agent 文件已存在于 `agents/` 目录（使用 LangChain + Claude API），但尚未完全接入主链路：
- agents/discovery/agent.py — LLM 驱动的 Discovery Agent
- agents/research/agent.py — LLM 驱动的 Research Agent
- agents/coding/agent.py — LLM 增强的 Coding Agent
- agents/qa/agent.py — 增强版 QA Agent
- agents/publisher/agent.py — Publisher Agent
- agents/review/agent.py — Review Agent

接入 LLM 需要配置 ANTHROPIC_API_KEY。
