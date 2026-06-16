# 新增功能放哪：落位规则表

> 动手前对照本表确定目录。找不到对应场景时回到 `target-architecture.md` 按层职责判断。
> 用词约定：**必须 / 不允许 / 允许过渡（须标记技术债）**。

## 17 类场景落位

| # | 新增什么 | 必须放在 | 不允许放在 |
|---|---|---|---|
| 1 | 新 API 路由 | `apps/api/`（路由 + service 调用，委托 core） | 把业务写进路由体内 |
| 2 | 新 WebSocket | `apps/api/`（连接/鉴权/推送），事件来自 pipeline | 在 ws 里跑业务/长任务 |
| 3 | 新前端页面 | `apps/web/src/components/` + tab 接入 `App.vue` | 把后端执行逻辑塞进组件 |
| 4 | 新前端业务模块 | `apps/web/src/data/`（纯逻辑，可单测） | 散在 .vue 里写死状态 |
| 5 | 新 Worker/Scheduler/Queue | `apps/worker/` | api / pipeline |
| 6 | 新 pipeline step | `core/pipeline/`（step 编排），实现委托对应层 | 直接在 runner.py 内联大段业务 |
| 7 | 新 Agent | `core/agents/<agent>/` | runner.py / api |
| 8 | 新 app 分类逻辑 | `core/classification/` + `core/domain` 单一事实源 | 散落多处重复判断 |
| 9 | 新 capability adapter/registry/provider | `core/capabilities/`（adapter）+ 外部调用走 integrations | runner.py / 页面 |
| 10 | 新模板 | `core/generator/src/templates/<app_type>/` + generator 选择逻辑 | 在 runner.py 写死 if app_type |
| 11 | 新运行时任务/上传/轮询 | `core/runtime/` | 页面 / api 路由 |
| 12 | 新平台接入逻辑 | `core/platforms/<platform>/` | pipeline / api 里混平台 if-else |
| 13 | 新第三方 API 接入 | `core/integrations/` | 各模块各自直接调 |
| 14 | 新持久化读写 | `core/persistence/`（repository 接口） | 业务里硬拼路径直接读写 |
| 15 | 新 artifact schema / report | 由产出它的 core 层定义 + 写入 `data/outputs/{jobId}/`；字段进 `core/domain` | 前端臆造字段 |
| 16 | 新测试 | 后端 `core/agents/tests/`；前端 `apps/web/src/__tests__/`；generator `core/generator/src/__tests__/` | 无测试就合入 |
| 17 | 新部署/监控/docker | `infra/docker` `infra/compose` `infra/nginx` `infra/monitoring` `infra/scripts` | 散落仓库根 |

## 可容忍过渡 vs 不可继续恶化

### 允许短期过渡（但必须在改动说明里标记技术债）

- 现有目录尚未建立时（如 `apps/worker`、`core/runtime`、`core/platforms`、`core/persistence`
  尚未实体化），**小幅**沿用现状位置，但必须：
  1. 在 PR/改动说明里写明「技术债：本应落在 core/<层>，因目标目录未建暂存于此」
  2. 新逻辑封装成独立函数/模块，便于日后整体抽离，不与旧代码缠绕
- 复用现有 `core/agents/shared/`（llm.py / database.py）作为 integrations/persistence 的临时落点，
  但新接入的 provider/repository 必须是独立文件，不堆进同一个大文件。
- 现有 `runner.py` 内已存在的步骤可继续维护原处；**新** step 的业务实现必须抽到对应 core 层，
  runner 只保留编排调用。

### 绝对不允许（即使图快也不行）

- 把新业务大段写进 `core/pipeline/runner.py` 主体或 `apps/api/main.py` 路由体。
- 在 `.vue` 组件里写后端执行逻辑或臆造状态（passed/ready 必须来自 artifact）。
- 写死路径 / 平台 / 模板 / provider / 步骤——必须走 registry / config / 单一事实源。
- 在 pipeline 或 api 里新增平台 if-else 分支（必须落 core/platforms）。
- 多处重复 app 分类或可行性判断（必须只在 core/classification）。
- 能力未接入却返回假成功（必须 provider_missing + runnable_level 降级）。
- 新增功能不配套测试就合入。

### 判断口诀

新增逻辑落位前问一句：**「这段如果三个月后要换平台/换 provider/加一类 app，会不会要改很多处？」**
会 → 说明放错层，按本表归位；不会且独立可抽离 → 可接受（必要时标技术债）。
