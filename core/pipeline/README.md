# core/pipeline — 编排层

## 职责
**只负责编排**：step sequencing、状态流转、上下文传递、产物调度、pipeline 报告。
不承载重业务规则。

## 边界（重要）
runner.py 只允许做：
- step 编排与顺序
- 调用 `core/*` 各域能力（opportunity / generator / growth / qa / publisher）
- 组装参数、传递 JobContext、写 pipeline 报告

runner.py **不允许**内嵌：
- 评分规则（→ core/opportunity/scoring.py、viral_score.py）
- 题材归类/模板选择（→ core/opportunity/classifier.py）
- 增长策略正文（→ core/growth）
- QA 细节（→ core/qa）
- 小程序骨架/模板（→ core/generator，唯一生成真源）

## 产物（含新产物位）
prd / code / qa / listing + viral-score.json / template-selection.json /
growth-plan.md / share-strategy.md（文件名常量见 core/runtime/artifacts.py）
