# 老板汇报口径

现在项目已经整理成清晰的能力域（capability-domain）架构：

- `apps/web` 是前端控制台，用来看任务进度、各步骤产物、机会/传播力评分和提交状态。
- `apps/api` 是后端统一入口，负责启动流水线、提供任务数据、推送实时日志。
- `core/pipeline` 是核心生产线，只负责按步骤（step）编排，业务逻辑在各能力域。
- `core/opportunity` 负责机会发现、Viral Score（传播力评分）和题材/模板选择。
- `core/generator` 是小程序代码生成器和模板库（唯一生成执行真源）。
- `core/growth` 产出增长计划与分享/裂变策略；`core/qa` 做工程/增长/合规三层质检。
- `core/publisher` 是平台发布能力，微信、Telegram 等自动上传放这里。
- `data/outputs/{jobId}` 是每次运行产物。

架构已收口为能力域终态：后端唯一入口 `apps/api`、流水线唯一入口 `core/pipeline/runner.py`、
代码生成唯一真源 `core/generator/codegen.py`，没有 Agent 架构层，也没有双入口/双路径。
