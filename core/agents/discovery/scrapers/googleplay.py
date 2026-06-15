"""
Google Play data scraper.
Uses google-play-scraper library (free, no key required).
Falls back to SensorTower API when configured.
"""

import httpx
from config.settings import SENSORTOWER_API_KEY
from shared.models import AppInfo, AppSource

try:
    from google_play_scraper import search as gp_search
    HAS_GP_SCRAPER = True
except ImportError:
    HAS_GP_SCRAPER = False


# AI 相关搜索关键词
AI_SEARCH_TERMS = [
    "AI writing assistant", "AI photo editor", "AI chatbot",
    "AI translator", "AI productivity", "AI art generator",
]


def fetch_ai_apps_googleplay(
    category: str = "ai",
    limit: int = 50,
) -> list[AppInfo]:
    """
    Fetch AI-related apps from Google Play rankings.
    Uses google-play-scraper library (free) by default.
    Uses SensorTower API when key is configured.
    """
    if SENSORTOWER_API_KEY:
        st_results = _fetch_via_sensortower(category, limit)
        if st_results:
            return st_results

    if HAS_GP_SCRAPER:
        return _fetch_via_scraper(category, limit)

    return []


def _fetch_via_scraper(category: str, limit: int) -> list[AppInfo]:
    """Fetch from Google Play using google-play-scraper library."""
    search_terms = _get_search_terms(category)
    seen_ids: set[str] = set()
    apps: list[AppInfo] = []

    per_term_limit = max(10, limit // len(search_terms))

    for term in search_terms:
        if len(apps) >= limit:
            break
        try:
            results = gp_search(term, lang="en", country="us", n_hits=per_term_limit)

            for item in results:
                app_id = item.get("appId", "")
                if app_id in seen_ids:
                    continue
                seen_ids.add(app_id)

                # Parse installs string like "10,000,000+"
                installs_str = item.get("installs", "0")
                installs = _parse_installs(installs_str)

                app = AppInfo(
                    name=item.get("title", ""),
                    app_id=app_id,
                    source=AppSource.GOOGLE_PLAY,
                    category=item.get("genre", category),
                    description=item.get("description", "")[:500],
                    downloads=installs,
                    rating=float(item.get("score", 0) or 0),
                    features=_extract_features(item.get("description", "")),
                )
                apps.append(app)

        except Exception as e:
            print(f"[GooglePlay] Search failed for '{term}': {e}")
            continue

    # Sort by downloads
    apps.sort(key=lambda a: a.downloads, reverse=True)
    return apps[:limit]


def _parse_installs(installs_str: str) -> int:
    """Parse install count string like '10,000,000+' to int."""
    if isinstance(installs_str, int):
        return installs_str
    try:
        return int(str(installs_str).replace(",", "").replace("+", "").strip())
    except (ValueError, TypeError):
        return 0


def _get_search_terms(category: str) -> list[str]:
    """Get search terms based on category."""
    terms_map = {
        "ai": ["AI writing assistant", "AI photo editor", "AI chatbot", "AI translator", "AI productivity", "AI art"],
        "photo": ["AI photo editor", "AI avatar generator", "AI background remover", "AI enhance photo"],
        "education": ["AI tutor", "AI language learning", "AI study helper", "AI math solver"],
        "utilities": ["AI scanner", "AI voice recorder", "AI summarizer", "AI keyboard"],
        "entertainment": ["AI music generator", "AI video editor", "AI face swap", "AI story writer"],
    }
    return terms_map.get(category, terms_map["ai"])


def _extract_features(description: str) -> list[str]:
    """Extract key features from app description."""
    features = []
    lines = description.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith(("•", "-", "✓", "✔", "★", "·", "►")) and len(line) > 5:
            features.append(line.lstrip("•-✓✔★·► "))
            if len(features) >= 5:
                break
    return features


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
