# 小程序批量生产工厂 - 项目架构设计

## 核心定位

Agent 驱动的小程序/Mini App 批量生产系统。自动从 App Store / Google Play 发现已验证的 AI 需求，识别小程序生态供给缺口，通过多 Agent 协作完成需求洞察、产品设计、代码生成、质量检测、上架发布和数据复盘。

## 技术决策
- Agent 编排层：Python + LangChain/LangGraph
- 小程序代码生成：Node.js + uni-app
- 数据源：七麦/SensorTower API + 各小程序平台搜索
- LLM：Claude (Anthropic API)

## 完整 Agent 工作流

```
START
  │
  ▼
[Discovery Agent] ──→ 扫描 App Store/Google Play AI 排行榜
  │                    + 搜索各小程序平台是否已覆盖
  │                    + 8 问评估框架 (analyzer.py)
  ▼
[Research Agent] ──→ 深度分析 app 功能 + 用户需求
  │                   + 生成 PRD (功能/页面/API/变现)
  ▼
[Coding Agent] ──→ 调用 Generator 服务生成 uni-app 项目
  │                 + LLM 增强页面逻辑
  │                 + 生成 API 层 + 工具函数
  ▼
[QA Agent] ──→ 结构验证 + 代码质量检查
  │             + 平台合规性检查 (包大小/API/内容)
  │             + 自动修复可修复的问题
  ▼ (score >= 40 才放行)
[Publisher Agent] ──→ 生成上架材料 (名称/简介/隐私协议)
  │                    + 各平台提交指引 (MVP 手动)
  │                    + 后期: CI/CD 自动上传
  ▼
[Review Agent] ──→ 监控审核状态 (通过/拒绝)
  │                 + 分析拒绝原因 → 自动修复 → 重新提交
  │                 + 跟踪上线后数据 (访问/留存/转化)
  │                 + 决策: 优化 / 创建变体 / 扩平台 / 淘汰
  ▼
  └──→ 循环回 Discovery (找下一个机会)
```

## 8 问评估框架 (Discovery → Analyzer)

每发现一个 App 必须回答：
1. 需求是否真实存在？(下载量/评分/评论验证)
2. 用户是否愿意付费？(变现模式可行性)
3. 小程序平台有没有同类产品？
4. 如果有，覆盖是否充分？(差异化空间)
5. 需求是否适合做成小程序？(技术限制评估)
6. MVP 能否快速实现？(≤2周)
7. 合规/版权/审核风险？
8. 最适合上架到哪个平台？

综合评分 ≥ 60 才进入生产流程。

## 项目结构

```
miniapp-factory/
├── agents/                      # Python Agent 层
│   ├── pyproject.toml
│   ├── config/settings.py       # 全局配置
│   ├── discovery/               # 发现 Agent
│   │   ├── agent.py             # 主逻辑: 扫描 + 覆盖检查
│   │   ├── analyzer.py          # 8 问评估框架
│   │   └── scrapers/            # 数据采集器
│   │       ├── appstore.py      # App Store (七麦 API)
│   │       ├── googleplay.py    # Google Play (SensorTower)
│   │       └── miniprogram.py   # 小程序平台搜索
│   ├── research/                # 分析 Agent
│   │   └── agent.py             # 功能拆解 + PRD 生成
│   ├── coding/                  # 编码 Agent
│   │   ├── agent.py             # 主逻辑 + LLM 增强
│   │   └── task_dispatcher.py   # HTTP 调用 Generator 服务
│   ├── qa/                      # 质检 Agent
│   │   └── agent.py             # 结构/代码/合规验证
│   ├── publisher/               # 上架 Agent
│   │   ├── agent.py             # 提交材料生成 + 平台适配
│   │   └── platforms/           # 各平台提交逻辑
│   ├── review/                  # 复盘 Agent
│   │   └── agent.py             # 审核跟踪 + 数据复盘 + 决策
│   ├── orchestrator/            # 总调度器
│   │   └── pipeline.py          # LangGraph 工作流
│   └── shared/
│       ├── llm.py               # LLM 客户端
│       ├── database.py          # 数据持久化
│       └── models.py            # 数据模型
│
├── generator/                   # Node.js 代码生成层
│   ├── src/index.ts             # Express 服务入口
│   └── src/codegen/
│       └── page-builder.ts      # 页面生成器
│
├── data/                        # 运行时数据
│   ├── apps/                    # 采集到的 app 数据
│   ├── prds/                    # 生成的 PRD
│   ├── projects/                # 生成的小程序项目
│   └── reports/                 # 分析/提交/复盘报告
│
└── scripts/
    └── run_pipeline.py          # 入口脚本
```

## 实现阶段

### Phase 1 (MVP) ✅ DONE
- Discovery Agent: LLM 推荐 + 小程序搜索对比 + 8 问评估
- Research Agent: Claude 分析 + PRD 生成
- Coding Agent: Generator 服务 + LLM 增强 + 本地 fallback
- QA Agent: 结构/代码/平台合规检查
- Publisher Agent: 提交材料生成 + 手动上架指引
- Review Agent: 拒绝分析 + 决策建议
- Pipeline: LangGraph 全流程串联

### Phase 2 (自动化)
- 七麦/SensorTower API 接入真实数据
- miniprogram-ci 自动上传微信小程序
- uni-app 模板库 (ai-tool / ai-chat / ai-image)
- 上架后数据自动采集 (平台 API)
- 基于 Review 决策的自动循环

### Phase 3 (规模化)
- 并行流水线 (同时处理多个 app)
- 变体生成 (同一需求 → 多个不同定位的小程序)
- A/B 测试框架
- 管理后台 (dashboard)
- 收益追踪和 ROI 分析
