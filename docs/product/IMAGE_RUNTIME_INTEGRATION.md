# Image 能力真实接入 + 生成小程序接 runtime

> 本轮把 image_ai 从「接口范式成立 / provider_missing」推进到「第一条复杂能力线真正跑通」。

## 本轮接入的 operation

- **remove_background（抠图换底）** —— 唯一真接通的 operation。
- id_photo / avatar_style / enhance —— 接口保留，但当前 provider 未接通，
  调用返回 `provider_unsupported`（诚实，不假成功）。

## provider 配置

provider 选择由 `IMAGE_PROVIDER` 决定（`core/integrations/image_providers/`）：

| IMAGE_PROVIDER | 说明 | 需要 env |
|---|---|---|
| `http`（默认） | 真实 HTTP provider，生产路径 | `IMAGE_API_BASE` + `IMAGE_API_KEY`（可选 `IMAGE_TIMEOUT_SECONDS`） |
| `mock` | 确定性 provider，CI/演示用，走完整 create→poll→succeeded 生命周期 | 仅需 `IMAGE_PROVIDER=mock` |

- 未配置任何 provider → `provider_missing`，**不 fallback 成本地伪结果**。
- HTTP 协议约定：`POST {BASE}/tasks` 创建、`GET {BASE}/tasks/{id}` 轮询；不同 vendor 字段差异在
  `http_provider.py` 适配，上层只见统一 `ProviderTask`。

## runtime 链路

```
前端(生成的小程序) → apps/api → core/runtime/executor → core/capabilities/image/adapter
  → core/integrations/image_providers（真实 vendor，唯一 HTTP 落点）
```
- executor 统一任务模型：create→processing→poll→succeeded/failed/timeout→cleanup
- 同步/异步统一为任务生命周期；image 是异步能力，走 create_task/poll_task/get_result
- 任务结果含 result_url / operation / provider / finished_at

## API 链路（apps/api，复用鉴权）

| 方法 | 路径 | 作用 |
|---|---|---|
| POST | `/api/runtime/image/tasks` | 创建任务，返回 task_id/status/provider |
| GET | `/api/runtime/image/tasks/{id}` | 轮询状态 |
| GET | `/api/runtime/image/tasks/{id}/result` | 取结果 result_url |

provider_missing / timeout / upstream_error / auth_failed / invalid_request 标准化区分；
前端绝不直连第三方 provider。

## 模板前端如何接 runtime（core/generator image_ai）

`runner._pages_image_ai` 生成的 form.vue：
1. `uni.chooseImage` 选图
2. POST `/api/runtime/image/tasks` 创建任务（**不再 setTimeout 假处理，不再回显原图**）
3. 轮询 `/api/runtime/image/tasks/{id}`
4. 成功 → 取 result → 跳结果页展示真实 result_url（可保存到相册）
5. 失败 / provider_missing → 明确提示
状态机：idle / creating / processing / succeeded / failed / provider_missing。

## 诚实双层状态（runtime-execution-report.json）

- `capability_runtime.image.process.executable_operations`：工厂侧真接通的 operation
  （配置后 = `["remove_background"]`，未配置 = `[]`）
- `app_runtime.runnable`：生成的小程序自身能否真跑
  - image_ai + provider 已接入 → **true**（前端真实走 runtime）
  - 未接入 → false + 原因

## 当前未真接通项

- **P0**：接真实图像 vendor（设 `IMAGE_PROVIDER=http` + `IMAGE_API_BASE/KEY`）；本轮已用 mock 证明链路
- **P1**：image 的 id_photo / avatar_style / enhance 三个 operation 接通
- **P2**：vision/speech/video 复用同一 runtime 模式接入
