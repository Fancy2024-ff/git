"""输入安全校验：能力任务的用户可控 source / params。

防护目标（把 SSRF / 本地文件读取面挡在进入 provider 之前）：
- source 允许：纯 ID（上传 id，无 scheme）、https:// URL。
- source 拒绝：file://、ftp://、gopher:// 等危险 scheme；http://（明文）；
  指向 localhost / IP 字面量为内网·环回·链路本地（169.254.x 云元数据）·保留网段的 URL。

关于 DNS：本模块**不做 DNS 解析**。原因：
1. 解析结果随环境变化（CI/沙箱里公网域名可能被劫持到保留网段），会误杀合法 URL；
2. 解析+使用之间存在 TOCTOU（DNS rebinding），输入层校验给不了真正保证。
   针对 DNS rebinding / 域名指向内网的纵深防御，应放在出网层（egress 代理/防火墙），
   而非输入校验。这里只挡最常见、最高价值的「IP 字面量直指内网/元数据」攻击向量。

设计为纯函数 + 自定义异常，便于在 API 边界调用并单元测试。
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


class UnsafeSourceError(ValueError):
    """source 未通过安全校验。"""


# 仅允许这些 URL scheme（纯 ID 无 scheme，单独放行）
_ALLOWED_SCHEMES = {"https"}
# 明确危险的 scheme
_BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "dict", "ftps", "tftp", "ldap"}

_MAX_SOURCE_LEN = 2048

_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain"}


def _ip_is_internal(host: str) -> bool | None:
    """host 若是 IP 字面量，判断是否内网/保留。非 IP 字面量返回 None（不做 DNS 解析）。"""
    h = host
    # 去掉 IPv6 字面量的方括号
    if h.startswith("[") and h.endswith("]"):
        h = h[1:-1]
    try:
        ip = ipaddress.ip_address(h)
    except ValueError:
        return None  # 不是 IP 字面量
    # IPv4-mapped IPv6（::ffff:a.b.c.d）按内嵌 IPv4 判断
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return (ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def validate_source(source: str) -> str:
    """校验并返回规范化的 source。不安全则抛 UnsafeSourceError。

    空串放行（上层会在 provider 处按 invalid_request 处理），由调用方决定是否必填。
    """
    if source is None:
        return ""
    source = source.strip()
    if source == "":
        return ""
    if len(source) > _MAX_SOURCE_LEN:
        raise UnsafeSourceError("source 过长")

    parsed = urlparse(source)
    scheme = (parsed.scheme or "").lower()

    # 无 scheme → 视为上传 id / 相对引用，放行（但不允许路径穿越）
    if scheme == "":
        if ".." in source or source.startswith("/") or source.startswith("\\"):
            raise UnsafeSourceError("source 含非法路径")
        return source

    if scheme in _BLOCKED_SCHEMES:
        raise UnsafeSourceError(f"不允许的 scheme: {scheme}")
    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeSourceError(f"仅允许 https 或纯 id，收到 scheme: {scheme}")

    host = (parsed.hostname or "").lower()
    if not host:
        raise UnsafeSourceError("URL 缺少主机名")
    if host in _BLOCKED_HOSTNAMES:
        raise UnsafeSourceError("不允许指向 localhost")
    if _ip_is_internal(host) is True:
        raise UnsafeSourceError("不允许指向内网/保留地址")

    return source

