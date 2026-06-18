# core/runtime — 运行时基础设施

## 职责
job context、artifact writer、配置、持久化、路径、日志、错误模型等运行时基础设施。
不含业务规则。

## 模块
- `config.py` — 全局配置单一事实源（路径/密钥/外部服务地址）
- `context.py` — `JobContext` 一次 pipeline run 的运行上下文
- `artifacts.py` — 统一产物写盘 + 产物文件名常量（含新产物位 viral-score/template-selection/growth-plan/share-strategy）
- `database.py` — 流水线状态持久化（JSON + 文件锁）

## 落点规则
- job context / artifacts / logging / path / config → 这里
- 持久化 / 状态存储 → 这里
