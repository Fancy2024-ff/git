# core/growth — 增长与裂变策略

## 职责
- 生成增长计划 `growth-plan.md`（`planner.py`）
- 生成分享策略 `share-strategy.md`（`share_strategy.py`）
- 分享钩子、激励策略、去水印/去广告建议、裂变传播路径设计

## 模块
- `planner.py` — `build_growth_plan(app, viral, selection)` → growth-plan.md 正文
- `share_strategy.py` — `build_share_strategy(app, viral, selection)` → share-strategy.md 正文

## 落点规则
- growth-plan / 裂变策略 → 这里
- 分享策略 / 激励设计 → 这里
- 当前为规则版 v1，后续可由 LLM 按真实题材细化（LLM 走 core/integrations）
