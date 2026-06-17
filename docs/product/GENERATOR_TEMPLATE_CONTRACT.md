# Generator 模板契约（Generator Template Contract）

> Node generator（core/generator）的模板体系。已从旧三模板迁移收口到新六模板。
> 单一事实源：`core/generator/src/codegen/template-registry.ts`。

## 正式模板体系（6 类 + base 底座）

正式模板（与 core/capabilities/app_types.py 的 template 字段同名）：
- text_ai / image_ai / ocr_scan / speech_ai / video_light / utility_tool

公共底座：
- **base** —— 始终先复制，保证项目可构建；非 app_type 主模板。

默认模板 / fallback：**text_ai**（统一；未知模板不再 fallback 到 ai-tool）。

## deprecated alias（已删除目录，仅保留归一化映射）

| 旧别名 | 归一化到 | 说明 |
|---|---|---|
| ai-tool | text_ai | 文本处理表单+结果，归 AI 文本工具主流形态 |
| ai-chat | text_ai | 对话页并入 text_ai（作为 chat 变体页） |
| ai-image | image_ai | 图片上传/处理 |

旧目录 `templates/ai-tool|ai-chat|ai-image` **已删除**；其真实页面已 git mv 迁入新目录
（form/result/chat → text_ai，canvas → image_ai）。传入旧别名仍可用（自动归一化），但不再作为目录存在。

## 模板单一事实源 API（template-registry.ts）

- `listOfficialTemplates()` / `listDeprecatedAliases()`
- `isOfficialTemplate(name)` / `templateExists(name)`（含 base 与别名 resolve）
- `resolveTemplateAlias(name)` / `normalizeTemplateName(name)`（任意入参 → 正式名，未知→text_ai）
- `getDefaultTemplate()`（text_ai）/ `getDefaultTemplateForAppType(appType)`

page-builder.ts 与 index.ts 均经此 registry，不再各自写死模板列表/fallback。

## generator API（index.ts）

- `/generate`：默认 template = text_ai；任意 template 入参经 normalizeTemplateName 归一化；
  返回的 `template` 字段一定是正式模板名（不再返回 ai-tool/ai-chat/ai-image）。
- `/templates`：`templates` 主列表 = base + 6 正式模板；旧别名单独放 `deprecated_aliases`；
  `default_template = text_ai`。

## app_type ↔ template 映射

同名约定，三处一致：
- `core/capabilities/app_types.py` 的 `template` 字段
- `core/generator/src/codegen/template-registry.ts`
- `core/pipeline/runner.py` 的 codegen overlay（按 app_type 选 templates/<app_type>）

## 哪些页面来自目录模板 / 哪些被动态生成（诚实说明）

- **Node generator（/generate）**：复制 base + overlay templates/<official>，再按 PRD feature
  生成页（保留模板自带页 index/form/result/profile/chat/canvas）。
- **runner.py 的 Python codegen（demo 主流程）**：复制 base + overlay templates/<app_type>，
  但 form/result 等功能页内容由 `_build_feature_pages` 动态生成并覆盖 → 模板目录页面对该路径是
  **参考/骨架**，实际运行页以动态生成为准。这是两套并存的 codegen，本轮只收口了 Node generator
  的模板体系命名与 registry；runner 的模板入口也已统一为 6 类正式名。
- text_ai / image_ai 目录已有真实页面资源（form/result/chat、canvas）；
  ocr_scan / speech_ai / video_light / utility_tool 当前仅 README，依赖 base + PRD 动态页，
  **尚无专属页面资源**（未来可补，接口与命名已就位）。

## 当前未完成项（诚实）

- ocr_scan / speech_ai / video_light / utility_tool 缺专属目录页面资源（仅 README）。
- Node generator 与 runner.py 两套 codegen 尚未合并（本轮不在范围）。
