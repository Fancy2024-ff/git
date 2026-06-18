# 步骤 / 能力域分工图（Step / Capability Map）

> 系统按**能力域 + pipeline 步骤（step）**组织，不是 Agent 架构。
> `core/pipeline/runner.py` 只编排（step 顺序、日志、报告），业务规则在 `core/<域>`。
> 运行时协议只使用 `step` / `capability`，不再输出 `agent` 字段。
> "真源（改这里）"指向当前代码中真实存在的模块。

| 步骤 | capability | 作用 | 真源（改这里） |
|---|---|---|---|
| 1 | MarketInput | 读取输入并选择候选 App | `core/pipeline/runner.py:load_market_input`（编排）；实时抓取 `core/opportunity/scrapers/` |
| 2 | DemandAnalysis | 分析需求强度并选出最优候选（demand×0.6 + viral×0.4） | `core/opportunity/demand_analysis.py` |
| 3 | GapCheck | 检查平台缺口 | `core/opportunity/gap_analysis.py` |
| 4 | ViralScore | 传播力评分（8 维度）+ 题材归类/选模板 | `core/opportunity/viral_score.py` / `classifier.py` → viral-score.json / template-selection.json |
| 5 | OpportunityScore | 综合机会评分（Viral Score 为核心维度，权重 0.25） | `core/opportunity/scoring.py` |
| 6 | PRD | 生成 PRD | `core/generator/prd_builder.py` |
| 7 | Codegen | 生成小程序代码 | `core/generator/codegen.py`（唯一执行真源）+ `core/generator/src/templates/`（模板事实源） |
| 8 | PublishMaterials | 生成上架材料 | `core/publisher/materials.py` |
| 9 | Growth | 增长 + 分享策略 | `core/growth/planner.py` / `share_strategy.py` → growth-plan.md / share-strategy.md |
| 10 | PublishPackage | 生成平台提交包 | `core/publisher/package_builder.py` + `core/platforms/guides.py` |
| 11 | EngineeringQA | 工程构建质检（build/dist/编码/关键页） | `core/qa/engineering_qa.py` |
| 12 | GrowthComplianceQA | 增长 QA（含生成代码传播链路扫描）+ 合规 QA（含敏感词扫描） | `core/qa/growth_qa.py` / `compliance_qa.py` |
| 13 | Readiness | 提交就绪评估 | `core/qa/readiness.py` |
| 14（可选） | TelegramDeploy | Telegram 自动部署 | `core/publisher/telegram_deploy.py` |

## 架构落点规则
- 传播机会判断 / Opportunity / Viral Score → `core/opportunity`
- 新模板类型 / 模板选择 → `core/generator`（生成执行真源 `core/generator/codegen.py`）
- growth-plan / 分享 / 激励 → `core/growth`
- 工程 build 检查 / 裂变位检查 / 合规检查 → `core/qa`（合规平台细则 → `core/platforms`）
- 图像/视频/LLM 接口 → `core/integrations`
- job context / artifacts / logging / config → `core/runtime`
- 公共 schema / types / constants → `core/shared`

> `agents/` 与 `core/agents/` 已在能力域重构中删除。旧版「Agent 分工图」已归档于
> `docs/archive/AGENT_MAP.legacy.md`。
