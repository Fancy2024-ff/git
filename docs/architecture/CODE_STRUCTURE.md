# Code Structure

## 项目结构

```
miniapp-factory/
├── scripts/
│   └── run_demo_pipeline.py      ← 主入口（9-step pipeline）
│
├── agents/                        ← LLM Agent 层（LangChain, 待完全接入）
│   ├── server.py                  ← FastAPI 后端 API
│   ├── config/settings.py         ← 配置
│   ├── shared/                    ← 模型、数据库、LLM 封装
│   ├── discovery/                 ← 发现 Agent + 爬虫
│   ├── research/                  ← 分析 Agent
│   ├── coding/                    ← 代码生成 Agent
│   ├── qa/                        ← 质检 Agent
│   ├── publisher/                 ← 上架 Agent
│   ├── review/                    ← 复盘 Agent
│   └── orchestrator/              ← LangGraph 流水线
│
├── generator/                     ← 代码生成模板
│   ├── src/templates/base/        ← uni-app 基础骨架
│   ├── src/templates/ai-tool/     ← AI 工具类页面
│   ├── src/templates/ai-chat/     ← AI 对话类页面
│   └── src/templates/ai-image/    ← AI 图片类页面
│
├── dashboard/                     ← Vue 3 前端
│   └── src/
│       ├── App.vue                ← 主页面
│       ├── services/api.ts        ← API 客户端
│       └── components/            ← UI 组件
│
├── data/
│   ├── samples/apps.json          ← 样例数据
│   ├── real_inputs/               ← 真实导入数据
│   ├── platforms/                 ← 平台库
│   ├── platform-auth/             ← 平台授权配置
│   └── outputs/                   ← 每次运行的产物
│
└── docs/                          ← 文档
    ├── AGENT_MAP.md               ← Agent 说明
    ├── PROMPT_AND_RULES.md        ← 评分规则
    ├── production-architecture.md ← 生产架构
    └── publish-automation-plan.md ← 上架自动化规划
```

## 主要入口

| 场景 | 命令 | 说明 |
|------|------|------|
| 运行 pipeline | `python scripts/run_demo_pipeline.py --mode demo` | 样例数据 |
| 运行 pipeline | `python scripts/run_demo_pipeline.py --mode real` | 真实数据 |
| 启动后端 | `cd agents && python server.py` | FastAPI on :8000 |
| 启动前端 | `cd dashboard && npm run dev` | Vite on :5173 |

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
