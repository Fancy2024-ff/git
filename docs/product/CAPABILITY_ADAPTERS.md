# 能力适配层（Capability Adapters）

实现：`core/capabilities/`。把 6 类能力抽象成统一 adapter，供应商可替换。

## 接口设计

`base.py`：
- `BaseAdapter`：`is_configured()` / `config_requirements()` / `run(operation, **kwargs)` / `spec()`
- `CapabilityResult`：`ok / configured / data / error / provider` —— configured=False 表示"未接入"，非"失败"
- `CapabilitySpec`：`capability_id / provider / configured / supported_operations / automation_level / config_requirements / status`

`registry.py`：capability_id → adapter，提供 `capability_status` / `split_configured` / `snapshot`。

## 各能力状态

| capability_id | adapter | provider | 需要配置 | 当前 |
|---|---|---|---|---|
| text.generate | TextAdapter | anthropic(_proxy) | ANTHROPIC_API_KEY | **真实**（已配） |
| image.process | ImageAdapter | stub | IMAGE_API_KEY + IMAGE_API_BASE | provider_missing |
| vision.ocr | VisionAdapter | stub | VISION_API_KEY | provider_missing |
| speech.tts | SpeechAdapter | stub | SPEECH_API_KEY | provider_missing |
| video.process | VideoAdapter | stub | VIDEO_API_KEY | provider_missing |
| utility.execute | UtilityAdapter | local | 无 | **ready**（本地） |

## provider 如何接入

以 image.process 为例：
1. 配置 `.env`：`IMAGE_API_KEY=xxx` `IMAGE_API_BASE=https://...`（可选 `IMAGE_API_PROVIDER`）
2. `ImageAdapter.is_configured()` 自动变 True，registry/artifact/前端随之显示"已配置"
3. 在 `ImageAdapter.create_task / poll_task / _run` 的注释标注点替换为真实 API 调用
4. 业务层（runner.py）与模板层（生成的小程序）**无需改动** —— 接口不变

异步任务链路（image 已就位）：`create_task → poll_task → result`，供慢速图像处理使用。

## 缺配置时如何 fallback

- adapter 层：`run()` 检测未配置 → 返回 `ok=False, configured=False`，错误信息说明缺哪些 env
- pipeline 层：`_write_capability_reports` 把缺失能力写入 missing_capabilities，runnable_level 降级
- 前端：生产线能力芯片显示"未接入"，上架中心横幅显示"可上架但运行能力未接入"
- 生成的小程序：调 API 失败时页面显示"X 能力未接入（需配置 Y API）"，不假成功
