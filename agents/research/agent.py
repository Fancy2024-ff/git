"""
Research Agent - Analyzes an app opportunity and generates a PRD document.

Takes a GapOpportunity and produces a detailed PRD that the Coding Agent can use.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from shared.models import GapOpportunity, PRDDocument, MiniProgramPlatform
from shared.llm import get_llm
from config.settings import PRDS_DIR

import json
import re
from datetime import datetime


def run_research(opportunity: GapOpportunity) -> PRDDocument:
    """
    Analyze app and generate PRD:
    1. Deep-dive into what the app does
    2. Identify core features suitable for mini-program
    3. Assess technical feasibility
    4. Generate complete PRD
    """
    llm = get_llm(max_tokens=8192)

    # Step 1: Analyze the app
    analysis = _analyze_app(llm, opportunity)

    # Step 2: Generate PRD
    prd = _generate_prd(llm, opportunity, analysis)

    # Step 3: Save PRD to disk
    _save_prd(prd)

    return prd


def _analyze_app(llm: ChatAnthropic, opportunity: GapOpportunity) -> dict:
    """Use LLM to deeply analyze the app's functionality."""
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior product manager specializing in mobile apps and mini-programs.
Analyze the given app and identify its core value proposition, key features, and how it could
be adapted as a WeChat/Alipay/Douyin mini-program.

Consider mini-program limitations:
- Package size limits (usually 2-20MB)
- Limited background execution
- Platform-specific APIs
- No push notifications in some platforms
- Limited local storage

Return a JSON object with your analysis.""",
        ),
        (
            "human",
            """Analyze this app:
Name: {app_name}
Category: {category}
Description: {description}
Features: {features}
Downloads: {downloads}
Rating: {rating}

Target mini-program platforms: {platforms}

Provide:
1. Core value proposition (what problem does it solve?)
2. Key features that can be replicated in a mini-program
3. Features that CANNOT be done in mini-programs (and alternatives)
4. Suggested monetization strategy for mini-program
5. Technical feasibility assessment (0-100)
6. Estimated development hours

Return as JSON with keys: value_proposition, replicable_features (array of objects with
name, description, type, priority), impossible_features, alternatives, monetization,
feasibility_score, dev_hours""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = chain.invoke({
            "app_name": opportunity.app.name,
            "category": opportunity.app.category,
            "description": opportunity.app.description,
            "features": ", ".join(opportunity.app.features),
            "downloads": opportunity.app.downloads,
            "rating": opportunity.app.rating,
            "platforms": ", ".join([p.value for p in opportunity.missing_platforms]),
        })
    except Exception as e:
        print(f"[Research] Analysis JSON parse failed, trying fallback: {e}")
        raw_response = (prompt | llm).invoke({
            "app_name": opportunity.app.name,
            "category": opportunity.app.category,
            "description": opportunity.app.description,
            "features": ", ".join(opportunity.app.features),
            "downloads": opportunity.app.downloads,
            "rating": opportunity.app.rating,
            "platforms": ", ".join([p.value for p in opportunity.missing_platforms]),
        })
        result = _extract_json_from_text(raw_response.content)

    return result


def _generate_prd(llm: ChatAnthropic, opportunity: GapOpportunity, analysis: dict) -> PRDDocument:
    """Generate a structured PRD from the analysis."""
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a product manager writing a PRD for a mini-program development team.
Based on the app analysis, create a detailed PRD that a developer can implement.

Focus on:
- Clear feature specifications with UI descriptions
- API endpoint definitions
- User flow descriptions
- Data models needed

Return as JSON matching the PRD schema.""",
        ),
        (
            "human",
            """Create a PRD for building a mini-program version of "{app_name}".

Analysis results:
{analysis}

Target platforms: {platforms}

Generate a PRD with:
- summary: 2-3 sentence product summary
- core_features: array of features, each with:
  - name: feature name
  - description: detailed description
  - type: "input" | "display" | "interaction" | "navigation"
  - api_endpoint: backend API path needed
  - priority: "p0" | "p1" | "p2"
- user_scenarios: array of user story strings
- tech_requirements: array of technical requirements
- monetization: monetization strategy description

Return as JSON.""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = chain.invoke({
            "app_name": opportunity.app.name,
            "analysis": json.dumps(analysis, ensure_ascii=False),
            "platforms": ", ".join([p.value for p in opportunity.missing_platforms]),
        })
    except Exception as e:
        # Fallback: invoke LLM directly and try to parse JSON manually
        print(f"[Research] JSON parse failed, trying fallback: {e}")
        raw_response = (prompt | llm).invoke({
            "app_name": opportunity.app.name,
            "analysis": json.dumps(analysis, ensure_ascii=False),
            "platforms": ", ".join([p.value for p in opportunity.missing_platforms]),
        })
        result = _extract_json_from_text(raw_response.content)

    # Build PRD model
    dev_hours_raw = analysis.get("dev_hours", 40)
    if isinstance(dev_hours_raw, dict):
        dev_hours_raw = dev_hours_raw.get("total", 40)
    dev_hours = int(dev_hours_raw) if dev_hours_raw else 40

    feasibility_raw = analysis.get("feasibility_score", 50)
    if isinstance(feasibility_raw, dict):
        feasibility_raw = feasibility_raw.get("score", 50)

    prd = PRDDocument(
        app_name=opportunity.app.name,
        target_platforms=opportunity.missing_platforms,
        summary=result.get("summary", ""),
        core_features=result.get("core_features", []),
        user_scenarios=result.get("user_scenarios", []),
        tech_requirements=result.get("tech_requirements", []),
        monetization=result.get("monetization", ""),
        feasibility_score=float(feasibility_raw),
        estimated_dev_hours=dev_hours,
    )

    return prd


def _save_prd(prd: PRDDocument) -> None:
    """Save PRD to data/prds/ directory."""
    PRDS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{prd.app_name.lower().replace(' ', '-')}_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = PRDS_DIR / filename

    filepath.write_text(
        prd.model_dump_json(indent=2),
        encoding="utf-8",
    )
    print(f"[Research] PRD saved to {filepath}")


def _extract_json_from_text(text: str) -> dict:
    """Extract JSON from LLM response text, handling markdown code blocks."""
    # Try to find JSON in code blocks
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try the whole text
        json_str = text.strip()

    # Attempt to fix common JSON issues before parsing
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try truncating at the last valid closing brace
        brace_count = 0
        last_valid_pos = -1
        for i, ch in enumerate(json_str):
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    last_valid_pos = i
                    break

        if last_valid_pos > 0:
            try:
                return json.loads(json_str[: last_valid_pos + 1])
            except json.JSONDecodeError:
                pass

        # Final fallback: return minimal valid structure
        print("[Research] WARNING: Could not parse LLM JSON output, using defaults")
        return {
            "summary": text[:200] if text else "",
            "core_features": [],
            "user_scenarios": [],
            "tech_requirements": [],
            "monetization": "",
        }
