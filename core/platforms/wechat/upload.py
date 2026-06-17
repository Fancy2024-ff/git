"""微信开发版上传：平台层真实执行入口。

链路：auth 校验 → 解析 job dist/project 路径 → 调 miniprogram_ci → 统一结果 → 更新 submit-status。
未配置/无 dist/无 CLI/上传失败都诚实区分，绝不假成功。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# 让 integrations 可导入
_CORE = Path(__file__).resolve().parents[2]
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from platforms.wechat.auth import load_auth, validate_auth
from platforms.common.status import UploadStatus, UploadErrorCode
from platforms.common.models import PlatformUploadResult, PlatformNextAction


def _result(upload_passed, status, *, message="", error_code="", dist_path="",
            appid="", version="", next_action="", next_owner="human", raw_output="") -> dict:
    """统一上传返回结构（基于公共 PlatformUploadResult）。"""
    return PlatformUploadResult(
        platform_id="wechat",
        upload_passed=upload_passed,
        upload_status=status,                # UploadStatus.*
        provider="miniprogram-ci",
        dist_path=dist_path,
        appid=appid,
        version=version,
        message=message,
        error_code=error_code,
        raw_output=raw_output,
        next_action=PlatformNextAction(owner=next_owner, text=next_action) if next_action else None,
    ).to_dict()


def resolve_project_path(job_dir: Path) -> str:
    """解析 job 的 uni-app 项目路径（miniprogram-ci 上传的是 mp-weixin 产物目录）。

    优先用 qa-report.json 里记录的 dist_path（构建产物），其次推断默认路径。
    """
    job_dir = Path(job_dir)
    qa = job_dir / "qa-report.json"
    if qa.exists():
        try:
            checks = json.loads(qa.read_text(encoding="utf-8")).get("checks", {})
            dp = checks.get("dist_path")
            if dp and Path(dp).exists():
                return dp
        except Exception:
            pass
    default = job_dir / "generated" / "miniapp" / "dist" / "build" / "mp-weixin"
    return str(default) if default.exists() else ""


def upload_dev_version(
    *,
    job_dir: Path,
    platform_auth_dir: Path,
    runner=None,
    which=None,
) -> dict:
    """执行微信开发版上传。runner/which 可注入便于测试。"""
    from integrations.platform_clis import miniprogram_ci

    # 1) auth
    config = load_auth(platform_auth_dir)
    configured, missing = validate_auth(config)
    if not configured:
        return _result(False, UploadStatus.NOT_UPLOADED, error_code=UploadErrorCode.CONFIG_MISSING,
                       message=f"微信授权未配置（缺: {', '.join(missing)}）",
                       next_action="在 data/platform-auth/wechat.json 配置 appid 与 private_key_path")
    if not config.get("upload_enabled"):
        return _result(False, UploadStatus.NOT_UPLOADED, error_code=UploadErrorCode.UPLOAD_DISABLED,
                       appid=config.get("appid", ""),
                       message="upload_enabled 为 false，未开启自动上传",
                       next_action="将 wechat.json 的 upload_enabled 置为 true")

    # 2) dist/project
    project_path = resolve_project_path(job_dir)
    if not project_path:
        return _result(False, UploadStatus.UPLOAD_FAILED, error_code=UploadErrorCode.DIST_MISSING,
                       appid=config.get("appid", ""),
                       message="构建产物 dist/build/mp-weixin 不存在，请先构建",
                       next_action="先跑通 build/QA 生成 dist 产物")

    # 3) CLI 可用性
    kwargs = {}
    if which is not None:
        kwargs["which"] = which
    ok, miss = miniprogram_ci.validate_env_or_binary(**({"which": which} if which else {}))
    if not ok:
        return _result(False, UploadStatus.UPLOAD_FAILED, error_code=UploadErrorCode.CLI_MISSING,
                       appid=config.get("appid", ""), dist_path=project_path,
                       message=f"{miss} 不可用，无法调用 miniprogram-ci",
                       next_action="安装 Node.js + npx 后重试")

    # 4) 真实上传
    version = config.get("version", "1.0.0")
    run_kwargs = dict(
        appid=config["appid"],
        private_key_path=config["private_key_path"],
        project_path=project_path,
        version=version,
        desc=config.get("desc", "automated dev upload"),
        robot=int(config.get("robot", 1)),
    )
    if runner is not None:
        run_kwargs["runner"] = runner
    if which is not None:
        run_kwargs["which"] = which
    ci = miniprogram_ci.upload_project(**run_kwargs)

    if ci.success:
        return _result(True, UploadStatus.UPLOADED, appid=config["appid"], dist_path=project_path,
                       version=ci.version or version, message="开发版已上传到微信后台",
                       raw_output=ci.raw_output,
                       next_action="去 mp.weixin.qq.com 后台提交审核")
    # 失败：映射 CLI 错误码
    code_map = {
        "cli_missing": UploadErrorCode.CLI_MISSING,
        "auth_failed": UploadErrorCode.AUTH_FAILED,
        "timeout": UploadErrorCode.TIMEOUT,
        "dist_missing": UploadErrorCode.DIST_MISSING,
    }
    return _result(False, UploadStatus.UPLOAD_FAILED, appid=config["appid"], dist_path=project_path,
                   error_code=code_map.get(ci.error_code, UploadErrorCode.UPSTREAM_FAILED),
                   message=ci.message or "上传失败", raw_output=ci.raw_output,
                   next_action="检查私钥/appid/网络后重试")


def update_submit_status(job_dir: Path, upload_result: dict) -> None:
    """把上传结果写回 submit-status.json 的 wechat 项。永不抛异常。"""
    f = Path(job_dir) / "submit-status.json"
    if not f.exists():
        return
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        for plat in data.get("platforms", []):
            if plat.get("platform_id") == "wechat":
                plat["upload_status"] = "uploaded" if upload_result["upload_passed"] else "failed"
                plat["can_upload"] = bool(upload_result["upload_passed"]) or plat.get("can_upload", False)
                plat["last_action_by"] = "agent"
                plat["last_action_at"] = datetime.now().isoformat()
                plat["upload_provider"] = upload_result.get("provider", "miniprogram-ci")
                plat["upload_message"] = upload_result.get("message", "")
                plat["upload_error_code"] = upload_result.get("error_code", "")
                if upload_result["upload_passed"]:
                    plat["next_action_owner"] = "human"
                    plat["next_action"] = "去 mp.weixin.qq.com 后台提交审核"
                    plat["review_status"] = plat.get("review_status", "not_submitted")
                else:
                    plat["next_action"] = upload_result.get("next_action", "")
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def update_submission_readiness(job_dir: Path, upload_result: dict) -> None:
    """把上传结果真联动到 submission-readiness-report.json。永不抛异常。

    核心原则（与 submit-status 不矛盾）：
    - 上传成功 → wechat 项 can_upload=true、upload_status=uploaded、next_action=去后台提审；
      新增 upload_ready=true；但 review_ready 绝不因上传成功置 true（仍需人工提审 + 截图/真机）。
    - 上传失败 → wechat 项体现失败原因，加入 blocking_issues（去重），upload_ready=false。
    - 顶层 ready_to_submit/is_ready_to_submit 维持原业务判定（不因上传而置 true）。
    """
    f = Path(job_dir) / "submission-readiness-report.json"
    if not f.exists():
        return
    passed = bool(upload_result.get("upload_passed"))
    msg = upload_result.get("message", "")
    try:
        data = json.loads(f.read_text(encoding="utf-8"))

        # 1) platform_readiness 中 wechat 项联动
        for plat in data.get("platform_readiness", []):
            if plat.get("platform") == "wechat":
                if passed:
                    plat["uploaded"] = True
                    plat["upload_status"] = "uploaded"
                    plat["next_action"] = "开发版已上传，去 mp.weixin.qq.com 后台提交审核"
                else:
                    plat["uploaded"] = False
                    plat["upload_status"] = "upload_failed"
                    plat["next_action"] = upload_result.get("next_action", msg)

        # 2) upload_ready：是否有平台已成功上传开发版
        any_uploaded = any(p.get("uploaded") for p in data.get("platform_readiness", []))
        data["upload_ready"] = any_uploaded

        # 3) blocking / warning 联动
        blocking = data.get("blocking_issues", [])
        fail_note = f"微信上传失败：{msg}"
        if not passed:
            if fail_note not in blocking:
                blocking.append(fail_note)
        else:
            # 成功则清掉历史的微信上传失败阻塞项
            blocking = [b for b in blocking if not b.startswith("微信上传失败")]
        data["blocking_issues"] = blocking

        # 4) review_ready：绝不因上传成功置 true（仍需人工提审）
        data.setdefault("review_ready", False)

        # 5) 顶层 next_action：上传成功后提示提审，但不改 ready_to_submit
        if passed:
            data["next_action"] = "微信开发版已上传，下一步人工去微信后台提交审核"

        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
