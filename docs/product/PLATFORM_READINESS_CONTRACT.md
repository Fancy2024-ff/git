# 平台就绪度字段契约（Platform Readiness Contract）

> submission-readiness-report.json 与 submit-status.json 的字段定义与职责边界。
> 唯一权威；任何消费方（runner/API/前端/测试）以此为准，不得自行发明语义。

## 三个易混概念（严格区分，禁止混用）

| 概念 | 含义 | 位置 |
|---|---|---|
| **can_upload** | 该平台当前**具备上传条件**（已配置授权 + 有 dist + 支持自动上传） | platform_readiness[].can_upload |
| **uploaded** | 该平台开发版**已实际上传成功** | platform_readiness[].uploaded |
| **upload_ready**（顶层） | 是否**存在至少一个平台 can_upload** | 顶层字段 |
| **upload_completed**（顶层） | 是否**存在至少一个平台 uploaded** | 顶层字段 |

要点：
- `upload_ready` 表示"能不能上传"，**上传失败不会改变它**（除非配置/dist 本身失效导致 can_upload 变 false）。
- `upload_completed` 表示"上没上成"。
- 两者**语义不同、不可互换**。历史上 runner 用 upload_ready=可上传、wechat/upload.py 误用 upload_ready=已上传，本轮已统一。

## submission-readiness-report.json 字段定义

顶层：
- `ready_to_submit` / `is_ready_to_submit`：是否零阻塞可提交（含人工截图/真机，故通常 false）
- `upload_ready`：∃ 平台 can_upload
- `upload_completed`：∃ 平台 uploaded
- `review_ready`：∃ 目标平台可进入审核提交阶段（见下）
- `code_generated` / `build_passed` / `qa_passed` / `materials_ready` / `runtime_ready` / `runnable_level`
- `blocking_issues` / `warning_issues` / `human_actions`：展示层说明，**不是 review_ready 的唯一真相源**
- `platform_readiness[]` / `rejected_platforms[]`

platform_readiness[] 每项：
- `platform` / `name_cn` / `name_en` / `status` / `automation_level` / `submit_url`（均来自 registry.py）
- `configured` / `missing_fields`
- `can_upload` / `uploaded` / `upload_status`(not_uploaded|uploaded|upload_failed)
- `ready`（上游就绪可进入流程）/ `next_action` / `upload_path`

## review_ready 定义（平台层判定，非 runner 临时拼）

`review_ready = ∃ 目标平台满足：configured + uploaded + qa_passed + materials_ready + 无人工阻塞`

- 人工阻塞 = blocking_issues 中的"截图/真机"类。
- **上传成功 ≠ review_ready**：微信即便 uploaded=true，因仍需人工截图/真机/后台提审，review_ready 仍为 false。
- 判定逻辑在 `core/platforms/common/readiness.py:compute_review_ready`，runner 与 wechat/upload 均调用它，不各自拼。

## submit-status.json 与 readiness 的职责边界

| artifact | 职责 |
|---|---|
| `submit-status.json` | 各平台**流转状态**：upload_status / review_status / release_status / last_action_by |
| `submission-readiness-report.json` | **能否提交审核**的总判定 + 平台就绪明细（含 can_upload/uploaded/upload_ready/upload_completed/review_ready） |

两者由同一次上传同时更新（`update_submit_status` + `update_submission_readiness`），**不矛盾**。

## registry.py 是平台元数据主真相源

- 平台名称/status/automation_level/submit_url/upload_target/动作实现状态 → 一律经 `core/platforms/registry.py` 函数获取。
- `data/platforms/platform-registry.json` 仅作 registry.py 的 **legacy backing data**（富字段来源），业务层不直接读它。
- 唯一例外：`gap_check_agent`（分类/覆盖打分）仍直接读该 JSON 做 fit/coverage 评估——属 classification 域，非平台行为元数据。

## 上传成功 / 失败后的状态变化

成功：
- platform_readiness[wechat]：uploaded=true / upload_status=uploaded / next_action=去后台提审
- 顶层：upload_completed=true；**upload_ready 不变**；**review_ready 仍 false**（人工阻塞）

失败：
- platform_readiness[wechat]：uploaded=false / upload_status=upload_failed
- 顶层：upload_completed=false；**upload_ready 不漂移**（平台仍具上传条件）；blocking_issues 追加"微信上传失败:…"（去重）

## 当前微信做到哪一步

- ✅ 开发版上传（miniprogram-ci，真实代码路径，mock subprocess 验证）
- ✅ 状态一致（submit-status ↔ readiness）
- ❌ 自动提交审核（未做，需人工去 mp.weixin.qq.com）
- 不把"开发版上传成功"写成"自动审核完成"。
