# 🔥 Miniapp Factory 顶级工程审计 — 你欠的活全在这里

## 你的身份

你是这个项目的 sole developer。我作为 Staff Engineer 审计了你的全部代码。以下是我逐模块的拷打，每一条都需要你回应：要么修掉，要么给出合理的技术论据说明为什么不修。"MVP 先不做" 不是借口——我指出的 P0 问题是**你声称已完成但实际没完成的**。

---

## 🔴 P0 — 核心流程已断裂，你的 "Phase 1 ✅ DONE" 是假的

### 1. Generator 模板目录全空 — 生成的项目是废物

```
generator/src/templates/
├── ai-chat/    (空)
├── ai-image/   (空)
├── ai-tool/    (空)
└── base/       (空)
```

`page-builder.ts:44-55` 会 `fs.copy(templatePath, projectPath)` —— 拷贝一个空目录。生成出来的"项目"连 `package.json` 都没有。uni-app CLI 跑不起来，QA Agent 验证的是一堆空气。

**要求：**
- `base/` 模板必须包含完整可运行的 uni-app 3 项目骨架：
  - `package.json` (依赖: `@dcloudio/uni-app`, `vue@3`, `@dcloudio/vite-plugin-uni`)
  - `vite.config.ts`
  - `src/App.vue`, `src/main.ts`, `src/pages/index/index.vue`
  - `src/manifest.json` (带占位 appid)
  - `src/pages.json`
  - `src/uni.scss`
  - `src/static/` (空目录保留)
- `ai-tool/` 扩展 base，增加：通用 AI 工具页面布局（输入区+结果区+loading 状态）
- `ai-chat/` 扩展 base，增加：聊天界面骨架（消息列表+输入栏+流式响应 placeholder）
- `ai-image/` 扩展 base，增加：图片上传/展示界面

这些模板要能 `npm install && npx uni build:mp-weixin` 不报错。

---

### 2. page-builder 生成了 pages.json 声明但没生成首页文件

`page-builder.ts:228` 在 pagesConfig 里声明了 `pages/index/index`，但 L62-77 的循环只遍历 `prd.core_features` 生成功能页。**首页永远不存在**。

uni-app 启动时找不到入口页 → 白屏。

**要求：**
- 在 `generateProject()` 里，功能页生成之前，先生成 `src/pages/index/index.vue`
- 首页应包含：app 名称、功能入口列表（navigator 到各功能页）、底部 tab 配置对应

---

### 3. server.py 路由定义重复 — FastAPI 启动行为不确定

以下路由定义了**两次**：
- `/api/pipeline/status` → L60处的 `get_overview` 之后（~L370）和 L450
- `/ws/pipeline` → L378 和 L543

FastAPI 不会报错但后定义的覆盖前面的。`_stream_pipeline_output` 和 `_read_pipeline_output` 是两套几乎相同的逻辑，说明你复制粘贴后没清理。

**要求：**
- 删除重复的路由定义，保留逻辑更完整的版本
- `_stream_pipeline_output` 和 `_read_pipeline_output` 合并为一个
- 添加 `/api/pipeline/status` 的 response_model

---

## 🟡 P1 — 功能性问题，不修会被用户骂

### 4. 支付宝/抖音小程序搜索直接 return False

`agents/discovery/scrapers/miniprogram.py:70-85`

```python
def _search_alipay(app_name: str) -> bool:
    # TODO: Implement Alipay mini-program search
    return False

def _search_douyin(app_name: str) -> bool:
    # TODO: Implement Douyin mini-program search
    return False
```

这意味着 8 问评估框架的第 3/4 问（平台有没有同类？覆盖是否充分？）对支付宝和抖音**永远回答"没有"**。所有候选 app 的 gap_score 都虚高。

