"""Quick smoke test - run discovery with search disabled to verify LLM chain works."""

import sys
import os
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "agents"))

from shared.llm import get_llm
from shared.models import AppInfo, AppSource, GapOpportunity, MiniProgramPlatform


def main():
    print("=" * 50)
    print("Smoke Test: MiniApp Factory")
    print("=" * 50)

    # Test 1: LLM connection
    print("\n[1/3] Testing LLM connection...")
    llm = get_llm(max_tokens=1024)
    response = llm.invoke("Say 'LLM OK' if you can hear me.")
    print(f"  LLM response: {response.content[:50]}")
    print("  PASS")

    # Test 2: LLM-based app discovery (skip HTTP scrapers)
    print("\n[2/3] Testing app discovery via LLM...")
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Return a JSON array of 3 popular AI apps."),
        ("human", "List 3 popular AI apps with fields: name, category, description, downloads (number), rating (float), features (array of strings). Return JSON array only."),
    ])
    chain = prompt | llm | JsonOutputParser()
    apps_data = chain.invoke({})
    print(f"  Found {len(apps_data)} apps:")
    for app in apps_data:
        print(f"    - {app.get('name', '?')} ({app.get('category', '?')})")
    print("  PASS")

    # Test 3: Build a mock opportunity and run through Research Agent
    print("\n[3/3] Testing Research Agent (PRD generation)...")
    from research.agent import run_research

    app = AppInfo(
        name=apps_data[0]["name"],
        app_id="com.test.app",
        source=AppSource.APP_STORE,
        category=apps_data[0].get("category", "AI"),
        description=apps_data[0].get("description", "An AI app"),
        downloads=apps_data[0].get("downloads", 100000),
        rating=apps_data[0].get("rating", 4.5),
        features=apps_data[0].get("features", ["AI chat"]),
    )
    opportunity = GapOpportunity(
        app=app,
        missing_platforms=[MiniProgramPlatform.WECHAT, MiniProgramPlatform.DOUYIN],
        gap_score=85.0,
        competition_level="low",
        estimated_difficulty="easy",
        reason="Test opportunity",
    )

    prd = run_research(opportunity)
    print(f"  PRD generated: {prd.app_name}")
    print(f"  Summary: {prd.summary[:80]}...")
    print(f"  Features: {len(prd.core_features)} core features")
    print(f"  Feasibility: {prd.feasibility_score}/100")
    print("  PASS")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED - Pipeline core is working!")
    print("=" * 50)


if __name__ == "__main__":
    main()
