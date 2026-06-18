# 🔥 第二轮拷打 — P0 验收 + P1 工单

## P0 验收评审

### ✅ 通过项

| # | 项目 | 状态 |
|---|------|------|
| 1 | 生成的 miniapp 骨架完整 | 通过 — package.json/vite/pages 都有，npm build 通过 |
| 2 | 首页 index.vue 存在 | 通过 |
| 3 | server.py 路由去重 | 通过 — 14 个唯一端点 |
| 4 | Pipeline start 返回 job_id | 通过 |
| 5 | WebSocket 按 job 推送 | 通过 |
| 7 | Real mode 校验 apps.json | 通过 |

### ⚠️ 打回项

| # | 问题 | 为什么打回 |
|---|------|-----------|
| A | **Generator 模板还是空的** | `generator/src/templates/base/` `ai-tool/` `ai-chat/` `ai-image/` 四个目录 **零文件**。你是在 `run_demo_pipeline.py` 里用 Python 内联字符串生成的代码，完全绕过了 Generator Node.js 服务。这意味着 `Coding Agent (agent.py)` 调 `task_dispatcher.py` → HTTP → `page-builder.ts` 的路径是**死路**。LangGraph 全量 pipeline (`run_pipeline.py`) 走不通。 |
| B | **Pipeline report 非逐步写入** | 你说"性能有影响"所以推迟。写一个 JSON 文件每步追加一个 object 的性能开销是 **微秒级**，10 步总共 10 次 file write。这不是性能问题，这是偷懒。 |
| C | **WebSocket 重连逻辑删了但没替换** | 老版本有无限递归重连（有 bug），你 "修" 的方式是**直接删掉重连**。现在 WS 断了就永远断了，用户看不到后续日志。这比之前还差。 |

---

## 🔴 必须立刻修的 3 项（打回返工）

### 返工-A: Generator 模板必须有内容

你有两条路，选一条：

**方案 1（推荐）**：把 `run_demo_pipeline.py` 的 codegen 逻辑提取到 `generator/src/templates/`，让 Node.js 服务用它作为真模板。
- `base/` = 最小可运行 uni-app 项目（从你 demo pipeline 里已有的代码提取）
- `ai-tool/` = base + 工具页面布局（输入+结果+loading）
- `ai-chat/` = base + 聊天 UI
- `ai-image/` = base + 图片处理 UI

**方案 2**：如果你坚持不用 Node.js 服务，那就**删掉 generator/ 整个目录**，把 `page-builder.ts` 的逻辑并入 Python 的 `coding/agent.py`。但这意味着你要重写 `.plan.md` 里的架构，因为你宣称的架构是"Coding Agent 调 Generator 服务"。

不管选哪个，验收标准：
```bash
# 方案 1 验收
cd generator && npm run build  # TypeScript 编译通过
curl http://localhost:3001/health  # 200
curl -X POST http://localhost:3001/generate -d '{"app_name":"test","core_features":[{"name":"翻译","type":"input"}],"target_platforms":["wechat"]}' -H 'Content-Type: application/json'
# 返回 project_path，且该路径下有完整可 build 的 uni-app 项目
```

### 返工-B: pipeline-report.json 逐步写入

每个 step 完成后立刻写入：

```python
def write_step_report(output_dir: Path, step_num: int, step_name: str, status: str, data: dict):
    report_file = output_dir / "pipeline-report.json"
    if report_file.exists():
        report = json.loads(report_file.read_text(encoding="utf-8-sig"))
    else:
        report = {"steps": [], "started_at": datetime.now().isoformat()}
    report["steps"].append({
        "step": step_num,
        "name": step_name,
        "status": status,
        "completed_at": datetime.now().isoformat(),
        **data
    })
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
```

每步完成就调一次。Dashboard 前端轮询或 WS 推送都能拿到中间状态。

### 返工-C: WebSocket 重连（带指数退避）

```typescript
export function connectPipelineWS(
  jobId: string,
  onMessage: (data: any) => void,
  onDisconnect?: () => void
): { ws: WebSocket; disconnect: () => void } {
  let retryCount = 0
  let maxRetries = 15
  let ws: WebSocket
  let intentionalClose = false

  function connect() {
    ws = new WebSocket(`${WS_BASE}/ws/pipeline/${jobId}`)
    ws.onopen = () => { retryCount = 0 }
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {
      if (intentionalClose) return
      if (retryCount < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)
        retryCount++
        setTimeout(connect, delay)
      } else {
        onDisconnect?.()
      }
    }
  }

  connect()

  return {
    ws: ws!,
    disconnect() {
      intentionalClose = true
      ws?.close()
    }
  }
}
```

调用方在组件 unmount 时调 `disconnect()`。

---

## 🟡 P1 — 新工单（上一轮审计的 P1 你一条没动）

以下是必须在这一轮实现的 P1 项。不是"标记 P1 后面做"——是现在做。

### P1-1: API 认证中间件

CORS 还是 `allow_origins=["*"]`，API 无任何认证。修：

```python
from fastapi import Depends, Header

DASHBOARD_API_KEY = os.environ.get("DASHBOARD_API_KEY", "")

async def verify_api_key(x_api_key: str = Header(default="")):
    if DASHBOARD_API_KEY and x_api_key != DASHBOARD_API_KEY:
        raise HTTPException(401, "Invalid API key")

# 给所有写操作加依赖
@app.post("/api/pipeline/start", dependencies=[Depends(verify_api_key)])
```

CORS 改为：
```python
allow_origins=[
    "http://localhost:5173",
    os.environ.get("DASHBOARD_ORIGIN", "http://localhost:5173"),
]
```

