# 数据流说明

一次任务从输入数据开始，按 pipeline 步骤（step）逐步生成一组产物。

```text
输入 App 数据
  -> candidate.json
  -> analysis.json
  -> gap-check.json
  -> viral-score.json
  -> template-selection.json
  -> opportunity-report.json
  -> prd.md / prd.json
  -> generated/miniapp/        (含 dist/build/mp-weixin、docs/*)
  -> listing-materials.md / listing-materials.json
  -> growth-plan.md / share-strategy.md
  -> publish-package/          (各平台提交材料) + submit-status.json
  -> qa-report.json
  -> growth-qa-report.json / compliance-qa-report.json
  -> submission-readiness-report.json
  -> artifact-manifest.json
  -> pipeline-report.json / pipeline.log
```

| 文件 | 作用 | 真源能力域 |
|---|---|---|
| `candidate.json` | 本次选中的候选 App，后续分析都基于它 | opportunity |
| `analysis.json` | 需求强度分析结果 | opportunity |
| `gap-check.json` | 小程序平台缺口检查结果 | opportunity |
| `viral-score.json` | 传播力评分（8 维度，参与机会决策） | opportunity |
| `template-selection.json` | 题材归类与选中的模板类型 | opportunity |
| `opportunity-report.json` | 综合机会评分（Viral Score 为核心维度，权重 0.25） | opportunity |
| `prd.md` / `prd.json` | 产品需求文档，人看 md，机器用 json | generator |
| `generated/miniapp/` | 自动生成的 uni-app 工程 + dist 构建产物 + 法务 docs | generator |
| `listing-materials.*` | 上架文案、关键词、隐私/审核说明 | publisher |
| `growth-plan.md` / `share-strategy.md` | 增长计划与分享/裂变策略 | growth |
| `publish-package/` + `submit-status.json` | 各平台提交材料包与状态 | publisher + platforms |
| `qa-report.json` | 工程构建与质检结果 | qa |
| `growth-qa-report.json` / `compliance-qa-report.json` | 增长产物与合规材料质检 | qa |
| `submission-readiness-report.json` | 是否可提交审核、阻塞项是什么 | qa |
| `artifact-manifest.json` | 各产物用途/状态/下一步（供 UI） | runtime |
| `pipeline-report.json` | 每个 step 的状态、耗时、产物（主字段 `step` / `capability`） | runtime |
| `pipeline.log` | 运行日志，排查失败原因 | runtime |

> 运行时协议：`pipeline-report.json` 的每个步骤只使用 `step` / `capability` 两个标识字段，
> 不输出 `agent` 字段。前后端、报告、事件流均以 `step` / `capability` 为唯一口径。
