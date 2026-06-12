"""
App Store data scraper.
Uses Qimai API (七麦) when available, falls back to web scraping.
"""

import httpx
from config.settings import QIMAI_API_KEY
from shared.models import AppInfo, AppSource


def fetch_ai_apps_appstore(
    category: str = "ai",
    limit: int = 50,
    country: str = "cn",
) -> list[AppInfo]:
    """
    Fetch AI-related apps from App Store rankings.

    In production, uses Qimai (七麦) API or SensorTower.
    For MVP, returns empty list to trigger LLM fallback.
    """
    if QIMAI_API_KEY:
        return _fetch_via_qimai(category, limit, country)

    # TODO: Implement web scraping fallback
    # For now, return empty to trigger LLM suggestion in agent.py
    return []


def _fetch_via_qimai(category: str, limit: int, country: str) -> list[AppInfo]:
    """Fetch from Qimai (七麦) API."""
    try:
        # Qimai API endpoint for app rankings
        url = "https://api.qimai.cn/rank/indexPlus/brand_id/1"
        headers = {"Authorization": f"Bearer {QIMAI_API_KEY}"}
        params = {
            "genre": _category_to_genre_id(category),
            "country": country,
            "device": "iphone",
            "page": 1,
            "limit": limit,
        }

        response = httpx.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        apps = []
        for item in data.get("appData", []):
            app = AppInfo(
                name=item.get("appInfo", {}).get("appName", ""),
                app_id=item.get("appInfo", {}).get("appId", ""),
                source=AppSource.APP_STORE,
                category=category,
                description=item.get("appInfo", {}).get("description", ""),
                downloads=item.get("appInfo", {}).get("downloads", 0),
                rating=float(item.get("appInfo", {}).get("score", 0)),
            )
            apps.append(app)

        return apps
    except Exception as e:
        print(f"[Qimai] API fetch failed: {e}")
        return []


def _category_to_genre_id(category: str) -> str:
    """Map category name to Qimai genre ID."""
    mapping = {
        "ai": "6013",  # Productivity (closest to AI tools)
        "photo": "6008",
        "education": "6017",
        "utilities": "6002",
        "entertainment": "6016",
    }
    return mapping.get(category, "6013")
