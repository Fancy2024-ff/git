# [历史文档] 需求分析与小程序生成器汇报说明（已归档）

> 🗄️ **历史文档，不代表当前架构和当前代码位置。**
> 本文引用的 `demand_analysis_agent()` / `prd_agent()` / `codegen_agent()` /
> `agents/research/agent.py` 等命名已废弃。当前真源：需求→`core/opportunity/demand_analysis.py`，
> PRD→`core/generator/prd_builder.py`，生成→`core/generator/codegen.py`。
> 当前权威说明见 `docs/architecture/STEP_CAPABILITY_MAP.md` 与各 `core/<域>/README.md`。

---

这份文档用于老板汇报和项目验收，重点回答三个问题：需求怎么判断、规则和 prompt 在哪里、小程序代码怎么生成。

## 一句话汇报

这个项目不是单纯做页面，而是一个 Agent 驱动的小程序生产工厂：先从 App Store / Google Play 或人工导入的数据里找到高需求 App，再判断这些需求在国内外小程序平台是否覆盖不足，最后自动生成 PRD、小程序代码、构建产物、QA 报告和上架材料。

## 需求分析模块怎么讲

需求分析不是拍脑袋选 App，而是把一个 App 拆成可量化指标，再由 Agent 自动评分。

当前主流程会看这些指标：

1. 下载量：证明市场规模，下载越高，说明需求越被验证。
2. 评分：证明用户满意度，评分低说明可能有体验问题。
3. 评论数：证明用户反馈活跃度，评论越多越容易挖需求。
4. 变现方式：订阅、付费、内购说明商业价值更清楚。
5. 功能复杂度：判断能不能做成轻量小程序。
6. 小程序适配度：判断是否适合即用即走、短流程、轻工具场景。
7. 平台缺口：判断微信、支付宝、抖音、Telegram、LINE 等国内外小程序平台有没有同类覆盖。
8. 风险：判断是否涉及医疗、金融、版权、隐私、审核敏感类目。

最终不是只看需求大不大，而是看：需求强 + 小程序平台缺口大 + 能轻量实现 + 审核风险可控。

## 老板问：需求怎么确定是真的？

可以这样回答：

当前 MVP 阶段先用规则评分保证流程稳定，主要依据下载量、评分、评论数、变现方式、功能复杂度和平台覆盖缺口。后续生产阶段会接入真实 App Store / Google Play 数据、评论挖掘、竞品搜索和 LLM 分析，把规则评分升级成真实数据驱动的机会判断。

## 老板问：是不是抄 App？

可以这样回答：

不是抄 App。系统提取的是已经被市场验证的用户需求和使用场景，再判断这个需求是否适合小程序形态，最后生成一个小程序版本的 PRD 和实现方案。重点是需求迁移，不是复制原 App 的代码、品牌和素材。

## 老板问：如果分析错了，改哪里？

可以这样回答：

分析错了不是改前端页面，而是按 Agent 分层定位：

- 需求强度不准：改 `core/pipeline/runner.py` 里的 `demand_analysis_agent()`。
- 平台缺口不准：改 `core/pipeline/runner.py` 里的 `gap_check_agent()`，以及 `data/platforms/platform-registry.json`。
- 综合机会分不准：改 `core/pipeline/runner.py` 里的 `opportunity_score_agent()`。
- PRD 内容不准：改 `core/pipeline/runner.py` 里的 `prd_agent()`，后续可接 `agents/research/agent.py` 的 LLM prompt。

## Prompt / 规则在哪里

当前主链路主要是规则和模板驱动，不是完全依赖 LLM prompt。这样做的好处是稳定、可复现、方便排查。

核心位置：

| 内容 | 位置 | 作用 |
|---|---|---|
| 主流水线 | `core/pipeline/runner.py` | 串起所有 Agent 步骤 |
| 需求评分规则 | `core/pipeline/runner.py:demand_analysis_agent()` | 给 App 打需求分 |
| 平台缺口规则 | `core/pipeline/runner.py:gap_check_agent()` | 判断国内外小程序平台覆盖情况 |
| 机会评分规则 | `core/pipeline/runner.py:opportunity_score_agent()` | 综合需求、缺口、适配度、实现难度、风险 |
| PRD 模板 | `core/pipeline/runner.py:prd_agent()` | 生成 `prd.md` 和 `prd.json` |
| 小程序生成逻辑 | `core/pipeline/runner.py:codegen_agent()` | 根据 PRD 生成 uni-app 项目 |
| 小程序模板 | `core/generator/src/templates/` | 存放 uni-app 基础模板和页面模板 |
| Agent 说明 | `apps/web/src/data/agentDefinitions.ts` | 前端展示每个 Agent 的输入、输出、规则位置 |
| 平台库 | `data/platforms/platform-registry.json` | 国内外小程序/Mini App 平台配置 |
| 每次产物 | `data/outputs/{jobId}/` | 保存分析、PRD、代码、QA、上架材料 |

