"""core.generator.prd_builder — PRD 生成（产品需求文档）。

落点理由：PRD 定义页面/功能/技术栈，是直接驱动代码生成的"规格"，
因此归在 generator（生成域），而非 growth（生成后的运营策略）。
runner 通过 build_prd 调用本模块。
"""

from __future__ import annotations


def build_prd(app: dict, opportunity: dict) -> tuple[str, dict]:
    """生成产品需求文档（Markdown + JSON）。"""
    features_md = "\n".join([f"- {f}" for f in app["features_cn"]])
    platforms_str = "、".join(opportunity["target_platforms"])

    prd_md = f"""# {app['name_cn']} 小程序 - 产品需求文档

## 产品概述

**产品名称**：{app['name_cn']}
**英文名**：{app['name']}
**产品形态**：小程序
**目标平台**：{platforms_str}
**机会评分**：{opportunity['opportunity_score']}/100

## 产品定位

将 {app['name']} 的核心功能以小程序形态提供给用户，实现即用即走、无需下载安装的轻量体验。

## 目标用户

{app['description_cn']}的目标人群，偏好在微信/支付宝/抖音生态内完成操作，不愿额外下载 App。

## 核心功能

{features_md}

## MVP 范围

首版聚焦以下功能：
1. {app['features_cn'][0]}（核心功能）
2. {app['features_cn'][1] if len(app['features_cn']) > 1 else '基础展示'}（辅助功能）
3. 用户输入表单
4. 结果展示页面
5. 历史记录（本地存储）

## 页面结构

- **首页** index：功能入口、快捷操作
- **表单页** form：用户输入核心信息
- **结果页** result：AI 处理结果展示、复制/分享
- **我的** profile：历史记录、设置

## 技术方案

- 框架：uni-app（跨端兼容微信/支付宝/抖音）
- 语言：Vue 3 + TypeScript
- 状态管理：Pinia
- API：RESTful，后端独立部署
- 存储：本地 Storage + 云端同步（Pro）

## 变现策略

- 免费版：每日 {3} 次使用额度
- Pro 版：¥{12}/月，无限使用
- 支付方式：微信支付 / 支付宝

## 开发周期

预计 {opportunity['estimated_dev_days']} 天完成 MVP。

## 风险评估

- 平台审核：需确保内容合规，不涉及敏感词
- 包大小：控制在 2MB 以内（微信主包限制）
- AI 依赖：后端 API 需保证 P95 < 2s 响应
"""

    prd_json = {
        "app_name": app["name"],
        "app_name_cn": app["name_cn"],
        "product_type": "miniapp",
        "target_platforms": opportunity["target_platforms"],
        "opportunity_score": opportunity["opportunity_score"],
        "core_features": app["features_cn"],
        "mvp_features": app["features_cn"][:2] + ["用户输入表单", "结果展示", "历史记录"],
        "pages": [
            {"path": "pages/index/index", "title": "首页", "type": "navigation"},
            {"path": "pages/form/form", "title": "表单", "type": "input"},
            {"path": "pages/result/result", "title": "结果", "type": "display"},
            {"path": "pages/profile/profile", "title": "我的", "type": "navigation"},
        ],
        "tech_stack": {
            "framework": "uni-app",
            "language": "Vue 3 + TypeScript",
            "state": "Pinia",
            "api": "RESTful",
        },
        "monetization": {"model": "freemium", "free_quota": 3, "pro_price": 12},
        "timeline_days": opportunity["estimated_dev_days"],
    }

    return prd_md, prd_json
