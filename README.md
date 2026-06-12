# Mini App Factory

Agent 驱动的小程序批量生产系统。自动发现 App Store / Google Play 上已验证的 AI 应用需求，识别小程序生态供给缺口，生成产品方案、代码、上架材料。

## 当前 MVP 已跑通

- 一条命令完成 9 步流水线闭环
- 从 5 个候选 App 中自动选择最优机会
- 自动生成 PRD、uni-app 小程序代码、上架材料、人工操作指南
- 自动执行 npm install + npm run build:mp-weixin
- QA 自动验证构建产物
- 生成的 dist/build/mp-weixin 可直接导入微信开发者工具

## 快速开始

### 运行 Demo Pipeline

```bash
python scripts/run_demo_pipeline.py
```

执行后生成：
```
data/outputs/{jobId}/
  candidate.json          - 选中的候选 App
  analysis.json           - 需求分析
  gap-check.json          - 覆盖检查
  opportunity-report.json - 机会评分
  prd.md                  - 产品文档
  prd.json                - 结构化 PRD
  listing-materials.md    - 上架材料
  listing-materials.json  - 上架材料（结构化）
  human-actions.md        - 人工操作指南
  qa-report.json          - 质量检查报告
  generated/miniapp/      - 小程序项目代码
    dist/build/mp-weixin/ - 构建产物（可导入微信开发者工具）
```

### 启动后端 API

```bash
cd agents
pip install -e .
python server.py
```

后端运行在 http://localhost:8000

### 启动前端 Dashboard

```bash
cd dashboard
npm install
npm run dev
```

前端运行在 http://localhost:5173

### 用微信开发者工具导入

1. 打开微信开发者工具
2. 选择"导入项目"
3. 目录选择：`data/outputs/{jobId}/generated/miniapp/dist/build/mp-weixin`
4. 填入 AppID（或使用测试号）
5. 即可预览和调试

## 项目结构

```
miniapp-factory/
  scripts/
    run_demo_pipeline.py    - MVP 演示流水线（核心入口）
  agents/
    server.py               - FastAPI 后端
    config/settings.py      - 配置
    shared/                 - 数据模型、LLM 封装
    discovery/              - 发现 Agent
    research/               - 分析 Agent
    coding/                 - 代码生成 Agent
    qa/                     - 质检 Agent
    publisher/              - 上架 Agent
    review/                 - 复盘 Agent
    orchestrator/           - LangGraph 流水线
  dashboard/                - Vue 3 前端
  generator/                - Node.js 代码生成服务
  data/
    samples/apps.json       - 候选 App 数据
    outputs/                - 每次运行的产物
```

## 环境要求

- Python 3.11+
- Node.js 18+
- npm

## 当前限制

- 候选 App 数据来自本地 JSON，未接真实 App Store API
- 评分逻辑使用本地规则，未接 LLM
- 代码生成使用模板骨架，未接 LLM 智能增强
- 上架为人工操作，系统只生成材料和指南
- 前端 Dashboard 展示真实 job 数据，但未做实时 WebSocket 推送

## TODO

- [ ] 接入七麦 / SensorTower API 获取真实排行榜数据
- [ ] 接入 Claude API 替换本地评分规则
- [ ] LLM 驱动的代码增强（更智能的页面逻辑）
- [ ] 审核结果回填 + 自动复盘迭代
- [ ] miniprogram-ci 自动上传（替代手动上架）
- [ ] 前端 WebSocket 实时日志推送
