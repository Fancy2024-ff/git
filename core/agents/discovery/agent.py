"""
Discovery Agent - Finds AI apps in App Store/Google Play that don't exist as mini-programs.

Strategy:
1. Fetch top AI apps from app stores (via Qimai/SensorTower or scraping)
2. Search each app name in mini-program platforms
3. Score the gap opportunity (downloads × missing platforms × category heat)
4. Run 8-question evaluation to filter viable opportunities
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from config.settings import LLM_MODEL, ANTHROPIC_API_KEY
from shared.models import (
    AppInfo,
    AppSource,
    GapOpportunity,
    MiniProgramPlatform,
)
from shared.llm import get_llm
from shared.database import list_projects
from discovery.scrapers.appstore import fetch_ai_apps_appstore
from discovery.scrapers.googleplay import fetch_ai_apps_googleplay
from discovery.scrapers.miniprogram import search_miniprogram
from discovery.analyzer import evaluate_opportunity, filter_opportunities


def run_discovery(
    category: str = "ai",
    limit: int = 50,
    evaluate: bool = True,
) -> list[GapOpportunity]:
    """
    Main discovery flow:
    1. Get top AI apps from stores
    2. Check if they exist as mini-programs
    3. Score and rank opportunities
    4. (Optional) Run 8-question deep evaluation to filter
    """
    # Dedup: skip apps already in our pipeline
    existing_names = {p.app_name.lower() for p in list_projects()}

    # Step 1: Fetch AI apps from app stores
    apps = fetch_ai_apps_appstore(category=category, limit=limit)

    # Also fetch from Google Play and merge
    gp_apps = fetch_ai_apps_googleplay(category=category, limit=limit)
    seen_names = {a.name.lower() for a in apps}
    for gp_app in gp_apps:
        if gp_app.name.lower() not in seen_names:
            apps.append(gp_app)
            seen_names.add(gp_app.name.lower())

    if not apps:
        print("[Discovery] No apps fetched, using LLM to suggest known AI apps")
        apps = _suggest_apps_via_llm(category)

    # Step 2: Check mini-program coverage
    opportunities: list[GapOpportunity] = []

    for app in apps:
        missing_platforms = []

        for platform in [
            MiniProgramPlatform.WECHAT,
            MiniProgramPlatform.ALIPAY,
            MiniProgramPlatform.DOUYIN,
        ]:
            exists = search_miniprogram(app.name, platform)
            if not exists:
                missing_platforms.append(platform)

        if missing_platforms:
            if app.name.lower() in existing_names:
                continue  # Already processed, skip
            gap_score = _calculate_gap_score(app, missing_platforms)
            opportunity = GapOpportunity(
                app=app,
                missing_platforms=missing_platforms,
                gap_score=gap_score,
                competition_level=_assess_competition(app),
                estimated_difficulty=_estimate_difficulty(app),
                reason=f"{app.name} has {app.downloads}+ downloads but missing from {len(missing_platforms)} mini-program platforms",
            )
            opportunities.append(opportunity)

    # Sort by gap score
    opportunities.sort(key=lambda x: x.gap_score, reverse=True)

    # Step 3: Deep evaluation (8 questions) on top candidates
    if evaluate and opportunities:
        top_candidates = opportunities[:10]  # Evaluate top 10 only (LLM cost)
        evaluated = filter_opportunities(top_candidates, min_score=60)
        if evaluated:
            # Return only evaluated & approved opportunities
            return [opp for opp, _ in evaluated]
        else:
            print("[Discovery] No opportunities passed evaluation, returning raw top 5")
            return opportunities[:5]

    return opportunities


def _calculate_gap_score(app: AppInfo, missing_platforms: list) -> float:
    """Score the opportunity: higher = more worthwhile."""
    score = 0.0

    # Downloads weight (log scale)
    if app.downloads > 1_000_000:
        score += 40
    elif app.downloads > 100_000:
        score += 30
    elif app.downloads > 10_000:
        score += 20
    else:
        score += 10

    # Missing platforms weight
    score += len(missing_platforms) * 15

    # Rating weight
    if app.rating >= 4.5:
        score += 10
    elif app.rating >= 4.0:
        score += 5

    return min(score, 100)


def _assess_competition(app: AppInfo) -> str:
    """Assess competition level in mini-program space."""
    # Simplified - in production, would check actual mini-program search results
    if app.downloads > 5_000_000:
        return "high"  # Popular apps likely have copycats
    elif app.downloads > 500_000:
        return "medium"
    return "low"


def _estimate_difficulty(app: AppInfo) -> str:
    """Estimate how hard it is to build as a mini-program."""
    complex_keywords = ["video", "ar", "camera", "real-time", "3d"]
    for kw in complex_keywords:
        if kw in app.description.lower():
            return "hard"

    if len(app.features) > 5:
        return "medium"
    return "easy"


def _suggest_apps_via_llm(category: str) -> list[AppInfo]:
    """Use LLM to suggest popular AI apps when API is unavailable."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a mobile app market analyst. Return a JSON array of popular AI apps.",
        ),
        (
            "human",
            """List 20 popular AI-related apps in the "{category}" category that are on
App Store or Google Play. For each app, provide:
- name: app name
- app_id: bundle id or package name (approximate is fine)
- category: specific sub-category
- description: one-line description
- downloads: estimated downloads (number)
- rating: app store rating
- features: list of 3-5 key features

Return as a JSON array. Focus on apps that would work well as mini-programs.""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"category": category})

    apps = []
    for item in result:
        apps.append(
            AppInfo(
                name=item["name"],
                app_id=item.get("app_id", ""),
                source=AppSource.APP_STORE,
                category=item.get("category", category),
                description=item.get("description", ""),
                downloads=item.get("downloads", 0),
                rating=item.get("rating", 0.0),
                features=item.get("features", []),
            )
        )
    return apps