补充说明：`docs/PROMPT_AND_RULES.md` 是规则说明文档，但当前本地文件存在中文乱码风险，汇报时优先以这份文档和代码位置为准，并要求后续修复该文档编码。

## 小程序生成器模块怎么讲

小程序生成器的作用是把 PRD 变成可构建的小程序工程。

流程是：

1. `prd_agent()` 生成结构化 `prd.json`。
2. `codegen_agent()` 读取 `prd.json`。
3. 从 `core/generator/src/templates/` 复制 uni-app 基础骨架。
4. 根据产品名称、功能点、页面结构生成页面代码和配置。
5. 输出到 `data/outputs/{jobId}/generated/miniapp/`。
6. QA Agent 自动执行 `npm install` 和 `npm run build:mp-weixin`。
7. 构建成功后生成 `dist/build/mp-weixin/`，可用微信开发者工具导入。

## 老板问：小程序生成器做到什么程度了？

可以这样回答：

小程序生成器在 MVP 阶段完成度比较高，已经不是只生成静态文件，而是能生成 uni-app 项目、自动安装依赖、自动执行微信小程序构建，并产出 dist 目录。连续多个 job 的 QA、install、build 都通过，说明生成器的工程链路是跑通的。

但生产级还没有完全结束，因为现在生成的功能更偏模板化，后续还要补真实业务 API、登录、支付、更多平台适配、截图生成和自动上传。

## 两个重点模块完成度判断

### 需求分析模块

结论：MVP 可用，但还不能说生产完成度很高。

当前完成度：约 70% 到 75%。

已经完成：

- 能读取候选 App 数据。
- 能按规则计算需求分。
- 能做小程序平台缺口判断。
- 能输出 `analysis.json`、`gap-check.json`、`opportunity-report.json`。
- 能把分析结果继续传给 PRD 和代码生成。

还差：

- 真实 App Store / Google Play 数据自动采集。
- 真实评论挖掘和用户痛点总结。
- 真实小程序竞品搜索证据。
- LLM 需求分析 prompt 接入主链路。
- 评分权重需要用更多真实案例校准。

汇报口径：需求分析已经能支撑 MVP 跑通，但生产准确性还要靠真实数据源和 LLM 分析增强。

### 小程序生成器模块

结论：MVP 完成度较高，是当前项目里相对最扎实的模块之一。

当前完成度：约 85%。

已经完成：

- 能生成 uni-app 小程序工程。
- 能生成页面、配置、依赖和构建脚本。
- 能自动 `npm install`。
- 能自动 `npm run build:mp-weixin`。
- 能生成 `dist/build/mp-weixin/`。
- QA 报告里能记录 `build_verified=true` 和 `build_passed=true`。

还差：

- 页面功能还偏模板化。
- 缺少真实后端 API 接入。
- 登录、支付、订阅、用户数据还没做成通用模块。
- 多平台适配还需要从微信扩展到支付宝、抖音、Telegram、LINE 等。
- 自动上传微信需要接 `miniprogram-ci` 和平台密钥。

汇报口径：生成器链路已经跑通且稳定性较好，是“先跑通”阶段的核心成果；下一阶段重点是从模板生成升级成更丰富的业务生成。

## 汇报时最重要的一段话

老板，我现在重点讲两个核心模块：需求分析和小程序生成器。需求分析负责判断“该不该做”，它根据 App 市场数据、小程序平台缺口、实现难度和风险做机会评分；小程序生成器负责判断“能不能自动做出来”，它根据 PRD 和模板生成 uni-app 项目，并自动构建出微信小程序 dist 产物。目前生成器完成度更高，已经能稳定构建；需求分析已经能跑通 MVP，但生产准确性还需要继续接真实数据源、评论分析和 LLM prompt。

## 下一步给 Claude 的要求

1. 修复 `docs/PROMPT_AND_RULES.md` 中文乱码，保证 UTF-8。
2. 把 `core/pipeline/runner.py` 中需求分析、机会评分、小程序生成器的规则拆成独立文档。
3. 在前端 Agent 说明页展示每个 Agent 的代码位置、规则位置、输入文件、输出文件。
4. 增加一个“规则解释”面板，让老板能直接看到每个评分为什么这么打。
5. 让每次 job 产物里增加 `rule-explanation.md`，说明本次为什么选中这个 App、为什么推荐这些平台、为什么能生成小程序。
