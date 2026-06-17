# 需求分析决策框架（Demand Analysis Framework）

> 需求分析已从"单一需求分 + 几句泛分析"升级为成熟产品决策框架。
> 实现：`core/agents/research/`（schemas / framework / decision / product_research / artifacts）。
> 主体**规则驱动**（USE_LLM=false 也产出完整决策），LLM 仅可选增强。

## 1. 不只是"需求分"

旧版只回答"热门 App 值不值得做"，新版回答：产品需求是否真实 → 是否适合小程序形态 →
能否裁成可执行 MVP → 当前 capabilities/generator/runtime 能否支撑 → 审核/品牌风险 →
最终给出可执行建议。

## 2. 八个分析维度

1. **Market Demand** 市场需求（痛点频率/长期性/趋势/竞争）
2. **Scenario Granularity** 场景颗粒度（平台型 vs 工具型 / 可否裁 MVP / 几步完成核心任务）
3. **Miniapp Fit** 小程序适配度（轻交互/短链路/是否依赖复杂画布·时间轴·图层/能否闭环）
4. **Capability Feasibility** 能力可实现性（所需能力 / 已配置 / 缺失 / runnable_level 预估）
5. **Generation Feasibility** 生成可行性（模板可选/runtime 支撑/是否大概率空壳/风险）
6. **Compliance & Review Risk** 合规与审核风险（品牌/商标/内容/隐私/微信友好度）
7. **Business & Competition** 商业与竞争（变现适配/差异化/是否值得抢空白）
8. **Execution Recommendation** 执行建议

## 3. 双总分 + 决策门槛

不再只给一个总分，拆成两类：
- **market_opportunity_score**：市场机会（需求 + 缺口）
- **miniapp_feasibility_score**：小程序落地性（fit + 场景颗粒度 + 能力可实现性 + 生成可行性）

外加 brand_risk_score / review_risk_score / execution_confidence。

门槛（`decision.py`）：
- feasibility < 50 → **禁 immediate_execute**
- market 高 + feasibility 中 → split_then_execute / research_only
- market & feasibility 都高 + 无高风险 → immediate_execute
- market 低 → reject / research_only
- 高品牌/审核风险（≥70）→ 一律不得 immediate_execute

recommendation ∈ {immediate_execute, split_then_execute, research_only, reject}。

## 4. 为什么"热门 ≠ 适合直接小程序化"

热门只决定 market_opportunity_score。能不能做成可用小程序由 miniapp_feasibility_score 决定
（轻交互/能力支撑/非复杂画布）。两者分开后，高市场+低落地的产品会被正确导向"拆分"而非"立即执行"。

## 5. 如何处理 Canva 这类平台型产品

Canva：平台型（功能数多）+ 复杂画布/图层/时间轴 + image 能力缺 provider + 品牌词 →
- market_opportunity_score 高（≈94）
- miniapp_feasibility_score 低（≈0，复杂画布 + 缺 provider）
- brand_risk 高（含 "canva" 品牌词）
- **recommendation = split_then_execute**（非 immediate_execute）
- mvp-split-plan 推荐垂直 MVP（如"证件照/一键抠图"），标注不可迁移功能（多图层/时间轴）+ 替代方案

## 6. 功能拆解 + MVP 裁剪（mvp-split-plan.json）

original_product_summary / core_feature_breakdown / replicable_features /
non_replicable_features / substitution_strategies / recommended_mvp(name/app_type/capabilities/first_version_scope/reason)。

## 7. 与 capabilities 联动

基于 app_type → `registry.build_capability_snapshot` → required/configured/missing →
capability_feasibility 维度真实反映；缺 provider（image/video）→ generation_feasibility.likely_shell_only=true，
不给虚高 runtime_ready，也不会给 immediate_execute。

## 8. 产出 artifacts

| 文件 | 内容 |
|---|---|
| demand-analysis.json | 市场需求/用户/场景/竞品/价值 + market_opportunity_score |
| miniapp-feasibility-report.json | 适配/能力依赖/生成可行性/runtime/审核风险 + miniapp_feasibility_score |
| mvp-split-plan.json | 拆分方案 / replicable / non_replicable / substitution / recommended_mvp |
| execution-decision.json | recommendation / confidence / 双总分 / 风险分 / blocking_reasons / next_action |
| demand-analysis.md | 给老板/产品看的摘要 |

兼容现有 analysis.json：回写 market_opportunity_score / miniapp_feasibility_score /
recommendation / execution_confidence / blocking_reasons / recommended_mvp_name / recommended_app_type。

## 9. 前端展示

总览页决策区展示：执行建议（含色调）、market vs feasibility 双分、推荐 MVP、阻塞项、下一步。
不再让前端只显示一个"机会评分"就给"适合立即上架"的错觉。

## 当前未完成项

- 默认规则驱动；LLM 增强目前仅补 reasoning 文字，未让 LLM 重算 8 维度评分。
- substitution_strategies / recommended_mvp 为规则模板化产出，未做深度领域定制。
