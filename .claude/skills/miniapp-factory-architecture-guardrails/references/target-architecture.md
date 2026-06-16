# 最终版目标架构 v1.0（权威说明）

> 已冻结。除非用户明确批准改架构，否则本文件即判断模块归属的唯一权威。
> 现状未完全迁移到位——本文件描述的是**目标**；新增代码必须按此落位，旧代码可暂存（见 migration-principles.md）。

## 顶层目录树

```
D:\code\git\
├─ apps\
│  ├─ api\          # 对外 API / WebSocket / 鉴权 / 路由 / schema / service 调用
│  ├─ web\          # 前端控制台（展示、交互、状态呈现）
│  └─ worker\       # 7x24 调度、后台任务、自动扫描、自动复盘
├─ core\
│  ├─ domain\       # 核心领域模型、枚举、状态定义（单一事实源）
│  ├─ pipeline\     # 流水线编排、step 状态、事件、报告
│  ├─ agents\       # discovery / research / coding / qa / review 等 Agent
│  ├─ classification\  # App 分类、小程序可行性判断、能力推导、平台推荐
│  ├─ capabilities\    # text/image/vision/speech/video/utility 能力适配层
│  ├─ generator\    # 模板矩阵、代码生成器
│  ├─ runtime\      # 上传、任务、轮询、结果回传、清理
│  ├─ platforms\    # wechat/alipay/douyin/telegram/reddit/discord 平台逻辑
│  ├─ integrations\ # 第三方 API / 数据源 / 平台 CLI / LLM / provider 接入
│  └─ persistence\  # repository / sqlite / postgres / file-store
├─ data\            # inputs / outputs / platform-auth / cache / temp / snapshots
├─ infra\           # docker / compose / nginx / monitoring / scripts
├─ scripts\  tests\  docs\
├─ .env.example  docker-compose.yml  README.md  CLAUDE.md
```

## apps 层职责

### apps/api
只做 API / WebSocket / auth / route / schema / service 调用。
**不负责重业务编排，不负责长任务执行。** 路由收到请求后委托给 core 层；不在路由里写业务细节。

### apps/web
只做前端展示、交互、状态呈现。
**不制造假状态，不塞后端执行逻辑。** 所有关键状态来自后端 artifact / API，前端不臆造 passed/ready。

### apps/worker
负责未来 7x24 调度、扫描、队列、自动复盘。
**所有后台长任务最终落这里**（自动扫 App Store/Google Play、定时复盘、任务队列消费）。
现状无此目录——新建后台调度逻辑必须落这里，不得塞进 api 或 pipeline。

## core 层职责（每层为什么必须分开）

### core/domain
核心领域模型、枚举、状态定义。是**单一事实源**：app_type、runnable_level、review_status 等
枚举与数据结构集中定义，其它层引用，不各自重定义。
> 现状：app_type 定义在 `core/capabilities/app_types.py`，是 domain 的雏形；新增领域枚举优先归入 domain 方向。

### core/pipeline
只做编排、step、事件、报告。
**不包办所有业务细节**——每个 step 调用对应的 agent/capability/generator，自己只管串联、状态、事件、写报告。
为什么分开：编排逻辑与业务实现混在一起 = runner.py 膨胀成 2000 行的根因。

### core/agents
负责分析、研究、PRD、策略、QA、复盘（discovery / research / coding / qa / review）。
**不直接承载第三方 provider 执行器**——要调外部 API 走 integrations，要调能力走 capabilities。

### core/classification
负责 app_type、可行性判断、required_capabilities、platform 推荐。
**不能多处散落重复判断**——分类是唯一入口，pipeline/前端/平台层都引用它的结论，不自行再判一遍。

### core/capabilities
负责 text/image/vision/speech/video/utility 的统一能力抽象（adapter + registry）。
**复杂能力不得散落在 runner.py 或页面里**——图像处理、OCR、TTS 等一律走 adapter 接口。

### core/generator
负责模板矩阵和代码骨架。
**生成骨架 ≠ 真实 runtime 能力**——generator 只产出可构建的 uni-app 项目；能不能真跑由 capabilities/runtime 决定。

### core/runtime
负责上传、任务、轮询、结果回传、清理。
**复杂运行态不能塞在页面里**——异步任务链路（create→poll→result）、文件上传、临时清理归这里。

### core/platforms
负责平台差异逻辑（wechat/alipay/douyin/telegram/reddit/discord 各自的上传/审核/资质差异）。
**不准继续在 pipeline 和 API 中混杂各平台细节**——平台 if-else 收敛到这里。

### core/integrations
负责所有外部 provider / 数据源 / LLM / 平台 CLI 接入。
**不能各模块各自乱调**——LLM 客户端、图像 API、七麦/SensorTower、miniprogram-ci 等统一从这里出。
> 现状：LLM 封装在 `core/agents/shared/llm.py`；新增外部 provider 接入优先归入 integrations 方向。

### core/persistence
负责 repository / db / file store。
**不准每个模块任意直接读写散乱路径**——JSON/SQLite/文件存储通过 repository 接口，不在业务里硬拼路径。
> 现状：`core/agents/shared/database.py` 是 persistence 雏形；新增持久化读写优先归入 persistence 方向。

## 什么逻辑绝对不能放错地方

| 逻辑 | 必须在 | 绝不能在 |
|---|---|---|
| 业务编排串联 | core/pipeline | api 路由 / 大组件 |
| 长任务 / 调度 / 扫描 | apps/worker | api / pipeline |
| app 分类 / 可行性 | core/classification（唯一） | 散落多处 |
| 能力调用（图像/OCR/语音…） | core/capabilities adapter | runner.py / 页面 |
| 异步上传/轮询/清理 | core/runtime | 页面 / api 路由 |
| 平台差异 if-else | core/platforms | pipeline / api |
| 外部 API / LLM / CLI | core/integrations | 各模块自行调 |
| DB / 文件读写 | core/persistence | 业务里硬拼路径 |
| 状态/枚举定义 | core/domain（单一事实源） | 各层重定义 |

## 最终模板矩阵方向（core/generator）

六类 app_type，每类一套模板，按分类结果选用：

- `text_ai` — 写作/翻译/摘要/问答（能力 text.generate）
- `image_ai` — 证件照/抠图/头像/增强（能力 image.process）
- `ocr_scan` — OCR/文档/票据识别（能力 vision.ocr）
- `speech_ai` — 配音/TTS/语音转写（能力 speech.tts / speech.asr）
- `video_light` — 视频摘要/封面/脚本，仅轻量入口（能力 video.process）
- `utility_tool` — 计算/转换/查询，本地能力（能力 utility.execute）

新增 app 形态时：先归入这六类之一；确需第七类必须先更新 core/domain 的单一事实源，再加模板与能力。

## 最终全局状态表达（统一，不允许另造一套）

全局运行/上架状态统一为以下分级，每一档独立表达，**绝不一律 passed**：

- `shell_only` — 仅页面骨架
- `buildable` — 可构建可提交，但所需能力全部未接入（空壳可上架）
- `runtime_ready` — 能力全部就位，可真实运行
- `upload_ready` — 平台授权齐备，可自动上传
- `review_ready` — 满足提交审核条件

诚实原则：能力未接入 = `provider_missing` + `runnable_level` 降级；
「能上架（空壳）」与「真能用（runtime_ready）」必须严格区分，前端/报告不得混为 passed。
