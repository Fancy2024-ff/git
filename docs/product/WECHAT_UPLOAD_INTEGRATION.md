# 微信小程序上传接入（miniprogram-ci）

> 本轮把微信上传从 `apps/api/main.py` 里的占位接口（返回 "miniprogram-ci integration pending"）
> 升级为真正可执行的 miniprogram-ci 上传链路。

## 本轮接通了什么

- 微信**开发版上传**链路真打通：`dist 产物 → miniprogram-ci → 上传结果 → submit-status 联动`
- 上传逻辑从 API 层迁出，分三层：
  - `apps/api/main.py` —— 薄路由（鉴权 + job_id + 调 service）
  - `core/platforms/wechat/upload.py` —— 平台执行入口（auth/dist/CLI 校验 + 结果归一 + artifact 更新）
  - `core/integrations/platform_clis/miniprogram_ci.py` —— CLI 唯一封装（参数/解析/超时/错误映射）

## 调用方式

```
POST /api/platforms/wechat/upload
body: { "job_id": "<job>" }
```
返回：`upload_passed / status / provider / dist_path / appid / version / message / error_code / next_action`

## 需要哪些配置（data/platform-auth/wechat.json）

| 字段 | 必需 | 说明 |
|---|---|---|
| appid | ✅ | 小程序 AppID |
| private_key_path | ✅ | 上传密钥文件路径（从微信后台下载） |
| upload_enabled | ✅(true) | 未置 true 则 upload_disabled |
| version | 否 | 上传版本号，默认 1.0.0 |
| desc / robot | 否 | 版本描述 / 机器人编号(1-30) |

另需运行环境有 **Node.js + npx**（miniprogram-ci 通过 `npx miniprogram-ci` 调用）。

## dist 路径从哪来

平台层 `resolve_project_path(job_dir)`：
1. 优先读 `data/outputs/{job}/qa-report.json` 的 `checks.dist_path`（构建产物真实路径）
2. 兜底 `data/outputs/{job}/generated/miniapp/dist/build/mp-weixin`
不存在 → `dist_missing`，不写死假路径。

## miniprogram-ci 怎么被调用

`miniprogram_ci.upload_project()` 拼接并执行：
```
npx miniprogram-ci upload --pp <project> --appid <appid> --pkp <key> --uv <version> --desc <desc> -r <robot>
```
- `validate_env_or_binary()` 先查 npx 可用性
- `parse_upload_result()` 按 exit code + 输出判定成功/失败并分类错误
- 错误码：cli_missing / invalid_config / dist_missing / auth_failed / timeout / upstream_failed
- subprocess 可注入（测试用 mock 走真实代码路径，本机无微信环境也能验证逻辑）

## 上传成功后下一步

`next_action = "去 mp.weixin.qq.com 后台提交审核"`，并把 submit-status.json 的 wechat 项更新为
`upload_status=uploaded / last_action_by=agent / review_status=not_submitted`。
前端提交中心实时显示「已上传开发版 + 下一步提审」。

## 失败如何表达（诚实）

config_missing / upload_disabled / dist_missing / cli_missing / auth_failed / upstream_failed / timeout
均如实返回 error_code + message + next_action；submit-status 标 `upload_status=failed`。绝不假成功。

## 当前还没做什么

- **自动提交审核**：本轮范围外（`review.py` 返回 not_implemented）。微信提审涉及后台人工确认，
  开发版上传后仍需人工去 mp.weixin.qq.com 提审。
- 其它平台（支付宝/抖音）自动上传：未做，仅微信。
- 审核结果回填：未做。

---

## 补充（本轮）：readiness 真联动 + 平台公共骨架

### submit-status 与 readiness 的区别

| artifact | 角色 | 上传后变化 |
|---|---|---|
| `submit-status.json` | 各平台**流转状态**(upload/review/release) | wechat 项 upload_status=uploaded、last_action_by=agent |
| `submission-readiness-report.json` | **能否提交审核**的总判定 + 平台就绪明细 | platform_readiness[wechat].uploaded=true、upload_ready=true、blocking 清理上传失败项 |

本轮起两者**同步更新、不再矛盾**：上传后 API 同时调 `update_submit_status()` 与 `update_submission_readiness()`。

### 上传成功后系统状态如何变化

- submit-status: wechat `upload_status=uploaded`、`next_action=去 mp.weixin.qq.com 提审`
- readiness: `platform_readiness[wechat].uploaded=true / upload_status=uploaded`、顶层 `upload_ready=true`、
  顶层 `next_action=微信开发版已上传，下一步人工去微信后台提交审核`
- **review_ready 不会因上传成功置 true**；`ready_to_submit` 仍按业务判定（缺截图/真机测试等）

### 为什么上传成功 ≠ review_ready

上传只是把开发版推到微信后台。提交审核是另一步,需人工在 mp.weixin.qq.com 操作,且通常还要截图、真机测试。
因此系统严格区分「已上传开发版」与「可提交审核」,绝不把上传成功冒充为可提审。

### 上传失败后

- submit-status: `upload_status=failed`
- readiness: `platform_readiness[wechat].upload_status=upload_failed`、`upload_ready=false`、
  `blocking_issues` 追加「微信上传失败：<原因>」

---

## 补充（本轮）：readiness 语义统一

- 字段契约迁至 [PLATFORM_READINESS_CONTRACT.md](PLATFORM_READINESS_CONTRACT.md)（权威）。
- 关键修正：`upload_ready`=「可上传」（具备条件，失败不漂移），新增 `upload_completed`=「已上传成功」。
  上一轮误把 upload_ready 当「已上传」的问题已修复。
- `update_submission_readiness` 改为调 `common/readiness` 重算顶层 upload_ready/upload_completed/review_ready，
  与 runner 同一套逻辑，submit-status 与 readiness 不再矛盾。
- 上传成功仍 **不** 置 review_ready（微信需人工截图/真机/后台提审）。
