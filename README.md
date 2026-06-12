# 🏭 Mini-program Factory

AI Agent 驱动的小程序批量生产工厂 —— 自动发现 App Store 上有但小程序平台缺失的 AI 应用机会，生成 PRD，编写代码，提交上架。

## 架构

```
Discovery Agent → Research Agent → Coding Agent → Publisher Agent
    (找机会)        (出 PRD)        (生成代码)       (提交审核)
```

- **Agent 编排层**: Python + LangChain/LangGraph
- **代码生成层**: Node.js + uni-app 模板
- **LLM**: Claude (Anthropic API)

## 快速开始

### 1. 环境准备

```bash
# Python 环境 (需要 3.11+)
cd agents
pip install -e .

# Node.js 环境
cd generator
npm install
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env 填入你的 ANTHROPIC_API_KEY
```

### 3. 启动 Generator 服务

```bash
cd generator
npm run dev
```

### 4. 运行流水线

```bash
# 完整流水线 (发现 → 分析 → 编码 → 上架)
python scripts/run_pipeline.py

# 仅运行发现阶段
python scripts/run_pipeline.py --discovery-only

# 指定品类
python scripts/run_pipeline.py --discovery-only --category photo

# 查看已有项目
python scripts/run_pipeline.py --list-projects
```

## 项目结构

```
miniapp-factory/
├── agents/                  # Python Agent 层
│   ├── config/settings.py   # 全局配置
│   ├── discovery/           # 发现 Agent - 找 App Store 有但小程序没有的
│   ├── research/            # 分析 Agent - 拆解功能、生成 PRD
│   ├── coding/              # 编码 Agent - 调度代码生成
│   ├── publisher/           # 上架 Agent - 提交各平台审核
│   ├── orchestrator/        # LangGraph 流水线调度
│   └── shared/              # 共享模型、LLM 封装、数据库
├── generator/               # Node.js 代码生成服务
│   └── src/codegen/         # uni-app 页面/API/样式生成器
├── data/                    # 运行时数据
│   ├── apps/                # 采集到的 app 数据
│   ├── prds/                # 生成的 PRD 文档
│   ├── projects/            # 生成的小程序项目
│   └── reports/             # 分析报告
└── scripts/                 # 入口脚本
```

## MVP 范围

1. **Discovery**: 用七麦 API 拉排行榜 + 微信小程序搜索对比（无 API 时用 LLM 推荐）
2. **Research**: Claude 分析 app 功能 → 生成 PRD
3. **Coding**: uni-app 模板 + Claude 增强页面代码
4. **Publisher**: 生成提交材料 + 手动上架指引（后期自动化）

## 注意事项

- 首次运行如果没有七麦/SensorTower API Key，系统会使用 LLM 推荐热门 AI 应用
- Generator 服务需要单独启动（`npm run dev`）
- 生成的项目在 `data/projects/` 目录下，可直接用对应平台开发者工具打开
