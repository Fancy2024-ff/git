# Mini App Factory

Agent 驱动的小程序批量生产系统。自动发现 App Store / Google Play 上已验证的 AI 应用需求，识别小程序生态供给缺口，生成产品方案、代码、上架材料。

## 当前 MVP 已跑通

- 一条命令完成 10+ 步流水线闭环
- 从 5 个候选 App 中自动选择最优机会
- 自动生成 PRD、uni-app 小程序代码、上架材料、人工操作指南
- 自动执行 npm install + npm run build:mp-weixin
- QA 自动验证构建产物（文件完整性、乱码检测、路径校验、构建验证）
- 生成的 dist/build/mp-weixin 可直接导入微信开发者工具
- WebSocket 实时日志推送（per-job 路由 + 指数退避重连）
- API 全链路认证（常量时间比较、路径穿越防御）
- 35 个自动化测试覆盖核心路径（agents 26 + web 4 + generator 5）

## 快速开始

### 运行 Demo Pipeline

```bash
python core/pipeline/runner.py
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
  pipeline.log            - Pipeline 运行日志
  generated/miniapp/      - 小程序项目代码
    dist/build/mp-weixin/ - 构建产物（可导入微信开发者工具）
```

### 启动后端 API

```bash
pip install -e core/agents/[dev]
python apps/api/main.py
```

后端运行在 http://localhost:8000

### 启动前端 Dashboard

```bash
cd apps/web
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
  apps/                       - 对外应用层
    api/main.py               - FastAPI 后端（认证、WS、Pipeline 管理）
    web/                      - Vue 3 前端（WS 实时推送）
  core/                       - 核心业务逻辑
    pipeline/runner.py        - MVP 演示流水线（核心入口，规则+模板）
    agents/                   - LLM Agent 模块 + 共享代码
      config/settings.py      - 配置
      shared/                 - 数据模型、LLM 封装、数据库
      discovery/              - 发现 Agent（去重、gap 检测）
      research/               - 分析 Agent
      coding/                 - 代码生成 Agent
      qa/                     - 质检 Agent（src/ 路径校验）
      publisher/              - 上架 Agent
      review/                 - 复盘 Agent
      orchestrator/           - LangGraph 编排（可选 LLM 链路）
      run_pipeline.py         - LangGraph 链路入口（需 langgraph + API key）
      tests/                  - pytest 测试套件（26 cases）
        manual/               - LLM 手动冒烟脚本（需 API key，不参与 CI）
    generator/                - Node.js 代码生成服务（生产鉴权）
    publisher/                - Telegram 自动上架
  infra/docker/               - 三个 Dockerfile
  data/
    inputs/demo/apps.json     - demo 候选 App 数据
    inputs/real/apps.json     - 真实导入数据
    platforms/                - 平台注册表
    outputs/                  - 每次运行的产物
```

## Docker 部署（推荐）

```bash
cp .env.example .env
# 编辑 .env，必须设置：
#   DASHBOARD_API_KEY — API 认证密钥
#   GENERATOR_API_KEY — Generator 服务认证密钥
#   ANTHROPIC_API_KEY — LLM 调用密钥（可选，demo 模式不需要）
docker compose up --build
```

三个服务自动编排：
- API (FastAPI): http://localhost:8000
- Generator (Node.js): http://localhost:3100
- Web Dashboard (nginx): http://localhost:5173

停止：`docker compose down`

**Docker 验证状态：Dockerfile 与 compose 已静态校验（路径、lockfile、端口、healthcheck 全部对齐当前架构），但尚未在本仓库的开发机上实跑 `docker compose build`（该机器未安装 Docker）。** 待在装有 Docker 的环境按 [docs/deployment/DOCKER_VERIFY.md](docs/deployment/DOCKER_VERIFY.md) 实测确认。

- infra/docker/Dockerfile.api（Python 3.11 + Node.js 22）
- infra/docker/Dockerfile.generator（node:22-slim multi-stage）
- infra/docker/Dockerfile.web（node:22-slim build + nginx:alpine runtime）
- 三个服务：api / generator / web
- web healthcheck 使用 `127.0.0.1`（Alpine 兼容）

已知部署风险：
- `VITE_API_TOKEN` 通过 build-arg 烘焙进前端 JS bundle。内部 MVP 可接受，对外生产应改为 runtime config（nginx 提供 `/config.json`）或后端 session 方案。
- 更换 API key 需要重新 build web 镜像。

## 环境要求（本地开发）

- Python 3.11+
- Node.js 18+
- npm
- Docker（可选，用于容器化部署）

## 运行测试

```bash
# 后端 (core/agents) — 26 cases
cd core/agents
pip install -e ".[dev]"
pytest tests/ -q

# 前端 (apps/web) — 4 cases
cd apps/web
npm test -- --run

# Generator (core/generator) — 5 cases
cd core/generator
npm test -- --run
```

## 安全特性

- API Key 认证（POST + 敏感 GET 路由）
- WebSocket token 校验（query param）
- 常量时间比较防 timing attack
- 路径穿越防御
- CORS 限定 origin
- HTTP 安全头（X-Content-Type-Options, X-Frame-Options, Cache-Control）
- 生产环境强制要求密钥配置
- Graceful shutdown（SIGTERM 清理子进程）

## 已知限制（设计取舍，非 Bug）

- **单 worker + 全局状态** — 同时只能运行一个 Pipeline，不支持水平扩展
- **JSON 文件数据库** — MVP 级别，并发写受 filelock 约束
- **LLM Agent 无单元测试** — 需要 mock LLM 调用，属于下一阶段
- **Vue 组件零测试** — 14 个组件无 render/interaction test
- **core/pipeline/runner.py 约 2000 行** — 与 core/agents/ 逻辑有重复，重构需整体规划
- **WebSocket token 在 query string** — 浏览器 WS API 限制，已文档化
- **Scraper 使用搜狗/百度作为代理** — 准确率有限，短名称(≤3字符)跳过

## TODO

- [ ] 接入七麦 / SensorTower API 获取真实排行榜数据
- [ ] 接入 Claude API 替换本地评分规则
- [ ] LLM 驱动的代码增强（更智能的页面逻辑）
- [ ] 审核结果回填 + 自动复盘迭代
- [x] miniprogram-ci 微信开发版上传（已接通，见 docs/product/WECHAT_UPLOAD_INTEGRATION.md；自动提审仍待做）
- [ ] 任务队列替换子进程模型（支持并发 Pipeline）
- [ ] SQLite/PostgreSQL 替换 JSON 文件数据库
- [ ] Rate limiting
- [ ] Vue 组件测试 + E2E 测试
