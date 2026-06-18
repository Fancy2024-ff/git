"""core.publisher.materials — 上架材料生成。

单一事实源：上架材料文案/配置只在这里。runner 调用 build_listing_materials。
"""

from __future__ import annotations


def build_listing_materials(app: dict, prd_json: dict) -> tuple[str, dict]:
    """生成完整的上架所需文案和配置（Markdown + JSON）。"""
    platforms_str = "、".join(prd_json["target_platforms"])

    materials_json = {
        "app_name_cn": app["name_cn"],
        "app_name_en": app["name"],
        "one_liner": f"{app['name_cn']} - {app['features_cn'][0]}，即用即走",
        "description": app["description_cn"] + f"\n\n核心功能：\n" + "\n".join([f"• {f}" for f in app["features_cn"]]),
        "category_suggestion": f"工具 > {'效率' if app['category'] == 'Productivity' else '生活' if app['category'] == 'Health & Fitness' else '图片' if app['category'] == 'Photography' else '教育' if app['category'] == 'Education' else '其他'}",
        "keywords": app["features_cn"][:5],
        "version_note": "v1.0.0 首次发布：支持核心 AI 功能、用户输入、结果展示、历史记录。",
        "privacy_summary": "收集用户输入文本（处理后不保留）、微信授权昵称头像、设备信息。不收集位置、通讯录等敏感信息。",
        "user_agreement_summary": "AI 辅助工具，生成内容仅供参考。用户对输入内容负责。",
        "screenshot_copywriting": [
            f"{app['name_cn']} - 首页",
            f"核心功能 - {app['features_cn'][0]}",
            "AI 处理结果展示",
            "个人中心 & 历史记录",
        ],
        "review_notes": f"本小程序为 AI 工具类应用，提供{app['features_cn'][0]}功能。所有 AI 处理在服务端完成，不涉及敏感内容生成。已配置内容安全过滤。",
        "risk_warnings": [
            "AI 生成内容需做内容安全审核",
            "免费额度限制需在页面明确展示",
            "隐私政策需在首次使用前展示并获得同意",
        ],
    }

    materials_md = f"""# {app['name_cn']} 上架材料

## 基本信息

| 项目 | 内容 |
|------|------|
| 中文名 | {materials_json['app_name_cn']} |
| 英文名 | {materials_json['app_name_en']} |
| 一句话简介 | {materials_json['one_liner']} |
| 服务类目 | {materials_json['category_suggestion']} |
| 版本号 | 1.0.0 |

## 详细简介

{materials_json['description']}

## 关键词

{', '.join(materials_json['keywords'])}

## 版本说明

{materials_json['version_note']}

## 隐私政策摘要

{materials_json['privacy_summary']}

## 用户协议摘要

{materials_json['user_agreement_summary']}

## 截图文案

1. {materials_json['screenshot_copywriting'][0]}
2. {materials_json['screenshot_copywriting'][1]}
3. {materials_json['screenshot_copywriting'][2]}
4. {materials_json['screenshot_copywriting'][3]}

## 审核备注

{materials_json['review_notes']}

## 风险提示

{"".join([f'- {r}' + chr(10) for r in materials_json['risk_warnings']])}
"""

    return materials_md, materials_json
