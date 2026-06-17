# 平台层模式（core/platforms）

> 微信是第一条按此模式落地的平台样板。后续 alipay / douyin / telegram 照此扩展，不再各写一套。

## 为什么需要 common + registry

最初只有 `core/platforms/wechat/`，微信上传结果是平台私有的裸 dict。问题：
- 每个平台各写一套返回结构 → 状态字符串不统一、消费方难复用
- 没有"平台层有哪些、各支持什么动作、实现到什么程度"的单一事实源

为此补齐两块公共骨架：
- `core/platforms/common/`：通用数据结构 + 统一状态
- `core/platforms/registry.py`：平台单一事实源

## 平台层公共结构

### common/status.py（统一状态，不许各平台自造字符串）
- `AuthStatus`：configured / not_configured
- `UploadStatus`：not_uploaded / uploaded / upload_failed
- `ReviewStatus`：review_not_submitted / pending / passed / rejected
- `UploadErrorCode`：config_missing / dist_missing / cli_missing / upload_disabled / auth_failed / upstream_failed / timeout
- `to_submit_status_value()`：公共态 → submit-status.json 历史字段（uploaded/failed/not_started），兼容前端

### common/models.py（通用数据结构）
- `PlatformAuthStatus`：授权状态 + 缺失字段
- `PlatformUploadResult`：**各平台上传统一结果**，`.to_dict()` 同时输出兼容历史前端的 status/tool/next_action 字段
- `PlatformReviewStatus`：审核状态
- `PlatformNextAction`：owner(agent/human) + text

### registry.py（平台单一事实源）
- `list_platforms()` / `get_platform(id)`
- `supports_action(id, action)`：仅 `implemented` 才算真支持（wechat.upload=implemented，wechat.review=not_implemented）
- `snapshot()`：平台清单 + automation_level + 各动作实现状态 + 已实现上传的平台列表

当前注册：wechat(upload 已实现 / review 未做)、alipay/douyin/telegram(占位 not_implemented)。

## wechat 如何作为第一条样板

```
apps/api (薄路由) → core/platforms/wechat/upload.py（平台执行入口，产出 PlatformUploadResult）
  → core/integrations/platform_clis/miniprogram_ci.py（CLI 唯一落点）
upload 结果 → update_submit_status() + update_submission_readiness()（双 artifact 联动，状态一致）
```
- upload.py 使用 common 的 UploadStatus / UploadErrorCode / PlatformUploadResult，不再私有 dict
- registry 描述 wechat 的 upload 能力

## 后续 alipay / douyin / telegram 如何照此扩展

1. 在 `registry.py` 把对应平台的 `actions.upload` 从 not_implemented 改为 implemented
2. 新建 `core/platforms/<platform>/upload.py`，复用 `common/models.PlatformUploadResult` + `common/status`
3. 平台特有 CLI/HTTP 放 `core/integrations/platform_clis/` 或对应 integrations 子目录
4. 上传后同样调 update_submit_status + update_submission_readiness 保持状态一致
5. API 加一条薄路由（或复用通用 `/api/platforms/{id}/upload`），不在路由里写平台逻辑

**原则**：平台差异收敛在 `core/platforms/<platform>/`，CLI/vendor 细节收敛在 `core/integrations/`，
公共结构走 `common/`，清单走 `registry.py`。

---

## 补充（本轮）：registry 为唯一元数据源 + readiness 聚合

- `core/platforms/registry.py` 现为平台元数据**唯一访问入口**：以 `data/platforms/platform-registry.json`
  为 legacy backing，但业务层（runner/API）一律经 registry 函数获取
  （list_platforms / get_platform / supports_action / is_upload_automatable / get_submit_url /
  get_platform_display / build_platform_snapshot），不再直接读 JSON → 消灭两套真相。
- `core/platforms/common/readiness.py` 统一就绪度聚合：normalize_platform_readiness /
  compute_upload_ready / compute_upload_completed / compute_review_ready /
  merge_platform_upload_result / build_submission_readiness_summary。
  runner 与 wechat/upload 都调它，不各自拼 upload_ready/review_ready。
- 字段语义契约见 [PLATFORM_READINESS_CONTRACT.md](PLATFORM_READINESS_CONTRACT.md)。
