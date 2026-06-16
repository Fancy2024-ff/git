# 能力工厂架构（Capability Factory）

## 为什么从单模板升级到 6 类能力工厂

旧架构 codegen 写死只复制 `base + ai-tool` 文本模板，无论扫到什么 App 都生成"文本框进、文本框出"。
证件照、抠图、OCR、配音等复杂 App 会被错误生成成文本工具，且无法表达"能上架但不能真用"。

升级目标：扫到任意热门 App → 识别类型 → 选对模板 → 诚实表达运行能力。

## 六类 app_type

| app_type | 中文 | 模板 | 核心能力 | 真实状态 |
|---|---|---|---|---|
| text_ai | 文本 AI | text_ai | text.generate | **真实可运行**（中转站已通） |
| image_ai | 图像 AI | image_ai | image.process | 完整架构+模板+状态机，**provider missing** |
| ocr_scan | OCR 扫描 | ocr_scan | vision.ocr | 架构+模板就位，stub |
| speech_ai | 语音 AI | speech_ai | speech.tts/asr | 架构+模板就位，stub |
| video_light | 轻视频 | video_light | video.process | 架构+模板就位，stub |
| utility_tool | 实用工具 | utility_tool | utility.execute | 本地能力，ready |

## 五层架构

1. **分类层** `core/agents/classification/classifier.py`
   规则 + LLM 双轨，LLM 失败 fallback 规则。产出 `app-classification.json`。
2. **能力适配层** `core/capabilities/`
   统一 adapter 接口 + registry，供应商可替换。text/utility 真实，其余 stub。
   产出 `capability-registry-snapshot.json`。
3. **模板矩阵层** `core/generator/src/templates/{6类}/` + `runner.py:_build_feature_pages`
   按 app_type 生成不同能力页面（含 5 态）。产出 `generator-capability-report.json`。
4. **运行支撑层** `runner.py:_write_capability_reports`
   产出 `runtime-capability-status.json`，runnable_level 五档。
5. **上架就绪层** `runner.py:build_submission_readiness`
   升级 `submission-readiness-report.json`：code/build/qa/materials/upload/review/runtime 分阶段。

## runnable_level 分级标准

- `shell_only`：仅页面骨架
- `buildable`：可构建可提交，但所需能力**全部**未接入（如 image_ai 无图像 API）
- `submit_ready`：材料齐可提交
- `partially_runtime_ready`：**部分**能力就位
- `runtime_ready`：能力**全部**就位，可真实运行（如 text_ai）

## 单一事实来源

`core/capabilities/app_types.py` 定义 6 类（关键词/能力/模板/可行性/约束）。
前端镜像 `apps/web/src/data/appTypes.ts`。分类、能力、codegen、前端全部读它。

## 诚实原则

没有真实 provider 的能力一律 `configured=false` + `status=provider_missing`，
runnable_level 如实降级，绝不返回假成功。"能上架"（空壳可提交）与"真能用"（runtime_ready）严格区分。
