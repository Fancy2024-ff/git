# Miniapp Factory — 剩余问题清单（Round 6 审计）

> P0-P1 全部关闭。以下是当前代码库仍存在的问题，按严重度排序。

---

## 🔴 CRITICAL — 必须修

### C-1: Zip 下载临时文件不清理（内存泄漏）

**文件**: `agents/server.py` ~L534-558

**问题**: `NamedTemporaryFile(delete=False)` 创建后返回 FileResponse，但文件永远不删除。每次下载留一个 zip 在 temp 目录。

**修复**:
```python
from fastapi import BackgroundTasks

@app.get("/api/jobs/{job_id}/download", dependencies=[Depends(verify_api_key)])
def download_job_miniapp(job_id: str, background_tasks: BackgroundTasks):
    ...
    background_tasks.add_task(os.unlink, str(zip_path))
    return FileResponse(zip_path, filename=f"{job_id}-miniapp.zip", media_type="application/zip")
```

---

### C-2: GET /download 没有鉴权

**文件**: `agents/server.py` ~L533

**问题**: 所有 POST 路由都加了 `Depends(verify_api_key)`，但 download 是 GET，没加。任何人猜到 job_id 就能下载。

**修复**: 加 `dependencies=[Depends(verify_api_key)]`（和 C-1 一起改）。

---

### C-3: WebSocket 没有 token 校验

**文件**: `agents/server.py` ~L225-246

**问题**: `/ws/pipeline/{job_id}` 无认证。任何人连上就能监听 pipeline 日志。

**修复**:
```python
@app.websocket("/ws/pipeline/{job_id}")
async def ws_pipeline(ws: WebSocket, job_id: str):
    # 从 query param 读 token
    token = ws.query_params.get("token", "")
    if DASHBOARD_API_KEY and token != DASHBOARD_API_KEY:
        await ws.close(code=4001, reason="Unauthorized")
        return
    await ws.accept()
    ...
```

前端连接时：
```typescript
new WebSocket(`${WS_BASE}/ws/pipeline/${jobId}?token=${API_KEY}`)
```

---

### C-4: `run_demo_pipeline.py` 函数重复定义

**文件**: `scripts/run_demo_pipeline.py` ~L263-267

**问题**: `opportunity_score_agent()` 定义了两次。第一次是空壳（只有 docstring），第二次才是真正实现。Python 不会报错但第一个定义是废代码。

**修复**: 删除 L263-265 的空定义。

---

### C-5: App.vue WebSocket 没有 disconnect 清理

**文件**: `dashboard/src/App.vue` ~L93

**问题**: `connectPipelineWS` 返回了 `{ disconnect }` 方法但从没调用。WS 连接永远不关闭：
- Pipeline 跑完后 WS 还开着
- 用户关闭页面时 WS 不主动断开（靠浏览器 GC）

**修复**:
```typescript
import { onBeforeUnmount } from 'vue'

let wsHandle: { disconnect: () => void } | null = null

async function startPipeline() {
  ...
  const res = await api.startPipeline(mode.value)
  wsHandle = connectPipelineWS(res.job_id, (msg) => {
    if (msg.type === 'log') logs.value.push(msg.data)
    if (msg.type === 'pipeline_finished') {
      running.value = false
      wsHandle?.disconnect()
      wsHandle = null
      ...
    }
  })
}

onBeforeUnmount(() => {
  wsHandle?.disconnect()
})
```

---

### C-6: agents/.env 泄露真实 API Key

**文件**: `agents/.env`

**问题**: 文件里包含真实的 Anthropic API key。即使 .gitignore 有 `.env`，如果已经 commit 过，历史里还有。

**修复**:
1. 确认 `git log --all -- agents/.env` 没有历史记录
2. 如果有，rotate 这个 key（去 Anthropic Console 重新生成）
3. 确认 `.gitignore` 覆盖了 `agents/.env`

---

## 🟡 HIGH — 应该修

### H-1: readline 阻塞导致超时检测延迟

**文件**: `agents/server.py` ~L175

**问题**: `run_in_executor(None, pipeline_process.stdout.readline)` 会在没有输出时阻塞。如果 pipeline 卡在某步不输出任何内容（比如 LLM 长时间思考），超时检测要等到下一行输出才能触发。

