"""miniprogram-ci 统一封装：微信小程序代码上传的唯一 CLI 落点。

封装参数拼接 / stdout-stderr 解析 / 超时 / exit code 映射 / 错误分类。
真实调用：npx miniprogram-ci upload --pp <project> --appid <appid> --pkp <key> ...
本机无微信环境时，测试通过注入 runner 跑 mock subprocess，代码路径一致。
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field


class CIErrorCode:
    CLI_MISSING = "cli_missing"
    INVALID_CONFIG = "invalid_config"
    DIST_MISSING = "dist_missing"
    AUTH_FAILED = "auth_failed"
    TIMEOUT = "timeout"
    UPSTREAM_FAILED = "upstream_failed"


@dataclass
class CIResult:
    success: bool
    error_code: str = ""
    message: str = ""
    version: str = ""
    raw_output: str = ""
    command: str = ""


def validate_env_or_binary(which=shutil.which) -> tuple[bool, str]:
    """检查 npx 是否可用（miniprogram-ci 通过 npx 调用）。返回 (ok, 缺什么)。"""
    if which("npx") is None:
        return False, "npx"
    return True, ""


def _classify(returncode: int, output: str) -> tuple[str, str]:
    """从 exit code + 输出分类错误。"""
    low = (output or "").lower()
    if "private key" in low or "private_key" in low or "auth" in low or "code: -1" in low and "key" in low:
        return CIErrorCode.AUTH_FAILED, "私钥/鉴权失败"
    if "appid" in low and ("invalid" in low or "not" in low):
        return CIErrorCode.AUTH_FAILED, "appid 无效"
    if "enoent" in low or "no such file" in low:
        return CIErrorCode.DIST_MISSING, "项目/产物路径不存在"
    return CIErrorCode.UPSTREAM_FAILED, f"上传失败（exit={returncode}）"


def parse_upload_result(returncode: int, stdout: str, stderr: str) -> CIResult:
    """从 CLI 输出提取成功/失败 + 版本信息。"""
    output = (stdout or "") + ("\n" + stderr if stderr else "")
    clipped = output[-2000:]
    if returncode == 0:
        # miniprogram-ci 成功通常输出 "upload" 完成信息
        return CIResult(success=True, message="开发版上传成功", raw_output=clipped)
    code, msg = _classify(returncode, output)
    return CIResult(success=False, error_code=code, message=msg, raw_output=clipped)


def upload_project(
    *,
    appid: str,
    private_key_path: str,
    project_path: str,
    version: str = "1.0.0",
    desc: str = "automated upload",
    robot: int = 1,
    timeout: int = 300,
    runner=subprocess.run,
    which=shutil.which,
) -> CIResult:
    """上传开发版到微信后台。

    runner/which 可注入，便于测试 mock subprocess 而走真实代码路径。
    """
    ok, missing = validate_env_or_binary(which)
    if not ok:
        return CIResult(success=False, error_code=CIErrorCode.CLI_MISSING,
                        message=f"{missing} 不可用，无法调用 miniprogram-ci")

    cmd = [
        "npx", "miniprogram-ci", "upload",
        "--pp", project_path,
        "--appid", appid,
        "--pkp", private_key_path,
        "--uv", version,
        "--desc", desc,
        "-r", str(robot),
    ]
    command_str = "npx miniprogram-ci upload --pp <project> --appid <appid> --pkp <key> ..."
    try:
        proc = runner(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return CIResult(success=False, error_code=CIErrorCode.TIMEOUT,
                        message=f"上传超时（>{timeout}s）", command=command_str)
    except FileNotFoundError:
        return CIResult(success=False, error_code=CIErrorCode.CLI_MISSING,
                        message="npx/miniprogram-ci 未找到", command=command_str)

    result = parse_upload_result(proc.returncode, proc.stdout, proc.stderr)
    result.version = version
    result.command = command_str
    return result
