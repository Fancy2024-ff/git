"""
Mini-program platform search.
Checks if a given app name already exists as a mini-program.

Limitations:
- No official public API exists for any platform's mini-program search.
- WeChat uses sogou.com web search as a proxy (rate-limited, CAPTCHA-prone).
- Alipay/Douyin use Baidu search as a proxy (noisy, indirect signal).
- Short app names (<=3 chars) produce unreliable matches and are skipped.
- Results should be treated as heuristic, not authoritative.
"""

import httpx
from shared.models import MiniProgramPlatform

# Minimum response body length to consider a search result page valid.
# Shorter responses are likely CAPTCHAs, error pages, or empty shells.
_MIN_VALID_RESPONSE_LENGTH = 1000


def search_miniprogram(app_name: str, platform: MiniProgramPlatform) -> bool:
    """
    Search if an app exists as a mini-program on the given platform.

    Returns True if found (meaning there's already coverage), False if not found (opportunity).
    """
    # Short names (<=3 chars) match too broadly in HTML content — skip to avoid false positives
    if len(app_name) <= 3:
        return False

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
    Search WeChat mini-program by name via sogou.com.

    Note: This is a heuristic approach. Production would use WeChat Open Platform API,
    third-party data sources (阿拉丁, QuestMobile), or a dedicated scraping service.
    """
    try:
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

        if response.status_code == 200:
            # Guard against CAPTCHA pages or empty responses
            if len(response.text) < _MIN_VALID_RESPONSE_LENGTH:
                return False
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
            if len(response.text) < _MIN_VALID_RESPONSE_LENGTH:
                return False
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
            if len(response.text) < _MIN_VALID_RESPONSE_LENGTH:
                return False
            content = response.text.lower()
            app_lower = app_name.lower()
            return app_lower in content and ("抖音小程序" in response.text or "douyin" in content)
    except Exception as e:
        print(f"[Douyin Search] Failed for '{app_name}': {e}")
    return False
