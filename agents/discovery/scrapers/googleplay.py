"""
Google Play data scraper.
Uses SensorTower API when available.
"""

import httpx
from config.settings import SENSORTOWER_API_KEY
from shared.models import AppInfo, AppSource


def fetch_ai_apps_googleplay(
    category: str = "ai",
    limit: int = 50,
) -> list[AppInfo]:
    """
    Fetch AI-related apps from Google Play rankings.
    Uses SensorTower API when key is configured.
    """
    if SENSORTOWER_API_KEY:
        return _fetch_via_sensortower(category, limit)

    return []


def _fetch_via_sensortower(category: str, limit: int) -> list[AppInfo]:
    """Fetch from SensorTower API."""
    try:
        url = "https://api.sensortower.com/v1/android/rankings/get_top_apps"
        params = {
            "auth_token": SENSORTOWER_API_KEY,
            "category": _map_category(category),
            "country": "US",
            "limit": limit,
        }

        response = httpx.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        apps = []
        for item in data:
            app = AppInfo(
                name=item.get("name", ""),
                app_id=item.get("app_id", ""),
                source=AppSource.GOOGLE_PLAY,
                category=category,
                description=item.get("description", ""),
                downloads=item.get("downloads_estimate", 0),
                rating=float(item.get("rating", 0)),
            )
            apps.append(app)

        return apps
    except Exception as e:
        print(f"[SensorTower] API fetch failed: {e}")
        return []


def _map_category(category: str) -> str:
    """Map to Google Play category IDs."""
    mapping = {
        "ai": "PRODUCTIVITY",
        "photo": "PHOTOGRAPHY",
        "education": "EDUCATION",
        "utilities": "TOOLS",
    }
    return mapping.get(category, "PRODUCTIVITY")
