# Dashboard 重构计划：交互式管理后台

## 需求总结

不是一个展示用 PPT，而是一个**能操作、能看到每一步真实数据**的管理后台。

老板视角：
- 我从哪里获取的数据？→ 数据源管理页，能看到 App Store/Google Play 的采集配置和结果
- 发现了什么机会？→ 机会列表，每一个 app 的 8 问评估详情都能展开看
- PRD 长什么样？→ 点进去看完整 PRD 内容，功能列表、用户场景、技术方案
- 代码生成了什么？→ 项目文件树 + 代码预览 + 下载 zip
- 上架到哪了？→ 每个平台的提交状态、审核进度
- 整体怎么样？→ Dashboard 首页看汇总数据和运行中的任务

## 架构

```
┌─────────────────────────────────────────────────┐
│  Vue 3 SPA (Vite + Vue Router + Pinia)          │
│  dashboard/                                      │
│  - 首页 Overview                                 │
│  - 数据源管理                                     │
│  - 机会列表 + 8问评估详情                          │
│  - PRD 详情页                                     │
│  - 项目管理（代码预览/下载）                        │
│  - Pipeline 控制台（触发/停止/日志）               │
└──────────────────────┬──────────────────────────┘
                       │ HTTP REST API
┌──────────────────────▼──────────────────────────┐
│  FastAPI Backend (agents/server.py)              │
│  - GET  /api/opportunities → 机会列表           │
│  - GET  /api/opportunities/:id → 8问评估详情     │
│  - GET  /api/projects → 项目列表                │
│  - GET  /api/projects/:id → 项目详情+文件树      │
│  - GET  /api/projects/:id/files/:path → 文件内容│
│  - GET  /api/prds/:id → PRD 详情                │
│  - POST /api/pipeline/start → 启动流水线        │
│  - POST /api/pipeline/stop → 停止               │
│  - GET  /api/pipeline/status → 当前状态+日志     │
│  - GET  /api/sources → 数据源配置               │
│  - POST /api/sources → 更新数据源               │
│  - WS   /ws/pipeline → 实时日志推送             │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Existing Agent Layer (已有代码)                  │
│  discovery / research / coding / qa / publisher  │
└─────────────────────────────────────────────────┘
```

## 前端页面结构

```
dashboard/
├── index.html
├── package.json
├── vite.config.ts
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── router/index.ts
│   ├── stores/
│   │   ├── pipeline.ts      # 流水线状态
│   │   └── projects.ts      # 项目数据
│   ├── api/index.ts          # HTTP 客户端
│   ├── views/
│   │   ├── Overview.vue      # 首页：汇总 + 实时状态
│   │   ├── Sources.vue       # 数据源管理
│   │   ├── Opportunities.vue # 机会列表
│   │   ├── OpportunityDetail.vue  # 8问评估详情
│   │   ├── Projects.vue      # 项目列表
│   │   ├── ProjectDetail.vue # 代码预览 + 文件树 + 下载
│   │   ├── PRDDetail.vue     # PRD 完整内容
│   │   └── Pipeline.vue      # 控制台：触发/日志/停止
│   ├── components/
│   │   ├── AppNav.vue
│   │   ├── StatsCard.vue
│   │   ├── PipelineTrack.vue
│   │   ├── LogConsole.vue
│   │   ├── FileTree.vue
│   │   └── CodePreview.vue
│   └── styles/
│       └── main.css          # Apple-style 全局样式
```

## 后端 API 层

新增 `agents/server.py` — 基于 FastAPI，暴露 REST API + WebSocket：

- 需要安装: `fastapi`, `uvicorn`, `websockets`
- 读取现有 `shared/database.py` 的 JSON 数据
- 读取 `data/` 目录下的 PRD、项目文件
- Pipeline 启动通过 subprocess 在后台跑，日志通过 WebSocket 实时推

## 实现步骤（按优先级）

### Phase 1: Backend API (先让数据能通过 HTTP 访问)
1. `agents/server.py` — FastAPI 主文件
2. `agents/api/routes.py` — 路由定义
3. 添加 `fastapi`, `uvicorn` 到 pyproject.toml

### Phase 2: Vue 3 前端骨架
1. Vite + Vue 3 + Vue Router + Pinia 初始化
2. Apple-style 全局样式 (基于之前的设计语言)
3. AppNav 导航 + 路由配置

### Phase 3: 核心页面实现
1. Overview — 统计卡片 + 实时 Pipeline 状态
2. Pipeline — 触发按钮 + 实时日志 (WebSocket)
3. Opportunities — 列表 + 8问评估展开
4. Projects — 列表 + 文件树 + 代码预览
5. PRD Detail — 完整 PRD 渲染
6. Sources — 数据源 CRUD

### Phase 4: 联调
1. 前后端联调
2. WebSocket 实时日志
3. 文件下载 (zip)
