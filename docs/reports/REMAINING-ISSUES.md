# Miniapp Factory — 剩余问题清单（5 轮审计后）

> 5 轮审计共发现 40 项问题，全部已修复。以下记录当前状态和已知限制。

---

## ✅ 全部已关闭项汇总

### Critical (P0) — 8 项 ✅

| # | 问题 | 修复轮次 |
|---|------|---------|
| C-1 | Zip 下载临时文件不清理 | R1 |
| C-2 | GET /download 没有鉴权 | R1 |
| C-3 | WebSocket 没有 token 校验 | R1 |
| C-4 | run_demo_pipeline.py 函数重复定义 | R1 |
| C-5 | App.vue WebSocket disconnect 清理 | R1 |
| C-6 | .env 泄露检查 | R1 |
| P0-6 | QA 检查路径错误（根目录 vs src/） | R3 |
| P0-7 | _flush_logs_to_disk 空覆盖 | R3 |
| P0-8 | Dockerfile.api 安装方式有误 | R4+R5 |
| P0-9 | Dockerfile.generator 缺 devDeps 导致 tsc 失败 | R4 |

### High (P1) — 17 项 ✅

| # | 问题 | 修复轮次 |
|---|------|---------|
| H-1 | readline 阻塞导致超时检测延迟 | R1 |
| H-2 | Docker 配置 | R1 |
| P1-9 | pipeline_stop 和 stream 竞态 | R3+R5 |
| P1-10 | get_job_detail 大文件限制 | R3 |
| P1-11 | pipeline_finished broadcast 异常保护 | R3 |
| P1-12 | mode 参数未校验 | R4 |
| P1-13 | get_job_artifact 无鉴权 | R4 |
| P1-14 | scraper 误判率优化 | R4 |
| P1-15 | pipeline_stop 僵尸 task | R5 |
| P1-16 | job_id 碰撞风险 | R5 |
| P1-17 | list_jobs limit/offset 无校验 | R5 |

### Medium (P2) — 15 项 ✅

| # | 问题 | 修复轮次 |
|---|------|---------|
| P2-1 | 路径穿越防御 | R2 |
| P2-2 | Pipeline 超时测试 | R2 |
| P2-6 | list_jobs 分页 | R3 |
| P2-7 | discovery agent 去重 | R3 |
| P2-8 | conftest.py fixture cleanup | R3 |
| P2-9 | Dockerfile.dashboard tsconfig 通配 | R4 |
| P2-10 | asyncio.get_event_loop() 废弃 | R4 |
| P2-11 | HTTP 安全头 | R4 |
| P2-12 | get_job_detail/latest 加 auth | R5 |
| P2-13 | download zip 大小限制 | R5 |
| P2-14 | 前端 api.ts GET 带 key（已确认覆盖） | R5 |
| P2-15 | python-dotenv 已在依赖中 | R5 |
| P2-16 | graceful shutdown | R5 |

### 终审追加修复 — 7 项 ✅

| # | 问题 | 说明 |
|---|------|------|
| 1 | Dockerfile.api --only-deps 无效 | 改为直接 pip install agents/（源码已 COPY） |
| 2 | API 容器缺 Node/npm | 加 nodesource Node.js 22 安装 |
| 3 | deque 不支持 slicing | 改为 list(pipeline_logs)[-N:] |
| 4 | generator 生产鉴权可关闭 | NODE_ENV=production 无 key 拒绝启动 |
| 5 | Dockerfile.dashboard fallback | 改为严格 npm ci |
| 6 | WebSocket jobId 未编码 | 加 encodeURIComponent |
| 7 | 文档过期 | README/REMAINING-ISSUES 重写 |

---

## 已知限制（非 Bug，是设计取舍）

1. **单 worker + 全局状态** — 不支持水平扩展，同时只能跑一个 pipeline
2. **JSON 文件数据库** — 对 MVP 够用，但并发写受 filelock 约束，无查询能力
3. **LLM Agent 无单元测试** — 需要 mock 才能测，属于下一阶段工作
4. **Vue 组件零测试** — 14 个组件无任何 render/interaction test
5. **run_demo_pipeline.py 2000 行** — 与 agents/ 逻辑重复，重构需要整体规划
6. **WebSocket token 在 query string** — 浏览器 WS API 限制
7. **Scraper 准确率有限** — 搜狗/百度代理搜索，短名称跳过
8. **VITE_API_TOKEN bake-in** — token 烘焙进 JS bundle，换 key 需重新 build dashboard 镜像
9. **端到端 pipeline run 已验证通过** — QA passed, build passed, dist 存在；readiness=false 因缺 AppID/截图（业务原因）

---

## 测试覆盖

```
agents/tests/test_database.py        — 4 cases（save/load/list + filelock）
agents/tests/test_pipeline_report.py — 9 cases（报告生成 + 步骤验证）
agents/tests/test_real_inputs.py     — 5 cases（输入验证 + 规范化）
agents/tests/test_server.py          — 8 cases（API 端点 + auth + 路径穿越 + WS 历史日志）
dashboard/src/__tests__/api.test.ts  — 4 cases（WS 编码 + 重连 + 4001 + disconnect）
generator/src/__tests__/page-builder.test.ts — 5 cases（项目生成 + pages.json merge）
                                     ─────────
                                     35 cases total, all passing
```

---

## 下一阶段建议

| 优先级 | 方向 | 预估 |
|--------|------|------|
| 1 | Vue 组件测试（Vitest + Testing Library） | 1-2 天 |
| 2 | LLM Agent mock 测试 | 1 天 |
| 3 | 任务队列（Celery/RQ）替换子进程 | 2-3 天 |
| 4 | SQLite 替换 JSON 数据库 | 1 天 |
| 5 | E2E 测试（Playwright） | 2 天 |
| 6 | Rate limiting + 请求日志 | 半天 |
