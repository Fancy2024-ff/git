"""
Full pipeline test - Discovery -> Research -> Coding -> QA
Skips miniprogram search and publisher for speed.
"""

import sys
import os
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

os.environ["PYTHONUNBUFFERED"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "agents"))

from shared.llm import get_llm
from shared.models import AppInfo, AppSource, GapOpportunity, MiniProgramPlatform, MiniAppProject, ProjectStatus
from research.agent import run_research
from coding.agent import run_coding
from qa.agent import run_qa
import uuid


def p(msg):
    print(msg, flush=True)


def main():
    p("=" * 60)
    p("  Full Pipeline: Discovery -> Research -> Coding -> QA")
    p("=" * 60)

    # STEP 1: Discovery via LLM
    p("\n[1/4] DISCOVERY...")
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser

    llm = get_llm(max_tokens=1024)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Return one JSON object for a popular AI app."),
        ("human",
         "Suggest 1 AI app that would work as a WeChat mini-program. "
         "Return JSON with: name, category, description, downloads (number), "
         "rating (float), features (array of 3-5 strings)."),
    ])
    chain = prompt | llm | JsonOutputParser()
    app_data = chain.invoke({})
    p(f"  App: {app_data.get('name')} ({app_data.get('category')})")
    p(f"  Downloads: {app_data.get('downloads', 0):,}")

    app = AppInfo(
        name=app_data["name"],
        app_id="com.test.app",
        source=AppSource.APP_STORE,
        category=app_data.get("category", "AI"),
        description=app_data.get("description", ""),
        downloads=app_data.get("downloads", 100000),
        rating=app_data.get("rating", 4.5),
        features=app_data.get("features", []),
    )
    opportunity = GapOpportunity(
        app=app,
        missing_platforms=[MiniProgramPlatform.WECHAT, MiniProgramPlatform.DOUYIN],
        gap_score=85.0,
        competition_level="low",
        estimated_difficulty="easy",
        reason=f"{app.name} not on WeChat/Douyin",
    )
    p("  DONE")

    # STEP 2: Research
    p("\n[2/4] RESEARCH (PRD generation)...")
    prd = run_research(opportunity)
    p(f"  PRD: {prd.app_name}")
    p(f"  Summary: {prd.summary[:60]}...")
    p(f"  Features: {len(prd.core_features)}")
    p(f"  Feasibility: {prd.feasibility_score}/100")
    p("  DONE")

    # STEP 3: Coding
    p("\n[3/4] CODING (project generation)...")
    project_path = run_coding(prd)
    p(f"  Path: {project_path}")

    proj = Path(project_path)
    if proj.exists():
        files = [f for f in proj.rglob("*") if f.is_file()]
        p(f"  Files generated: {len(files)}")
        for f in sorted(files)[:12]:
            p(f"    {f.relative_to(proj)}")
        if len(files) > 12:
            p(f"    ... and {len(files) - 12} more")
    p("  DONE")

    # STEP 4: QA
    p("\n[4/4] QA (quality check)...")
    project = MiniAppProject(
        id=str(uuid.uuid4())[:8],
        app_name=app.name,
        status=ProjectStatus.CODE_READY,
        opportunity=opportunity,
        prd=prd,
        project_path=project_path,
        target_platforms=[MiniProgramPlatform.WECHAT, MiniProgramPlatform.DOUYIN],
    )
    qa_result = run_qa(project)
    p(f"  Score: {qa_result.score}/100")
    p(f"  Passed: {qa_result.passed}")
    if qa_result.structural_issues:
        for issue in qa_result.structural_issues:
            p(f"    [STRUCT] {issue}")
    if qa_result.code_issues:
        for issue in qa_result.code_issues[:5]:
            p(f"    [CODE] {issue}")
    p("  DONE")

    # Summary
    p("\n" + "=" * 60)
    p(f"  PIPELINE COMPLETE!")
    p(f"  App: {app.name}")
    p(f"  PRD: {len(prd.core_features)} features")
    p(f"  Project: {project_path}")
    p(f"  QA: {qa_result.score}/100 ({'PASS' if qa_result.passed else 'NEEDS WORK'})")
    p("=" * 60)


if __name__ == "__main__":
    main()
