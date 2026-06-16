# 生产架构规划 - 7x24 小程序上架工厂

> 当前阶段: 可演示自动化原型
> 目标阶段: 7x24 持续生产系统

## 架构模块

### 数据采集层
- **Scheduler**: 定时扫描 App Store / Google Play 排行榜
- **Data Collector**: 七麦 API、SensorTower API、App Store Connect API
- **Mini Program Search**: 各平台小程序搜索（搜狗微信搜索、支付宝搜索等）

### Agent 编排层
- **Opportunity Agent**: 机会评分（8 问评估框架 + LLM）
- **Platform Agent**: 平台适配推荐（读取 platform-registry.json）
- **PRD Agent**: LLM 驱动需求文档生成
- **Codegen Agent**: LLM 增强代码生成
- **QA Agent**: 自动构建 + 静态检查 + 合规检查
- **Submit Agent**: 平台 CLI 上传（miniprogram-ci / devvit CLI 等）
- **Review Agent**: 审核结果采集 + 复盘

### 基础设施层
- **Worker Queue**: 任务队列（Celery / BullMQ）
- **Database**: Job 状态持久化（PostgreSQL / SQLite）
- **Object Storage**: 产物存储（本地 / S3）
- **Alert**: 失败告警（邮件 / 企微 / Telegram Bot）
- **Auth Vault**: 平台密钥管理（加密存储）

### 展示层
- **Dashboard**: Vue 3 实时看板
- **WebSocket**: 实时流程推送
- **API**: RESTful 控制接口
- **CLI**: 命令行触发入口

## 当前已实现

| 模块 | 状态 | 说明 |
|------|------|------|
| 本地数据读取 | ✅ | data/inputs/demo + data/inputs/real |
| 需求评分 | ✅ | 5 维度本地规则 |
| 平台推荐 | ✅ | 读取 platform-registry.json |
| PRD 生成 | ✅ | 模板化 |
| 代码生成 | ✅ | uni-app 骨架 |
| 构建验证 | ✅ | npm install + build |
| QA 检查 | ✅ | 12 项自动检查 |
| 提交包生成 | ✅ | publish-package/ |
| 实时日志 | ✅ | WebSocket 推送 |
| Dashboard | ✅ | Vue 3 SPA |

## 下一步实现

| 模块 | 优先级 | 依赖 |
|------|--------|------|
| 七麦 API 接入 | P1 | API Key |
| LLM 评分替换 | P1 | Anthropic API Key |
| miniprogram-ci 上传 | P1 | 微信 CI 私钥 |
| Telegram Bot 自动配置 | P1 | Bot Token |
| Discord Activity 部署 | P2 | Application ID |
| 定时扫描调度 | P2 | Scheduler 模块 |
| 审核结果回填 | P2 | Webhook / 轮询 |
| 告警通知 | P2 | 通知渠道配置 |
| 多 Job 并发 | P3 | Worker Queue |
| 生产数据库 | P3 | PostgreSQL |

## 运行模式

| 模式 | 说明 | 数据源 | 频率 |
|------|------|--------|------|
| 试运行 | 检查 Agent 管线健康 | 本地样例 | 按需 |
| 生产运行 | 真实选品分析 | 导入/API 采集 | 按需 → 定时 |
| 监控模式 | 审核状态跟踪 | 平台 Webhook | 持续 |
