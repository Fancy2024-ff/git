# 历史报告归档

本目录为**历史审查 / 日报归档**，可能包含重构前的旧路径（例如 `dashboard/`、`agents/server.py`、`scripts/run_demo_pipeline.py`、`generator/src/templates`、`agents/steps`、根目录下的 `Dockerfile.*` 等）。

这些文档记录的是当时的状态快照，**不作为当前架构说明**。当前架构以以下文档为准：

- 根目录 [README.md](../../README.md)
- [docs/architecture/CODE_STRUCTURE.md](../architecture/CODE_STRUCTURE.md)
- [docs/architecture/AGENT_MAP.md](../architecture/AGENT_MAP.md)
- [docs/product/PROMPT_AND_RULES.md](../product/PROMPT_AND_RULES.md)

当前架构关键路径速查：

| 用途 | 当前路径 |
|------|----------|
| 后端 API | `apps/api/main.py` |
| 前端 | `apps/web/` |
| 主流水线 | `core/pipeline/runner.py` |
| Node 生成器 | `core/generator/` |
| Agent / 共享逻辑 | `core/agents/` |
| 代码模板 | `core/generator/src/templates/`（base / ai-tool / ai-chat / ai-image） |
| Dockerfile | `infra/docker/Dockerfile.api` / `.generator` / `.web` |
| demo 输入 | `data/inputs/demo/apps.json` |
| 真实输入 | `data/inputs/real/apps.json` |
| 产物输出 | `data/outputs/{jobId}/` |
