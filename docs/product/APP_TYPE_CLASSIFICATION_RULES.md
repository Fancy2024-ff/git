# App 类型分类规则

实现：`core/capabilities/app_types.py`（规则）+ `core/agents/classification/classifier.py`（规则/LLM 调度）。

## 六类分类标准

按关键词命中数打分，最高分胜出。关键词见 `app_types.py:APP_TYPES[*].keywords`。

| app_type | 命中关键词示例 |
|---|---|
| text_ai | write, 翻译, summar, chat, 助手, 文案, 语法, 问答 |
| image_ai | photo, 证件照, 抠图, background, avatar, 头像, 风格, 增强, 修复 |
| ocr_scan | ocr, scan, 扫描, 识别, document, 票据, 发票, 提取 |
| speech_ai | speech, 语音, 配音, tts, 朗读, 字幕, asr, 听写 |
| video_light | video, 视频, 封面, 脚本, 字幕, 转码, 短视频 |
| utility_tool | calculat, 计算, convert, 转换, 查询, 工具, 表单 |

无命中 → 回退 `text_ai`（DEFAULT_APP_TYPE），confidence ≤ 0.4。

## miniapp_feasibility 判断

取该类型的 `default_feasibility`：
- text_ai / utility_tool：high（纯文本/本地逻辑，小程序天然适配）
- image_ai / ocr_scan / speech_ai：medium（依赖云端能力 API）
- video_light：low（仅轻量入口，重型剪辑不适合小程序）

LLM 模式下允许 LLM 覆盖 feasibility，但 app_type 必须是合法 6 类之一，否则报错 fallback。

## required_capabilities 推导

由 app_type 直接映射（`APP_TYPES[*].capabilities`），**不让 LLM 自由编造**，保证与能力注册表对齐：
- text_ai → text.generate
- image_ai → image.process
- ocr_scan → vision.ocr
- speech_ai → speech.tts, speech.asr
- video_light → video.process
- utility_tool → utility.execute

## blocking_constraints 判定

取该类型的 `constraints`（小程序固有限制），例如：
- image_ai：图像处理依赖云端 API，包体积/算力不支持离线模型
- video_light：仅轻量入口，重型本地剪辑不支持
LLM 模式可补充，但默认以类型约束为底。

## 规则 vs LLM

- USE_LLM=false：纯规则（classify_by_rules）
- USE_LLM=true：LLM 分类 + 解释；**失败必 fallback 规则**，标 llm_fallback=true，不中断 pipeline
