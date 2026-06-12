"""
Mini-program platform search.
Checks if a given app name already exists as a mini-program.
"""

import httpx
from shared.models import MiniProgramPlatform


def search_miniprogram(app_name: str, platform: MiniProgramPlatform) -> bool:
    """
    Search if an app exists as a mini-program on the given platform.

    Returns True if found (meaning there's already coverage), False if not found (opportunity).
    """
    searchers = {
        MiniProgramPlatform.WECHAT: _search_wechat,
        MiniProgramPlatform.ALIPAY: _search_alipay,
        MiniProgramPlatform.DOUYIN: _search_douyin,
    }

    searcher = searchers.get(platform)
    if searcher:
        return searcher(app_name)
    return False


def _search_wechat(app_name: str) -> bool:
    """
    Search WeChat mini-program by name.

    Note: WeChat doesn't have a public search API.
    Options:
    1. Use WeChat Open Platform API (requires account)
    2. Scrape search results from web interfaces
    3. Use third-party data sources (阿拉丁, QuestMobile)

    For MVP, we use a heuristic approach with web search.
    """
    try:
        # Use web search to check if mini-program exists
        # This is a simplified approach - production would use proper APIs
        url = "https://weixin.sogou.com/weixin"
        params = {
            "type": "1",  # Mini-program search
            "query": app_name,
            "ie": "utf8",
        }

        response = httpx.get(
            url,
            params=params,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            follow_redirects=True,
        )

        # Check if we got meaningful results
        if response.status_code == 200:
            # Simple heuristic: check if app name appears in results
            content = response.text.lower()
            return app_name.lower() in content

    except Exception as e:
        print(f"[WeChat Search] Failed for '{app_name}': {e}")

    return False


def _search_alipay(app_name: str) -> bool:
    """
    Search Alipay mini-program via Baidu index.
    Uses Baidu search as a proxy since Alipay has no public search API.
    """
    try:
        response = httpx.get(
            "https://www.baidu.com/s",
            params={"wd": f'"{app_name}" 支付宝小程序'},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            follow_redirects=True,
        )
        if response.status_code == 200:
            content = response.text.lower()
            app_lower = app_name.lower()
            return app_lower in content and ("支付宝小程序" in response.text or "mini.alipay" in content)
    except Exception as e:
        print(f"[Alipay Search] Failed for '{app_name}': {e}")
    return False


def _search_douyin(app_name: str) -> bool:
    """
    Search Douyin mini-program via Baidu index.
    Uses Baidu search as a proxy since Douyin has no public search API.
    """
    try:
        response = httpx.get(
            "https://www.baidu.com/s",
            params={"wd": f'"{app_name}" 抖音小程序'},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            follow_redirects=True,
        )
        if response.status_code == 200:
            content = response.text.lower()
            app_lower = app_name.lower()
            return app_lower in content and ("抖音小程序" in response.text or "douyin" in content)
    except Exception as e:
        print(f"[Douyin Search] Failed for '{app_name}': {e}")
    return False
