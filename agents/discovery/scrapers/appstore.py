"""
App Store data scraper.
Uses iTunes Search API (free, no key required).
Falls back to Qimai API when configured.
"""

import httpx
from config.settings import QIMAI_API_KEY
from shared.models import AppInfo, AppSource


# iTunes Search API - 免费，无需 API Key
ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

# AI 相关搜索关键词
AI_SEARCH_TERMS = [
    "AI writing", "AI assistant", "AI photo", "AI translate",
    "AI chat", "AI art", "AI productivity", "AI education",
]


def fetch_ai_apps_appstore(
    category: str = "ai",
    limit: int = 50,
    country: str = "us",
) -> list[AppInfo]:
    """
    Fetch AI-related apps from App Store.
    Uses free iTunes Search API by default.
    Uses Qimai API when key is configured (Chinese market data).
    """
    if QIMAI_API_KEY:
        qimai_results = _fetch_via_qimai(category, limit, country)
        if qimai_results:
            return qimai_results

    return _fetch_via_itunes(category, limit, country)


def _fetch_via_itunes(category: str, limit: int, country: str) -> list[AppInfo]:
    """Fetch from iTunes Search API (free, no key needed)."""
    search_terms = _get_search_terms(category)
    seen_ids: set[str] = set()
    apps: list[AppInfo] = []

    per_term_limit = max(10, limit // len(search_terms))

    for term in search_terms:
        if len(apps) >= limit:
            break
        try:
            resp = httpx.get(
                ITUNES_SEARCH_URL,
                params={
                    "term": term,
                    "country": country,
                    "media": "software",
                    "limit": per_term_limit,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                app_id = item.get("bundleId", "")
                if app_id in seen_ids:
                    continue
                seen_ids.add(app_id)

                # Parse download estimate from rating count
                rating_count = item.get("userRatingCount", 0)
                # Rough estimate: ratings × 50 ≈ downloads
                estimated_downloads = rating_count * 50

                app = AppInfo(
                    name=item.get("trackName", ""),
                    app_id=app_id,
                    source=AppSource.APP_STORE,
                    category=item.get("primaryGenreName", category),
                    description=item.get("description", "")[:500],
                    downloads=estimated_downloads,
                    rating=float(item.get("averageUserRating", 0)),
                    features=_extract_features(item.get("description", "")),
                )
                apps.append(app)

        except Exception as e:
            print(f"[iTunes] Search failed for '{term}': {e}")
            continue

    # Sort by estimated popularity
    apps.sort(key=lambda a: a.downloads, reverse=True)
    return apps[:limit]


def _get_search_terms(category: str) -> list[str]:
    """Get search terms based on category."""
    terms_map = {
        "ai": ["AI writing", "AI assistant", "AI photo editor", "AI translate", "AI chat", "AI productivity"],
        "photo": ["AI photo editor", "AI avatar", "AI art generator", "photo enhance AI"],
        "education": ["AI tutor", "AI language learning", "AI study", "AI homework"],
        "utilities": ["AI scanner", "AI keyboard", "AI summarize", "AI voice"],
        "entertainment": ["AI music", "AI video", "AI face", "AI story"],
    }
    return terms_map.get(category, terms_map["ai"])


def _extract_features(description: str) -> list[str]:
    """Extract key features from app description."""
    features = []
    # Look for bullet-point style features
    lines = description.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith(("•", "-", "✓", "✔", "★", "·")) and len(line) > 5:
            features.append(line.lstrip("•-✓✔★· "))
            if len(features) >= 5:
                break
    return features


def _fetch_via_qimai(category: str, limit: int, country: str) -> list[AppInfo]:
    """Fetch from Qimai (七麦) API."""
    try:
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
        "ai": "6013",
        "photo": "6008",
        "education": "6017",
        "utilities": "6002",
        "entertainment": "6016",
    }
    return mapping.get(category, "6013")
