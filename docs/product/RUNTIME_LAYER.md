# Runtime 执行层（core/runtime）

> 能力的**真实执行层**。capabilities 定义"能做什么"，runtime 负责"真的去做"，
> 并把执行状态写成 artifact，让 capability → runtime → artifact → API → frontend 这条链真正打通。

## 为什么需要 runtime 层

capabilities 层只回答"能力是否接入"；但复杂能力（图像/视频）是**慢异步**的，需要任务模型
（创建→轮询→取结果→失败→超时→清理）。把这套放进 runtime，让：
- image 成为第一条真实运行链路的承载层
- OCR / speech / video 复用**同一套** executor + 任务模型，不各写一套
- 状态可落 artifact，被 API / 前端消费

## 统一任务模型（task_model.py）

状态机：`CREATED → PROCESSING → (SUCCEEDED | FAILED | TIMEOUT) → CLEANED`
- 非法转移抛错（如 SUCCEEDED→PROCESSING）
- 超时基于 deadline 判定
- **未接入 provider 的任务直接进 FAILED(provider_missing)，绝不停在假 PROCESSING、绝不假完成**

## 统一执行器（executor.py）

6 动作：`create / poll / result / fail / timeout / cleanup`，复用 capabilities adapter：
- **异步能力**（image.process）：create→adapter.create_task，poll→adapter.poll_task
- **同步能力**（text/utility）：create 即 adapter.execute，立即落终态，不伪造等待
- **未配置 provider**：create 直接 FAILED(provider_missing)

配置 IMAGE_API_KEY + IMAGE_API_BASE 后，**同一条 executor 链路自动变真实**，业务/模板层不改。

## 执行报告（status.py → runtime-execution-report.json）

诚实区分两个层级（回应"runtime_ready 不能偷换"）：

| 字段 | 含义 | 当前 |
|---|---|---|
| `capability_runtime` | **工厂侧**能否执行该能力（精确到 operation） | text=可执行; utility=仅 calculate; image/vision/speech/video=空 |
| `app_runtime.runnable` | **生成出来的小程序自身**能否真跑 | **全部 false** |

`app_runtime=false` 的原因：生成的小程序前端调用的 `/api/*` 能力接口，尚未由真实 provider + runtime
链路支撑。**不把"工厂能调 LLM"冒充"text_ai 小程序能跑"；不把单个 calculate 当整个 utility 品类成熟。**

`task_model` 字段声明状态枚举 + 6 动作 + async_capabilities，证明 OCR/speech/video 可复用同一模式。

## 消费链（已打通并测试）

```
runtime.status.build_execution_report(app_type)
  → runner._write_capability_reports 写 data/outputs/{jobId}/runtime-execution-report.json
    → API /api/jobs/{id} 通用 artifact 读取返回该字段
      → 前端 overview.ts capabilityOverview() 解析 capability_runtime / app_runtime
        → OverviewDashboard 展示「工厂侧能力执行」vs「生成小程序自身运行」两行
```
端到端测试 `test_runtime_layer.py::test_execution_report_is_artifact_serializable` + 前端
`appTypes.test.ts` 的诚实区分用例 + 实跑 API 验证均覆盖此链路。

## 能力当前精确状态（诚实表述）

- **text**：工厂侧 runtime_ready（LLM 已接）；生成的 text_ai 小程序自身 app_runtime=false
- **image**：能力接口范式成立（interface_ready）；真实 provider 未接，runnable_level=buildable，
  **不表述为"复杂能力线已跑通"**
- **utility**：仅 `calculate` 为本地真实实现（runtime_ready）；`convert/query` 为占位未实现
- **vision / speech / video**：接口就位，provider_missing，工厂侧无可执行 operation

## 后续接入真实 provider（不改业务层）

1. 在 `core/capabilities/<cap>/providers/` 加真实 provider，配置对应 env
2. 该能力 adapter.configured 变 True → executor 同一链路即真实执行
3. runtime-execution-report 的 capability_runtime 自动反映；待生成小程序接入后 app_runtime 方可转 true