前端 api.ts 的 get/post 函数加 header：
```typescript
const API_KEY = import.meta.env.VITE_API_KEY || ''
headers: { ...(API_KEY ? { 'X-API-Key': API_KEY } : {}) }
```

---

### P1-2: Pipeline 超时

当前 pipeline subprocess 永远没有 timeout。加：

```python
PIPELINE_TIMEOUT = int(os.environ.get("PIPELINE_TIMEOUT_SECONDS", "600"))

async def _stream_pipeline_output(job_id: str):
    started_at = time.time()
    ...
    while pipeline_process and pipeline_process.poll() is None:
        elapsed = time.time() - started_at
        if elapsed > PIPELINE_TIMEOUT:
            pipeline_process.kill()
            await _broadcast({"type": "pipeline_error", "job_id": job_id, "reason": f"Timeout after {PIPELINE_TIMEOUT}s"})
            break
        ...
```

`/api/pipeline/status` 返回增加 `started_at` 和 `elapsed_seconds`。

---

### P1-3: 支付宝/抖音小程序搜索

不需要完美，需要有东西。用百度搜索做 heuristic：

```python
def _search_alipay(app_name: str) -> bool:
    """通过百度搜索判断是否存在支付宝小程序。"""
    try:
        query = f'"{app_name}" 支付宝小程序'
        url = f"https://www.baidu.com/s?wd={query}"
        response = httpx.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 ..."}, follow_redirects=True)
        if response.status_code == 200:
            content = response.text.lower()
            # 检测是否有支付宝小程序相关结果
            indicators = ["支付宝小程序", "mini.alipay.com", "alipay.com"]
            return any(ind in content for ind in indicators) and app_name.lower() in content
    except Exception as e:
        print(f"[Alipay Search] Failed for '{app_name}': {e}")
    return False
```

抖音同理。这个准确度不需要 90%，50% 比 0% 强。

---

### P1-4: 数据库加锁

最小改动方案。安装 `filelock`，修改 database.py：

```python
from filelock import FileLock

DB_LOCK = FileLock(str(DB_FILE) + ".lock", timeout=10)

def save_project(project: MiniAppProject) -> None:
    with DB_LOCK:
        db = _load_db()
        project.updated_at = datetime.now()
        db["projects"][project.id] = json.loads(project.model_dump_json())
        _save_db(db)
```

加 `filelock` 到 `pyproject.toml` 的 dependencies。

---

### P1-5: 前端错误边界

当前 `App.vue` 的 error 只在顶部显示一行红字，API 失败时（服务没启动）用户看到空白 + console error。

需要：
- `loadJobs()` 和 `loadLatest()` 的 catch 里设置 `error.value`（当前是空 catch）
- error banner 加一个 retry 按钮
- Pipeline 跑的时候如果 WS 断了，显示"连接断开，重试中..."
- Pipeline 超时/失败时 `running` 改 false + 显示失败状态

---

### P1-6: Zip 下载

```python
import zipfile
import tempfile
from fastapi.responses import FileResponse

@app.get("/api/jobs/{job_id}/download")
def download_job_miniapp(job_id: str):
    """Download the generated miniapp as a zip file."""
    job_dir = OUTPUTS_DIR / job_id / "generated" / "miniapp"
    if not job_dir.exists():
        raise HTTPException(404, "Miniapp not found for this job")

    # Create zip in temp dir
    zip_path = Path(tempfile.mkdtemp()) / f"{job_id}-miniapp.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in job_dir.rglob("*"):
            if f.is_file() and "node_modules" not in str(f):
                zf.write(f, f.relative_to(job_dir))

    return FileResponse(zip_path, filename=f"{job_id}-miniapp.zip", media_type="application/zip")
```

前端 FilesPanel 加一个下载按钮。

---

## 📊 这一轮的验收标准

完成后我要看到：

| # | 验证命令/操作 | 期望结果 |
|---|-------------|----------|
| 1 | `generator/src/templates/base/` 有文件 | 至少 package.json + src/pages/index/index.vue |
| 2 | `curl POST /generate` 生成可 build 项目 | npm build 通过 |
| 3 | Pipeline report 第 3 步结束时文件已存在 | 包含 step 1-3 的数据 |
| 4 | 断开 WS → 等 3s → 自动重连 | 继续收到日志 |
| 5 | 不带 X-API-Key 调 `/api/pipeline/start` | 返回 401 |
| 6 | 带正确 key 调 | 返回 200 + accepted |
| 7 | CORS 从 `evil.com` 发请求 | 被拒绝 |
| 8 | Pipeline 跑超过 timeout | 自动 kill + WS 推送 error |
| 9 | `_search_alipay("翻译")` | 返回 True/False（不是写死 False） |
| 10 | `GET /api/jobs/{id}/download` | 返回 zip，解压后是完整 miniapp |
| 11 | Dashboard 断网 → 恢复 | error banner 消失，数据恢复 |

---

## 工作顺序

1. 返工-A（Generator 模板） — 这是架构债，再不修后面全是连锁问题
2. 返工-C（WS 重连） — 前端基础设施
3. P1-1（API 认证） — 安全
4. P1-2（Pipeline 超时） — 稳定性
5. 返工-B（Report 逐步写入） — 和超时配合
6. P1-3（搜索补全） — 数据质量
7. P1-4（数据库锁） — 并发安全
8. P1-5（前端错误边界） — UX
9. P1-6（Zip 下载） — 功能完整度

**每完成一项报告状态，不要一口气做完再说"全部通过"。**

---

*你上一轮的报告里 6 个"通过"里有 3 个存在偷工减料。这一轮我会逐项验证代码，不接受"通过"但实际绕过了核心模块的情况。开工。*
