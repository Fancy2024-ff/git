# core/generator — 小程序代码生成（唯一生成真源）

## 目录结构（最终架构）

```
core/generator/
├── prd_builder.py        PRD 生成（功能/页面/技术栈规格）
├── blueprint_builder.py  页面蓝图层（占位/TODO，见文件 docstring）
├── codegen.py            唯一执行真源（generate_miniapp）
├── README.md             本文件
├── src/templates/        模板事实源（base + ai-* + *-viral）
├── src/codegen/          Node parity 工具（page-builder.ts，非主链路）
└── tests/                Python 构建级回归（test_viral_build.py）
```

职责链：`prd_builder`（做什么）→ `blueprint_builder`（生成哪些页面，TODO）
→ `codegen`（填充模板出工程）。

## 执行真源（重要）

miniapp 代码生成的**唯一执行真源 = `core/generator/codegen.py`**（`generate_miniapp`）。

- 生产主链路：`apps/api` → `core/pipeline/runner.py` → `generate_miniapp`。
- 模板事实源：`core/generator/src/templates`（`base` + `ai-*` + `*-viral`）。
- PRD 生成：`core/generator/prd_builder.py`。

## Node 部分的身份

`src/codegen/page-builder.ts` + `src/index.ts`（Express 服务）是 **Node parity /
兼容工具链**，**不在生产主链路中执行**：

- 用途：Node 生态 / vitest 回归（`src/__tests__/page-builder.test.ts`），
  验证模板选择、token 契约、签名页等规则。
- 它与 `codegen.py` 共享同一套模板目录与 token 契约
  （`__APP_NAME__` / `__APP_SUBTITLE__` / `__APP_FEATURES_JSON__` /
  `__APP_FEATURE_TITLE__`）；改生成规则时**先改 `codegen.py`，再同步 page-builder.ts**。
- 部署：已从 `docker-compose.yml` 正式服务中移除，不再要求 generator 服务的鉴权/地址变量。

## 落点规则

- 新模板类型 / 模板选择 / 页面骨架 → `src/templates` + `classifier`（在 core/opportunity）。
- 生成流程（复制/overlay/token/pages/docs）→ `codegen.py`。
- 页面动态蓝图 → `blueprint_builder.py`（实现后由 codegen 调用）。
- 不要在 `core/pipeline/runner.py` 里 re-author 任何生成逻辑。
