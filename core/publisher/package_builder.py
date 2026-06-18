"""core.publisher.package_builder — 提交审核包组装 + 人工操作指南。

职责：组装 publish-package/ 目录（各平台提交材料、摘要、人工指南）与
submit-status.json。平台差异来自 core.platforms.guides。
runner 只调 build_publish_package() / build_human_actions()。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.platforms.guides import (
    platform_guide,
    platform_checklist,
    submit_status as build_submit_status,
)
from core.runtime.artifacts import write_text, write_json


def build_human_actions(app: dict, job_id: str, output_dir: Path) -> str:
    """生成人工操作指南 human-actions.md 正文。"""
    return f"""# 人工操作清单 - {app['name_cn']}

> Job ID: {job_id}
> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 你现在需要做什么

系统已自动完成：需求分析、覆盖检查、PRD 生成、代码生成、质量检查、上架材料准备。
以下步骤需要你手动操作：

---

### 步骤 1：登录微信公众平台

1. 打开浏览器访问 https://mp.weixin.qq.com
2. 使用管理员微信扫码登录
3. 如果还没有小程序账号，点击「前往注册」注册一个

---

### 步骤 2：创建或选择小程序

- 如果是新项目：左侧菜单 →「开发管理」→「开发设置」→ 复制 AppID
- 如果已有小程序：直接进入对应小程序后台

---

### 步骤 3：上传代码

1. 下载并安装「微信开发者工具」
2. 打开开发者工具，选择「导入项目」
3. 项目目录选择：
   ```
   {output_dir / 'generated' / 'miniapp'}
   ```
4. 填入 AppID（从公众平台复制）
5. 点击「上传」按钮，填写版本号 1.0.0

---

### 步骤 4：填写小程序资料

在微信公众平台填写以下信息：

- **小程序名称**：{app['name_cn']}
- **简介**：参考 `listing-materials.md` 中的一句话简介
- **服务类目**：参考 `listing-materials.json` 中的 category_suggestion
- **关键词**：参考 `listing-materials.json` 中的 keywords

---

### 步骤 5：上传截图

准备 4-5 张小程序截图（750×1334 或 1125×2436）：
1. 首页截图
2. 核心功能页截图
3. 结果展示页截图
4. 个人中心截图

截图文案参考 `listing-materials.md`。

---

### 步骤 6：配置隐私政策和用户协议

1. 在公众平台「设置」→「用户隐私保护指引」中填写
2. 内容参考：`docs/privacy-policy.md`
3. 用户协议参考：`docs/user-agreement.md`

---

### 步骤 7：提交审核

1. 回到「版本管理」页面
2. 在「开发版本」中找到刚上传的代码
3. 点击「提交审核」
4. 填写审核备注（参考 listing-materials.md 中的审核备注）
5. 确认提交

---

### 步骤 8：记录审核结果

审核通常 1-7 个工作日，结果出来后请：
- 如果通过：在公众平台点击「发布」
- 如果拒绝：记录拒绝原因，反馈至系统进行复盘迭代

---

## 文件清单

本次生成的所有文件位于：
```
{output_dir}
```

| 文件 | 用途 |
|------|------|
| candidate.json | 选中的候选 App 信息 |
| analysis.json | 需求分析报告 |
| gap-check.json | 小程序平台覆盖检查 |
| opportunity-report.json | 机会评分 |
| prd.md | 产品需求文档（可读版） |
| prd.json | 产品需求文档（结构化） |
| miniapp/ | 生成的小程序项目代码 |
| qa-report.json | 质量检查报告 |
| listing-materials.md | 上架材料（可读版） |
| listing-materials.json | 上架材料（结构化） |
| human-actions.md | 本文件 |

---

*如有疑问，请联系技术负责人。*
"""


def build_publish_package(app: dict, job_id: str, output_dir: Path,
                          listing_md: str, listing_json: dict,
                          target_platforms: list[str]) -> str:
    """组装 publish-package/ 目录 + submit-status.json。返回 human-actions.md 正文。

    output_dir 下产出：
      - human-actions.md
      - publish-package/（listing、摘要、审核备注、人工指南、checklist、各平台目录）
      - submit-status.json
    """
    human_md = build_human_actions(app, job_id, output_dir)
    write_text(output_dir / "human-actions.md", human_md)

    pkg_dir = output_dir / "publish-package"
    pkg_dir.mkdir(exist_ok=True)
    write_text(pkg_dir / "listing-materials.md", listing_md)
    write_text(pkg_dir / "privacy-summary.md", f"# 隐私政策摘要\n\n{listing_json['privacy_summary']}")
    write_text(pkg_dir / "user-agreement-summary.md", f"# 用户协议摘要\n\n{listing_json['user_agreement_summary']}")
    write_text(pkg_dir / "review-notes.md", f"# 审核备注\n\n{listing_json['review_notes']}")
    write_text(pkg_dir / "human-submit-guide.md", human_md)
    write_json(pkg_dir / "platform-checklist.json", platform_checklist(target_platforms))

    # 各平台提交材料（平台差异来自 core.platforms.guides）
    for plat in target_platforms:
        plat_dir = pkg_dir / plat
        plat_dir.mkdir(exist_ok=True)
        write_text(plat_dir / "submit-guide.md", f"# {plat} 提交指南\n\n{platform_guide(plat)}")
        write_json(plat_dir / "required-materials.json",
                   {"platform": plat, "materials": listing_json.get("keywords", [])})
        write_text(plat_dir / "review-notes.md", f"# {plat} 审核备注\n\n{listing_json['review_notes']}")

    write_json(output_dir / "submit-status.json", build_submit_status(job_id, target_platforms))
    return human_md
