# core/opportunity — 机会发现 + 评分决策

## 职责
- 机会发现（App Store / Google Play 抓取 → `scrapers/`）
- 题材归类与模板类型选择（`classifier.py` → template-selection.json）
- Opportunity Score 机会评分（`scoring.py` → opportunity-report.json）
- Viral Score 传播力评分（`viral_score.py` → viral-score.json）
- 回答"该做什么方向、先做哪个"

## 模块
- `scrapers/` — 外部榜单抓取（appstore / googleplay / miniprogram）
- `scoring.py` — `compute_opportunity_score(app, analysis, gap, viral)`，6 维度机会评分（Viral Score 为核心维度，权重 0.25）
- `viral_score.py` — `compute_viral_score(app, opportunity)`，8 维度传播力评分
- `classifier.py` — `classify(app, viral)`，题材归类 + 选模板

## 落点规则
- 传播机会判断 / Opportunity / Viral Score → 这里
- 题材归类、"先做哪个" → 这里
- 新增数据源 → `scrapers/`
