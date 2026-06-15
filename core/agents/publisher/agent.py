"""
Publisher Agent - Handles mini-program submission to various platforms.

For MVP: prepares submission package and provides manual submission guidance.
Full automation (CI/CD upload, API submission) is Phase 2.
"""

import json
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from shared.models import MiniAppProject, MiniProgramPlatform
from shared.llm import get_llm
from config.settings import DATA_DIR


def run_publisher(project: MiniAppProject) -> dict:
    """
    Main publishing flow:
    1. Validate the project is ready for submission
    2. Prepare platform-specific packages
    3. Generate submission metadata (descriptions, screenshots notes)
    4. Submit or provide manual instructions

    Returns submission status per platform.
    """
    results = {}

    if not project.project_path:
        return {"error": "No project path available"}

    project_path = Path(project.project_path)
    if not project_path.exists():
        return {"error": f"Project path does not exist: {project_path}"}

    # Step 1: Validate project structure
    validation = _validate_project(project_path)
    if not validation["valid"]:
        return {"error": f"Validation failed: {validation['issues']}"}

    # Step 2: Generate submission metadata using LLM
    metadata = _generate_submission_metadata(project)

    # Step 3: Prepare and submit for each target platform
    for platform in project.target_platforms:
        result = _submit_to_platform(project, platform, metadata)
        results[platform.value] = result

    # Step 4: Save submission report
    _save_submission_report(project, results)

    return results


def _validate_project(project_path: Path) -> dict:
    """Validate that the project has required files for submission."""
    issues = []

    # Check essential files (uni-app CLI places configs under src/)
    required_files = ["src/manifest.json", "src/pages.json"]
    for f in required_files:
        if not (project_path / f).exists():
            issues.append(f"Missing {f}")

    # Check pages directory
    pages_dir = project_path / "src" / "pages"
    if not pages_dir.exists():
        issues.append("Missing src/pages directory")
    elif not any(pages_dir.iterdir()):
        issues.append("No pages found in src/pages")

    # Check manifest has required fields
    manifest_path = project_path / "src" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not manifest.get("name"):
            issues.append("manifest.json missing 'name'")

    return {"valid": len(issues) == 0, "issues": issues}


def _generate_submission_metadata(project: MiniAppProject) -> dict:
    """Use LLM to generate platform submission descriptions, tags, categories."""
    llm = get_llm(max_tokens=2048)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a mini-program publishing specialist. Generate submission metadata
that maximizes approval rates and discoverability.

For Chinese platforms (WeChat, Alipay, Douyin): write in Chinese.
For international platforms (Telegram, LINE): write in English.

Return JSON with: title, short_description (max 120 chars), full_description,
tags (array of 5), category, privacy_statement.""",
        ),
        (
            "human",
            """Generate submission metadata for this mini-program:
App name: {app_name}
Summary: {summary}
Features: {features}
Target platforms: {platforms}

Important: descriptions should be professional, highlight AI capabilities,
and comply with platform content policies (no exaggerated claims).""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()

    prd = project.prd
    features_text = ""
    if prd and prd.core_features:
        features_text = ", ".join(f.get("name", "") for f in prd.core_features)

    try:
        result = chain.invoke({
            "app_name": project.app_name,
            "summary": prd.summary if prd else "",
            "features": features_text,
            "platforms": ", ".join(p.value for p in project.target_platforms),
        })
        return result
    except Exception as e:
        print(f"[Publisher] Metadata generation failed: {e}")
        return {
            "title": project.app_name,
            "short_description": f"{project.app_name} - AI 智能助手",
            "full_description": prd.summary if prd else "",
            "tags": ["AI", "工具", "效率"],
            "category": "工具",
            "privacy_statement": "本小程序不收集用户敏感信息。",
        }


def _submit_to_platform(
    project: MiniAppProject,
    platform: MiniProgramPlatform,
    metadata: dict,
) -> dict:
    """
    Submit to a specific platform.
    For MVP, generates instructions rather than actual API submission.
    """
    submitters = {
        MiniProgramPlatform.WECHAT: _submit_wechat,
        MiniProgramPlatform.ALIPAY: _submit_alipay,
        MiniProgramPlatform.DOUYIN: _submit_douyin,
        MiniProgramPlatform.TELEGRAM: _submit_telegram,
        MiniProgramPlatform.LINE: _submit_line,
    }

    submitter = submitters.get(platform, _submit_generic)
    return submitter(project, metadata)


