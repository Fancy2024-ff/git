"""6 类 app_type 的单一事实来源（Single Source of Truth）。

分类层、能力注册表、codegen、前端 snapshot 全部以此为准，杜绝定义漂移。
前端镜像见 apps/web/src/data/appTypes.ts（手工保持一致，字段名对齐）。
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────
# 6 类 app_type 定义
# ─────────────────────────────────────────────────────────────
# 每类字段：
#   id            稳定标识（写入 artifact 的 app_type）
#   name_cn       中文名
#   template      core/generator/src/templates/ 下的模板目录名
#   capabilities  所需能力 id（对应 capability registry）
#   keywords      规则分类用的关键词（命中越多越匹配）
#   default_feasibility  小程序可行性默认值 high/medium/low
#   constraints   该类常见的 blocking_constraints（小程序限制）

APP_TYPES: dict[str, dict] = {
    "text_ai": {
        "name_cn": "文本 AI",
        "template": "text_ai",
        "capabilities": ["text.generate"],
        "keywords": [
            "write", "writing", "翻译", "translate", "summar", "摘要", "chat", "助手",
            "assistant", "文案", "copywrit", "essay", "grammar", "语法", "问答", "qa",
            "paraphrase", "改写", "润色", "prompt", "gpt", "语言",
        ],
        "typical_operations": ['generate', 'chat'],
        "default_feasibility": "high",
        "constraints": [],
    },
    "image_ai": {
        "name_cn": "图像 AI",
        "template": "image_ai",
        "capabilities": ["image.process"],
        "keywords": [
            "photo", "image", "图片", "照片", "证件照", "id photo", "抠图", "background",
            "remove bg", "avatar", "头像", "style", "风格", "enhance", "增强", "修复",
            "restore", "老照片", "filter", "滤镜", "ai art", "绘画", "draw", "generate image",
            "图生图", "美化", "p图",
        ],
        "typical_operations": ['remove_background', 'id_photo', 'avatar_style', 'enhance'],
        "default_feasibility": "medium",
        "constraints": ["图像处理依赖云端图像 API，包体积与本地算力不支持离线模型"],
    },
    "ocr_scan": {
        "name_cn": "OCR 扫描识别",
        "template": "ocr_scan",
        "capabilities": ["vision.ocr"],
        "keywords": [
            "ocr", "scan", "扫描", "识别", "recognize", "document", "文档", "票据",
            "receipt", "invoice", "发票", "card", "卡证", "表格", "table", "text extract",
            "提取", "拍照识别",
        ],
        "typical_operations": ['ocr', 'document_extract', 'table_extract'],
        "default_feasibility": "medium",
        "constraints": ["识别依赖云端视觉 API"],
    },
    "speech_ai": {
        "name_cn": "语音 AI",
        "template": "speech_ai",
        "capabilities": ["speech.tts", "speech.asr"],
        "keywords": [
            "speech", "voice", "语音", "配音", "tts", "text to speech", "朗读", "read aloud",
            "字幕", "subtitle", "asr", "语音转文字", "transcri", "听写", "dubbing", "audio",
        ],
        "typical_operations": ['tts', 'asr'],
        "default_feasibility": "medium",
        "constraints": ["语音合成/识别依赖云端语音 API；部分平台录音权限受限"],
    },
    "video_light": {
        "name_cn": "轻视频能力",
        "template": "video_light",
        "capabilities": ["video.process"],
        "keywords": [
            "video", "视频", "封面", "cover", "脚本", "script", "剪辑入口", "字幕",
            "摘要", "transcode", "转码", "素材", "短视频", "clip",
        ],
        "typical_operations": ['summarize', 'cover_generate', 'metadata_extract'],
        "default_feasibility": "low",
        "constraints": ["仅提供轻量视频能力入口；重型本地剪辑小程序不支持", "视频处理依赖云端 API"],
    },
    "utility_tool": {
        "name_cn": "实用工具",
        "template": "utility_tool",
        "capabilities": ["utility.execute"],
        "keywords": [
            "calculat", "计算", "convert", "转换", "查询", "query", "tool", "工具",
            "效率", "表单", "form", "汇率", "单位", "倒计时", "记账", "checklist", "清单",
        ],
        "typical_operations": ['calculate', 'convert', 'query'],
        "default_feasibility": "high",
        "constraints": [],
    },
}

# 兜底类型：分类无法判断时回退到 text_ai（最稳、能力已就绪）
DEFAULT_APP_TYPE = "text_ai"

VALID_APP_TYPES = list(APP_TYPES.keys())


def get_app_type(app_type: str) -> dict:
    """取某个 app_type 的定义，未知则回退默认。"""
    return APP_TYPES.get(app_type, APP_TYPES[DEFAULT_APP_TYPE])


def template_for(app_type: str) -> str:
    return get_app_type(app_type)["template"]


def capabilities_for(app_type: str) -> list[str]:
    return list(get_app_type(app_type)["capabilities"])


def display_name_for(app_type: str) -> str:
    return get_app_type(app_type)["name_cn"]


def default_template_for(app_type: str) -> str:
    """default_template 与 template 同义（保留语义化别名供 registry/文档使用）。"""
    return get_app_type(app_type)["template"]


def typical_operations_for(app_type: str) -> list[str]:
    return list(get_app_type(app_type).get("typical_operations", []))


def feasibility_for(app_type: str) -> str:
    return get_app_type(app_type)["default_feasibility"]


def classify_by_rules(app: dict) -> dict:
    """纯规则分类：按关键词命中数打分，取最高分类型。

    返回 {app_type, app_type_confidence, miniapp_feasibility,
          required_capabilities, blocking_constraints, reasons, matched_keywords}
    无 LLM 时使用；也是 LLM 失败时的 fallback。
    """
    haystack = " ".join([
        str(app.get("name", "")),
        str(app.get("name_cn", "")),
        str(app.get("category", "")),
        str(app.get("description", "")),
        str(app.get("description_cn", "")),
        " ".join(app.get("features", []) or []),
        " ".join(app.get("features_cn", []) or []),
    ]).lower()

    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}
    for atype, spec in APP_TYPES.items():
        hits = [kw for kw in spec["keywords"] if kw.lower() in haystack]
        if hits:
            scores[atype] = len(hits)
            matched[atype] = hits

    if scores:
        best = max(scores, key=lambda k: scores[k])
        total = sum(scores.values())
        confidence = round(min(0.95, 0.4 + scores[best] / max(total, 1) * 0.55), 2)
    else:
        best = DEFAULT_APP_TYPE
        confidence = 0.3  # 没命中任何关键词 → 低置信回退

    spec = APP_TYPES[best]
    reasons = []
    if matched.get(best):
        reasons.append(f"命中 {best} 关键词: {', '.join(matched[best][:5])}")
    else:
        reasons.append(f"未命中明确关键词，回退默认类型 {DEFAULT_APP_TYPE}")
    reasons.append(f"小程序可行性默认: {spec['default_feasibility']}")

    return {
        "app_type": best,
        "app_type_confidence": confidence,
        "miniapp_feasibility": spec["default_feasibility"],
        "required_capabilities": list(spec["capabilities"]),
        "blocking_constraints": list(spec["constraints"]),
        "reasons": reasons,
        "matched_keywords": matched.get(best, []),
    }
