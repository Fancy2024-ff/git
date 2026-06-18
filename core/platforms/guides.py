"""core.platforms.guides — 各平台提交指南与差异规则（单一事实源）。

平台差异（提交步骤/所需材料/状态）只在这里。publisher 调用本模块组装平台材料。
"""

from __future__ import annotations

from datetime import datetime

from core.qa.readiness import platform_auth_status


# 平台提交指南（平台差异规则的单一事实源）
PLATFORM_GUIDES = {
    "wechat": "1. 登录 mp.weixin.qq.com\n2. 打开微信开发者工具导入 dist/build/mp-weixin\n3. 上传代码\n4. 填写资料\n5. 提交审核",
    "alipay": "1. 登录 open.alipay.com\n2. 创建应用\n3. 上传代码\n4. 填写资料\n5. 提交审核",
    "douyin": "1. 登录 developer.open-douyin.com\n2. 创建小程序\n3. 上传代码\n4. 提交审核",
    "telegram": "1. 联系 @BotFather 创建 Bot\n2. 使用 /newapp 创建 Web App\n3. 部署前端到 HTTPS URL\n4. 配置 WebApp URL\n5. 无需审核，部署即上线",
    "discord": "1. 创建 Discord Application\n2. 配置 Activity URL\n3. 集成 Discord SDK\n4. 提交审核",
    "reddit": "1. 安装 devvit CLI\n2. 创建 Devvit App\n3. 本地开发调试\n4. 发布到社区",
    "line": "1. 创建 LINE Channel\n2. 配置 LIFF App\n3. 部署 Web App\n4. 提交审核",
}


def platform_guide(plat: str) -> str:
    """返回某平台的提交指南文本。"""
    return PLATFORM_GUIDES.get(plat, f"平台 {plat} 提交指南待补充")


def platform_checklist(platforms: list[str]) -> dict:
    """生成 platform-checklist.json 内容。"""
    return {
        "platforms": [
            {"platform": plat, "status": "pending", "submitted_at": None, "review_result": None}
            for plat in platforms
        ]
    }


def submit_status(job_id: str, platforms: list[str]) -> dict:
    """生成 submit-status.json 内容（含各平台授权配置状态）。"""
    return {
        "job_id": job_id,
        "platforms": [
            {
                "platform_id": plat,
                "configured": platform_auth_status(plat)[0],
                "can_upload": False,
                "upload_status": "not_started",
                "review_status": "not_submitted",
                "release_status": "not_released",
                "last_action_by": "system",
                "last_action_at": datetime.now().isoformat(),
                "next_action_owner": "human",
                "next_action": f"配置 {plat} 平台授权后自动上传",
            }
            for plat in platforms
        ],
    }
