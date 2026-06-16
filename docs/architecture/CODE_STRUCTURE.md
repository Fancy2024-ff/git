# Code Structure

## 项目结构

```
miniapp-factory/
├── apps/                          ← 对外应用层
│   ├── api/main.py                ← FastAPI 后端 API（认证、WS、Pipeline 管理）
│   └── web/                       ← Vue 3 前端
│       └── src/
│           ├── App.vue            ← 主页面
│           ├── services/api.ts    ← API 客户端
│           └── components/        ← UI 组件
│
├── core/                          ← 核心业务逻辑
│   ├── pipeline/runner.py         ← 主入口（9-step pipeline，规则+模板）
│   ├── agents/                    ← LLM Agent 层（LangChain, 待完全接入）
│   │   ├── config/settings.py     ← 配置
│   │   ├── shared/                ← 模型、数据库、LLM 封装
│   │   ├── discovery/             ← 发现 Agent + 爬虫
│   │   ├── research/              ← 分析 Agent
│   │   ├── coding/                ← 代码生成 Agent
│   │   ├── qa/                    ← 质检 Agent
│   │   ├── publisher/             ← 上架 Agent
│   │   ├── review/                ← 复盘 Agent
│   │   ├── orchestrator/          ← LangGraph 流水线
│   │   ├── run_pipeline.py        ← LangGraph 链路入口（需 langgraph + API key）
│   │   └── tests/                 ← pytest 测试套件
│   │       └── manual/            ← LLM 手动冒烟脚本（需 API key）
│   ├── generator/                 ← 代码生成模板
│   │   └── src/templates/         ← base / ai-tool / ai-chat / ai-image
│   └── publisher/                 ← Telegram 自动上架
│
├── infra/docker/                  ← Dockerfile.api / .generator / .web
│
├── data/
│   ├── inputs/demo/apps.json      ← demo 样例数据
│   ├── inputs/real/               ← 真实导入数据
│   ├── platforms/                 ← 平台库
│   ├── platform-auth/             ← 平台授权配置
│   └── outputs/                   ← 每次运行的产物
│
└── docs/                          ← 文档
    ├── architecture/              ← AGENT_MAP / CODE_STRUCTURE / 生产架构
    ├── product/                   ← 评分规则 / 平台调研
    ├── operation/                 ← 上架自动化规划
    └── reports/                   ← 审计与计划归档
```

## 主要入口

| 场景 | 命令 | 说明 |
|------|------|------|
| 运行 pipeline | `python core/pipeline/runner.py --mode demo` | 样例数据 |
| 运行 pipeline | `python core/pipeline/runner.py --mode real` | 真实数据 |
| 启动后端 | `python apps/api/main.py` | FastAPI on :8000 |
| 启动前端 | `cd apps/web && npm run dev` | Vite on :5173 |

## 数据流

```
apps.json → MarketInput → DemandAnalysis → GapCheck → OpportunityScore
  → PRDAgent → CodegenAgent → PublishMaterials → PublishPackage → QA
  → data/outputs/{jobId}/
      candidate.json
      analysis.json
      gap-check.json
      opportunity-report.json
      prd.md / prd.json
      generated/miniapp/ (可 build)
      listing-materials.md / .json
      publish-package/
      submit-status.json
      qa-report.json
      pipeline-report.json
      generator-source.json
```