**要求：**
- 支付宝：搜索 `https://m.alipay.com/` 或用百度搜 `site:mini.alipay.com {app_name}` 做 heuristic
- 抖音：搜索 `https://microapp.bytedance.com/` 或类似 heuristic
- 如果直接访问被封，用通用搜索引擎 `"{app_name}" 小程序 支付宝/抖音` 检测存在性
- 出错时 return False（保持乐观策略），但要 log warning

---

### 5. 前端 API 地址硬编码

`dashboard/src/services/api.ts:3-4`：
```typescript
const BASE = 'http://localhost:8000'
const WS_BASE = 'ws://localhost:8000'
```

部署到任何非 localhost 环境立刻挂。

**要求：**
```typescript
const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'
```
同时在 `.env.example` 和 `dashboard/.env.development` 中声明这两个变量。

---

### 6. WebSocket 重连是无限递归 + 无退避

```typescript
ws.onclose = () => {
    setTimeout(() => connectPipelineWS(onMessage), 3000)
}
```

服务器挂了 → 每 3 秒创建一个新 WebSocket → 旧的 onclose 还在 → 指数级增长。

**要求：**
- 加指数退避（3s → 6s → 12s → 最大 30s）
- 最大重试次数 20 次
- 重连成功后重置计数
- 提供 `disconnect()` 方法让组件销毁时清理

---

### 7. 数据库竞态条件

`agents/shared/database.py` — `_load_db()` 读 → 修改内存对象 → `_save_db()` 写。Pipeline subprocess 和 FastAPI server 同时操作同一个 JSON 文件。

**要求：**
- 方案 A（最小改动）：用 `filelock` 包加文件锁
- 方案 B（推荐）：改 SQLite + SQLAlchemy，models.py 已经有 Pydantic model 了，加个 ORM 映射就完
- 无论选哪个，要保证 `save_project` 是原子操作

---

### 8. API 零认证零安全

- `POST /api/demo/start` — 任何人可以触发 pipeline（会调 LLM 花钱）
- `POST /api/pipeline/stop` — 任何人可以杀进程
- `GET /api/sources` — 暴露 API key 前 8 位
- `CORS allow_origins=["*"]` — 任意网站可以跨域调用

**要求：**
- 添加 `X-API-Key` header 校验中间件，key 从环境变量 `DASHBOARD_API_KEY` 读取
- `/api/sources` 只返回 configured: bool，不返回 key 的任何部分
- CORS 收紧为 `["http://localhost:5173", os.getenv("DASHBOARD_ORIGIN", "")]`
- Pipeline 启动加限流：同时只能跑一个（已有）+ 每分钟最多启动 1 次

---

### 9. Pipeline 进程无超时无健康检查

`server.py` 的 `subprocess.Popen` 启动 pipeline 后，如果 LLM API 卡住或网络断开：
- 进程永远不退出
- WebSocket 永远显示 "running"
- 用户无法知道是卡了还是在跑

**要求：**
- 给 pipeline subprocess 加 timeout（默认 10 分钟）
- 超时后 kill + 通过 WS 广播 `{"type": "pipeline_error", "reason": "timeout"}`
- 在 `/api/pipeline/status` 返回 `started_at` 时间戳 + `elapsed_seconds`

---

## 🟠 P2 — 架构完善

### 10. miniprogram-ci 自动上传

`server.py:678` 已经做了所有前置检查（config 解析、npx 存在性、key 校验），但最后一行是：
```python
# TODO: Actually call miniprogram-ci here when configured
return {"upload_passed": False, "reason": "...not yet implemented..."}
```

**要求：**
```python
result = subprocess.run(
    ["npx", "miniprogram-ci", "upload",
     "--pp", str(project_path),
     "--pkp", config["private_key_path"],
     "--appid", config["appid"],
     "--uv", version,
     "-r", "1",
     "--desc", description],
    capture_output=True, text=True, timeout=120
)
```
加错误处理、返回 upload 结果。

---

### 11. Zip 下载功能

Dashboard 计划里提到"代码预览 + 下载 zip"，但 API 没有 zip 端点。

