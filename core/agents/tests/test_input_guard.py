"""input_guard.validate_source 安全校验测试。

既验证「危险输入被拒」，也验证「合法输入放行」——后者同样重要，
防止过度拦截把正常上传 id / https 图片 URL 也挡掉。
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT / "core", REPO_ROOT / "core" / "agents"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from runtime.input_guard import validate_source, UnsafeSourceError


# ── 合法输入必须放行 ──

@pytest.mark.parametrize("src", [
    "",                                   # 空串放行（上层决定是否必填）
    "upload_abc123",                      # 纯上传 id
    "img-2026-0616-xyz.png",              # 带扩展名的 id
    "https://cdn.example.com/a/b.png",    # 正常 https 图片 URL
    "https://images.example.com:443/x.jpg?token=k",
])
def test_allows_legitimate_sources(src):
    assert validate_source(src) == src.strip()


# ── 危险 scheme 必须拒绝 ──

@pytest.mark.parametrize("src", [
    "file:///etc/passwd",
    "file://localhost/etc/shadow",
    "ftp://x/y",
    "gopher://x",
    "data:text/plain;base64,AAAA",
    "dict://x",
])
def test_blocks_dangerous_schemes(src):
    with pytest.raises(UnsafeSourceError):
        validate_source(src)


# ── http 明文也拒（只允许 https / 纯 id）──

def test_blocks_plain_http():
    with pytest.raises(UnsafeSourceError):
        validate_source("http://example.com/a.png")


# ── 内网 / 元数据 / 环回地址必须拒绝 ──

@pytest.mark.parametrize("src", [
    "https://169.254.169.254/latest/meta-data/",  # 云元数据
    "https://127.0.0.1/x.png",                     # 环回
    "https://10.0.0.5/x.png",                      # 私网 A
    "https://192.168.1.10/x.png",                  # 私网 C
    "https://172.16.0.3/x.png",                    # 私网 B
    "https://localhost/x.png",                     # localhost 名
])
def test_blocks_internal_targets(src):
    with pytest.raises(UnsafeSourceError):
        validate_source(src)


# ── 路径穿越 id 拒绝 ──

@pytest.mark.parametrize("src", [
    "../../etc/passwd",
    "/etc/passwd",
    "..\\..\\windows\\system32",
])
def test_blocks_path_traversal_ids(src):
    with pytest.raises(UnsafeSourceError):
        validate_source(src)
