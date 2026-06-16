# Docker 部署验证手册

> 本仓库的开发机未安装 Docker，因此 Dockerfile / docker-compose 只做了**静态校验**
> （路径、lockfile、端口、healthcheck 与当前架构对齐），**尚未实跑**。
> 请在装有 Docker 的机器上按本手册逐条执行，全部通过后才可对外声称「Docker 实测通过」。

## 0. 前置

- 已安装 Docker Desktop / Docker Engine（含 `docker compose` 子命令）
- 仓库根目录：`D:\code\git`（或对应克隆路径）

```bash
docker --version
docker compose version
```

## 1. 准备环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填入：

```
DASHBOARD_API_KEY=<自定义随机串>
GENERATOR_API_KEY=<自定义随机串>
# ANTHROPIC_API_KEY 可留空，demo 模式不需要
```

## 2. 构建镜像

```bash
docker compose build
```

预期：`api`、`generator`、`web` 三个镜像均 build 成功，无报错。
重点关注（这几处是上一轮重构修过的）：
- `web` 镜像 `npm ci` 能找到 `apps/web/package-lock.json`（不再是旧的 `dashboard/`）
- `generator` 镜像 `tsc` 编译通过，模板被 COPY 进 `src/templates`

## 3. 启动

```bash
docker compose up -d
docker compose ps
```

预期：三个服务 `State=running`，`api` 与 `web` 的 `Health` 最终为 `healthy`
（首次启动 `api` 会装 npm 依赖，healthy 可能需要 1–2 分钟）。

## 4. 健康检查

```bash
curl http://localhost:8000/health
# 预期: {"status":"ok"}  —— 该接口免鉴权
```

带鉴权的接口（替换 <KEY> 为 .env 里的 DASHBOARD_API_KEY）：

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/jobs            # 预期 401（无 key）
curl -s -H "X-API-Key: <KEY>" http://localhost:8000/api/jobs                        # 预期 200
```

## 5. 打开前端

浏览器访问 http://localhost:5173

预期：
- 顶部出现三档模式 **Demo / 试运行**、**Real / 生产运行**、**Live / 实时分析**，默认选中 Demo
- 顶部出现 **导入真实 App** 按钮

## 6. 跑一次 Demo Pipeline

方式 A：在前端点「启动试运行」。
方式 B：直接调 API：

```bash
curl -s -X POST http://localhost:8000/api/pipeline/start \
  -H "X-API-Key: <KEY>" -H "Content-Type: application/json" \
  -d '{"mode":"demo"}'
```

运行中预期：前端 Timeline 第一步显示中文「读取市场数据」（不是 `market_input`），
当前步骤蓝色脉冲，结束后变「完成」。

## 7. 检查产物

```bash
# {jobId} 取自 /api/jobs/latest 或 data/outputs 下最新目录
cat data/outputs/{jobId}/qa-report.json
```

预期字段：

```json
{
  "passed": true,
  "checks": {
    "install_passed": true,
    "build_passed": true,
    "dist_exists": true
  }
}
```

`data/outputs/{jobId}/generated/miniapp/dist/build/mp-weixin/` 应存在，可导入微信开发者工具。

## 8. 清理

```bash
docker compose down
```

## 通过标准

以上 2–7 全部符合预期，方可在 README 标注「Docker 实测通过（日期）」。
任一步失败，先记录失败步骤与日志（`docker compose logs <service>`），修复后从该步重跑。