def _submit_wechat(project: MiniAppProject, metadata: dict) -> dict:
    """
    WeChat Mini Program submission.

    Full automation requires:
    - miniprogram-ci npm package
    - Upload key from WeChat Open Platform
    - AppID configured

    For MVP: prepare the package and return manual instructions.
    """
    return {
        "platform": "wechat",
        "status": "ready_for_manual_submission",
        "instructions": [
            "1. 打开微信开发者工具",
            f"2. 导入项目：{project.project_path}",
            "3. 在 manifest.json 中填入 AppID",
            "4. 点击「上传」按钮",
            f"5. 版本描述填写：{metadata.get('short_description', '')}",
            "6. 登录 mp.weixin.qq.com 提交审核",
        ],
        "metadata": metadata,
        "automation_ready": False,
        "required_for_automation": ["WECHAT_APPID", "WECHAT_UPLOAD_KEY"],
    }


def _submit_alipay(project: MiniAppProject, metadata: dict) -> dict:
    """Alipay Mini Program submission."""
    return {
        "platform": "alipay",
        "status": "ready_for_manual_submission",
        "instructions": [
            "1. 打开支付宝小程序开发者工具",
            f"2. 导入项目：{project.project_path}",
            "3. 配置 AppID",
            "4. 点击「上传」",
            "5. 登录 open.alipay.com 提交审核",
        ],
        "metadata": metadata,
        "automation_ready": False,
    }


def _submit_douyin(project: MiniAppProject, metadata: dict) -> dict:
    """Douyin Mini Program submission."""
    return {
        "platform": "douyin",
        "status": "ready_for_manual_submission",
        "instructions": [
            "1. 打开抖音开发者工具",
            f"2. 导入项目：{project.project_path}",
            "3. 配置 AppID",
            "4. 上传代码并提审",
        ],
        "metadata": metadata,
        "automation_ready": False,
    }


def _submit_telegram(project: MiniAppProject, metadata: dict) -> dict:
    """Telegram Mini App submission — auto-deploy when configured."""
    from config.settings import TELEGRAM_BOT_TOKEN, CLOUDFLARE_API_TOKEN

    if TELEGRAM_BOT_TOKEN and CLOUDFLARE_API_TOKEN:
        # Auto-deploy available
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
            from deploy_telegram import deploy_telegram

            app_info = {
                "name_cn": project.app_name,
                "name": project.app_name,
                "description_cn": metadata.get("full_description", ""),
            }
            output_dir = Path(project.project_path).parent if project.project_path else None

            if output_dir and output_dir.exists():
                result = deploy_telegram(
                    job_id=project.id or "manual",
                    output_dir=output_dir,
                    app_info=app_info,
                    opportunity={"target_platforms": ["telegram"]},
                )
                return {
                    "platform": "telegram",
                    "status": result.get("status", "unknown"),
                    "webapp_url": result.get("webapp_url", ""),
                    "bot_link": result.get("bot_link", ""),
                    "metadata": metadata,
                    "automation_ready": True,
                    "automated": True,
                }
        except Exception as e:
            print(f"[Publisher] Telegram auto-deploy failed: {e}")

    # Fallback to manual instructions
    return {
        "platform": "telegram",
        "status": "ready_for_manual_submission",
        "instructions": [
            "1. Contact @BotFather to create a bot",
            "2. Set up Web App URL via /newapp",
            f"3. Deploy the project from: {project.project_path}",
            "4. Configure the Web App URL in BotFather",
        ],
        "metadata": metadata,
        "automation_ready": False,
    }


def _submit_line(project: MiniAppProject, metadata: dict) -> dict:
    """LINE Mini App submission."""
    return {
        "platform": "line",
        "status": "ready_for_manual_submission",
        "instructions": [
            "1. Register on LINE Developers Console",
            "2. Create a LIFF (LINE Front-end Framework) app",
            f"3. Deploy the project from: {project.project_path}",
            "4. Submit for review via Console",
        ],
        "metadata": metadata,
        "automation_ready": False,
    }


def _submit_generic(project: MiniAppProject, metadata: dict) -> dict:
    """Generic fallback for unsupported platforms."""
    return {
        "platform": "unknown",
        "status": "unsupported",
        "error": "Platform not yet supported for submission",
    }


def _save_submission_report(project: MiniAppProject, results: dict) -> None:
    """Save submission report to data/reports/."""
    reports_dir = DATA_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "project_id": project.id,
        "app_name": project.app_name,
        "submitted_at": datetime.now().isoformat(),
        "platforms": results,
    }

    filename = f"submission_{project.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    (reports_dir / filename).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Publisher] Report saved: {filename}")
