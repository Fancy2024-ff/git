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

---

# 能力层 v1 实现结构（core/capabilities）

> 本节描述能力层 v1 落地后的实际代码结构（第一阶段补齐）。

## 什么是 capability factory

`core/capabilities/` 是**全项目唯一的能力抽象层**。所有"调用 AI / 外部能力"的逻辑都收敛到这里，
不再散落进 runner.py、API 路由、前端组件。它把 6 类能力统一成「adapter（稳定接口）+ provider（可替换实现）+ 统一状态」。

## 为什么把复杂能力抽象到这里

- 图像/OCR/语音/视频每类的调用方式、异步性、失败模式都不同；散落会让 runner.py 再次膨胀。
- 统一 adapter 后：换 provider 不改业务层；新增能力类型只在 registry 登记一处。
- 状态统一表达，pipeline/API/前端拿到的是同一份 snapshot，不各自拼状态。

## 目录结构

```
core/capabilities/
├─ __init__.py        # 导出统一抽象
├─ status.py          # CapabilityStatus / RunnableLevel（状态单一事实源）
├─ schemas.py         # CapabilityResult / CapabilitySpec（数据结构单一事实源）
├─ base.py            # BaseAdapter / BaseProvider（统一基类）
├─ app_types.py       # 6 类 App 类型定义（App 类型单一事实源）
├─ registry.py        # 能力注册表（能力单一事实源）
├─ text/    (adapter + schemas + providers/local_or_existing_llm.py)  # 真实
├─ image/   (adapter + schemas + providers/stub.py)                   # 复杂范式，stub
├─ vision/  (adapter + schemas + providers/stub.py)                   # stub
├─ speech/  (adapter + schemas + providers/stub.py)                   # stub
├─ video/   (adapter + schemas + providers/stub.py)                   # stub
└─ utility/ (adapter + schemas + providers/local.py)                  # 本地 ready
```

## 六类能力当前状态

| capability_id | adapter | provider | 状态 | 接入需要 |
|---|---|---|---|---|
| text.generate | TextAdapter | ExistingLLMProvider | **configured/runtime_ready** | ANTHROPIC_API_KEY（已配） |
| image.process | ImageAdapter | ImageStubProvider | provider_missing | IMAGE_API_KEY + IMAGE_API_BASE |
| vision.ocr | VisionAdapter | VisionStubProvider | provider_missing | VISION_API_KEY |
| speech.tts(/asr) | SpeechAdapter | SpeechStubProvider | provider_missing | SPEECH_API_KEY |
| video.process | VideoAdapter | VideoStubProvider | provider_missing | VIDEO_API_KEY |
| utility.execute | UtilityAdapter | LocalUtilityProvider | **runtime_ready** | 无（本地） |

## app_type 与 capability 映射

`app_types.py` 是唯一权威：app_type → display_name / default_template / required_capabilities /
typical_operations / feasibility。registry 由 app_type 推导所需能力，不在别处重复判断。

| app_type | required_capabilities | template |
|---|---|---|
| text_ai | text.generate | text_ai |
| image_ai | image.process | image_ai |
| ocr_scan | vision.ocr | ocr_scan |
| speech_ai | speech.tts, speech.asr | speech_ai |
| video_light | video.process | video_light |
| utility_tool | utility.execute | utility_tool |

## 状态定义

- `configured`：已配置可真实调用
- `provider_missing`：需要外部 provider 但缺 key（声明了 required_env，可变真实）
- `stub`：纯占位，无 env 路径（当前无此类）
- `runtime_ready`：可真实运行（本地能力或已配置 provider）
- `degraded`：运行时部分失败/降级

上层映射：registry 的 `build_capability_snapshot(app_type)` 产出 `runnable_level`
（shell_only/buildable/runtime_ready），pipeline/readiness 再叠加平台授权得到 upload_ready/review_ready。

## image 作为第一条复杂能力线的意义

image 是唯一带**异步任务接口**（create_task → poll_task）的能力，为所有慢速能力（图像/视频）立范式：
- 4 个操作：remove_background / id_photo / avatar_style / enhance
- 未配置 provider 时如实 provider_missing，create_task 返回 task_id=None，**绝不 setTimeout 假完成**
- 配置 IMAGE_API_KEY + IMAGE_API_BASE 后自动 configured，在 adapter 标注的接入点替换真实调用即可

## 如何扩展 provider（不改业务层）

1. 在 `<capability>/providers/` 新增 `<vendor>.py`，继承 `BaseProvider`，实现 `is_configured/required_env/execute`
2. 在对应 adapter 的 `__init__` 换绑该 provider（或按 env 选择）
3. registry / snapshot / artifact / 前端自动反映新状态——**业务层、模板层、API 层均不动**