**要求：**
- 添加 `GET /api/jobs/{job_id}/download` → 返回 miniapp 目录的 zip 流
- 添加 `GET /api/projects/{project_id}/download` → 同上
- 前端对应位置加下载按钮

---

### 12. 测试 — 一个都没有

| 层 | 应有测试 |
|----|---------|
| agents/ | pytest: 每个 agent 的核心函数 + database 操作 + API 路由 |
| generator/ | jest/vitest: page-builder 的输出验证 |
| dashboard/ | vitest: store 逻辑 + API mock 测试 |

**要求：**
- 配置 `pytest.ini` / `pyproject.toml [tool.pytest]`
- 至少覆盖：
  - `test_analyzer.py` — 8 问评估的 scoring 逻辑
  - `test_database.py` — CRUD 操作正确性
  - `test_server.py` — 用 TestClient 测所有 API 路由（httpx + pytest-asyncio）
  - `test_page_builder.ts` — 生成的 Vue 文件语法正确
- 全部能 `pytest` / `npm test` 一键跑通

---

## ⚪ P3 — 工程化

### 13. Dockerfile + docker-compose

**要求：**
```yaml
# docker-compose.yml
services:
  api:
    build: ./agents
    ports: ["8000:8000"]
    env_file: .env
    volumes: ["./data:/app/data"]
  
  generator:
    build: ./generator
    ports: ["3001:3001"]
  
  dashboard:
    build: ./dashboard
    ports: ["5173:80"]
    depends_on: [api]
```

每个服务一个 Dockerfile。Dashboard 用 nginx 托管 build 产物。

---

### 14. .gitignore 和 secrets 管理

当前 `agents/.env` 直接在仓库里。

**要求：**
- 根目录 `.gitignore` 添加: `.env`, `agents/.env`, `data/`, `*.pyc`, `__pycache__/`, `node_modules/`, `.venv/`
- 提供 `.env.example` 列出所有需要的环境变量（值为空或 placeholder）
- `agents/.env` 如果已经提交了，从 git history 中确认没有真实 key

---

### 15. 错误边界和用户体验

当前如果 API 调不通，前端只在 console 报错，用户看到的是空白/卡住。

**要求：**
- 全局错误边界组件：API 失败时显示 toast 或 error banner
- Pipeline 页面：超时 / 失败有明确 UI 状态，不是永远转圈
- Jobs 列表：如果 pipeline 崩了没生成完整 artifacts，显示"失败"标签而不是空数据

---

## 📊 验收标准

完成以上修改后，我要看到：

1. `cd generator && npm install && npm run build` ✅
2. `cd generator && npm test` ✅ (至少 page-builder 有测试)
3. 生成的 uni-app 项目能 `npm install && npx uni build:mp-weixin` ✅
4. `cd agents && pip install -e . && pytest` ✅ (至少 10 个 test case pass)
5. `cd dashboard && npm install && npm run build` ✅ (无 TS error)
6. `docker-compose up` 能把三个服务跑起来 ✅
7. 访问 dashboard → 点击启动 pipeline → 看到实时日志 → 完成后看到完整 job 详情 ✅
8. API 未携带 key 时返回 401 ✅

---

## 工作顺序

不要乱做，按这个顺序来：

1. **先修 generator 模板** (P0-1) — 这是地基，后面所有测试都依赖它
2. **修 page-builder 首页生成** (P0-2) — 确保生成的项目能跑
3. **清理 server.py 重复路由** (P0-3) — 确保后端能启动
4. **加 API 认证** (P1-8) — 安全优先
5. **前端 env 变量 + WS 退避** (P1-5,6) — 确保联调能过
6. **补搜索、加超时、加下载** (P1-4, P2-9,10,11)
7. **测试** (P2-12) — 对以上改动写测试
8. **Docker + gitignore** (P3-13,14)
9. **错误边界** (P3-15)

每完成一个 P0 项，先验证再继续。别一口气写完最后发现模板还是跑不起来。

---

*审计完毕。开工。*