**修复**:
```python
import asyncio

async def _stream_pipeline_output(job_id: str):
    started_at = time.time()
    loop = asyncio.get_event_loop()

    while pipeline_process and pipeline_process.poll() is None:
        # 用 wait_for 限制单次 readline 等待时间
        try:
            line = await asyncio.wait_for(
                loop.run_in_executor(None, pipeline_process.stdout.readline),
                timeout=5.0  # 每 5 秒检查一次超时
            )
        except asyncio.TimeoutError:
            # readline 超时，检查总超时
            if time.time() - started_at > PIPELINE_TIMEOUT:
                pipeline_process.kill()
                await _broadcast({"type": "pipeline_failed", "job_id": job_id, "reason": "Timeout"})
                break
            continue

        if not line:
            break
        ...
```

---

### H-2: 无 Dockerfile / docker-compose

**缺失文件**: 项目根目录无 Docker 配置

**需要**:
```
miniapp-factory/
├── Dockerfile.api          # FastAPI backend
├── Dockerfile.generator    # Node.js generator service
├── Dockerfile.dashboard    # Vite build + nginx
└── docker-compose.yml      # 编排三个服务
```

---

### H-3: 零测试覆盖

**缺失**: 无任何 `.test.ts`、`.test.py`、`pytest.ini`、`vitest.config.ts`

**最小测试集建议**:

| 层 | 文件 | 覆盖内容 |
|----|------|---------|
| agents | `tests/test_server.py` | 所有 API 端点 + auth 校验 |
| agents | `tests/test_database.py` | save/load/list + 文件锁 |
| agents | `tests/test_analyzer.py` | 8 问评分逻辑 |
| generator | `src/__tests__/page-builder.test.ts` | 生成项目结构 + pages.json merge |
| dashboard | `src/__tests__/api.test.ts` | API 调用 mock |

---

## 🟠 MEDIUM — 建议修

### M-1: `run_demo_pipeline.py` 超长单文件

当前文件 **1700+ 行**，包含：市场分析、需求评估、缺口检测、评分、PRD 生成、代码生成、QA 检查、材料生成、打包……全在一个文件里。

**建议**: 拆分为 `scripts/agents/` 下的独立模块，pipeline 主文件只做编排调度。

### M-2: 前端无 loading 状态统一管理

各组件各自管理 loading/error 状态。建议用 Pinia store 统一管理 pipeline 状态、全局 error、WS 连接状态。

### M-3: Generator 服务（Node.js）未集成到主 pipeline

当前 `run_demo_pipeline.py` 用 `shutil.copytree` 直接从模板复制，不经过 Node.js 的 `page-builder.ts`。两套代码做同一件事。

**建议**: 二选一——
- A: Demo pipeline 也调 Generator HTTP 服务（需要先启动 generator）
- B: 把 page-builder.ts 的逻辑完全删掉，全用 Python 实现（当前的实际状态）

---

## 📋 推荐执行顺序

| 优先级 | 项 | 预估工时 |
|--------|---|---------|
| 1 | C-1 + C-2 合并修 (zip cleanup + auth) | 5 min |
| 2 | C-3 WS token | 10 min |
| 3 | C-4 删重复函数 | 1 min |
| 4 | C-5 WS disconnect | 5 min |
| 5 | C-6 检查 API key 泄露 | 5 min |
| 6 | H-1 readline 超时 | 15 min |
| 7 | H-3 最小测试集 | 2 hr |
| 8 | H-2 Docker 配置 | 30 min |
| 9 | M-1~M-3 重构优化 | 后续迭代 |

---

## ✅ 已完成项汇总（跨 6 轮）

- [x] Generator 模板填充（base/ai-tool/ai-chat/ai-image）
- [x] page-builder pages.json 合并逻辑
- [x] run_demo_pipeline 模板集成
- [x] pipeline-report.json 逐步写入
- [x] WebSocket per-job 路由 + 指数退避重连
- [x] API 认证中间件（POST 路由）
- [x] Pipeline 超时 kill
- [x] 支付宝/抖音搜索（百度 heuristic）
- [x] 数据库文件锁
- [x] 前端错误边界 + retry
- [x] Zip 下载端点
- [x] 前端下载按钮
- [x] loadLatest 404 区分
- [x] CORS 限定 origin
- [x] .env.example 配置
- [x] .gitignore 完善
- [x] server.py 路由去重
- [x] SubmitCenterPanel
- [x] BossViewPanel 假值清理
- [x] Pipeline start 返回 job_id
- [x] Real mode 校验
- [x] 文档生成（AGENT_MAP / CODE_STRUCTURE / PROMPT_AND_RULES）
