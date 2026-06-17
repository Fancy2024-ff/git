# 模板矩阵（Template Matrix）

## 设计

模板目录：`core/generator/src/templates/{app_type}/`（6 个，含 README 说明）。
**功能页内容**由 `core/pipeline/runner.py:_build_feature_pages(app_type, label)` 按类型生成，
保证 pages.json 稳定（index/form/result/profile 四页不变）→ build 永远可过。

codegen 流程：
1. 复制 `base` 骨架（package.json/manifest/pages.json/index/profile）
2. 叠加 `templates/{app_type}/` 资源（模板目录已统一为 6 类正式名；旧 ai-tool/ai-chat/ai-image 已迁移删除，见 GENERATOR_TEMPLATE_CONTRACT.md）
3. `_build_feature_pages` 按 app_type 写入差异化的 form.vue + result.vue

## 六类页面差异

| app_type | form 页（功能页） | result 页 | 能力调用 |
|---|---|---|---|
| text_ai | 文本输入框 | 文本结果+复制 | 本地占位（文本类 demo） |
| image_ai | 选图+参数(证件照/抠图/头像/增强)+上传 | 图片预览+保存到相册 | /api/image/process |
| ocr_scan | 拍照/选图 | 识别文本+复制 | /api/vision/ocr |
| speech_ai | 文本输入 | 音频播放 | /api/speech/tts |
| video_light | 视频链接+操作 | 文本结果 | /api/video/process |
| utility_tool | 结构化数值表单 | 结果卡片 | 本地计算 |

## 5 态视图

每类功能页含：空状态（未输入/未选图）、输入态、处理中（loading/disabled）、
成功（跳转结果页）、失败（errorMsg 红字明确提示"X 能力未接入"）。

## 共用 vs 专用

- 共用：base 骨架、index 首页、profile 个人中心、utils/request.ts、pages.json/manifest
- 专用：form.vue + result.vue（按 app_type 生成）；image_ai 额外有 chooseImage/saveImageToPhotosAlbum、
  speech_ai 有 innerAudioContext 播放

## 为什么页面在代码里生成而非纯模板文件

codegen 在模板叠加后会 `_write` form/result，纯模板文件会被覆盖。
把差异化内容放进 `_build_feature_pages`，既保证 build 稳定（pages.json 不变），
又让每类真正生成对应交互。模板目录保留 README 记录该类设计，供扩展参考。
