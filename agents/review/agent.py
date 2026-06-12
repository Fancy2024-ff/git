"""
Review Agent - Post-launch monitoring, feedback analysis, and iteration decisions.

Responsibilities:
1. Monitor submission status (approved/rejected)
2. Analyze rejection reasons and generate fixes
3. Track live metrics (if available): visits, retention, conversion
4. Decide next action: optimize, create variant, or deprecate
5. Feed insights back into the pipeline for the next cycle
"""

import json
from datetime import datetime
from pathlib import Path
from enum import Enum

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from shared.models import MiniAppProject, ProjectStatus
from shared.llm import get_llm
from shared.database import save_project, list_projects
from config.settings import DATA_DIR


class ReviewDecision(str, Enum):
    """Possible decisions after review."""
    OPTIMIZE = "optimize"          # Improve current version
    CREATE_VARIANT = "variant"     # Create a similar app for different niche
    SCALE_UP = "scale_up"          # App doing well, push to more platforms
    DEPRECATE = "deprecate"        # App not viable, move on
    RESUBMIT = "resubmit"         # Fix rejection issues and resubmit
    MONITOR = "monitor"            # Keep watching, no action needed


class ReviewReport(BaseModel):
    """Output of the review agent."""
    project_id: str
    app_name: str
    decision: ReviewDecision
    reasoning: str = ""
    action_items: list[str] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    rejection_analysis: dict | None = None
    variant_suggestions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


def run_review(project: MiniAppProject) -> ReviewReport:
    """
    Main review flow:
    1. Check current status (approved? rejected? live?)
    2. If rejected → analyze why, suggest fixes
    3. If live → check metrics, decide next steps
    4. Generate action items for the pipeline
    """
    # Step 1: Determine situation
    if project.status == ProjectStatus.REJECTED:
        return _handle_rejection(project)
    elif project.status in (ProjectStatus.LIVE, ProjectStatus.APPROVED):
        return _handle_live_app(project)
    elif project.status == ProjectStatus.UNDER_REVIEW:
        return _handle_pending_review(project)
    else:
        return ReviewReport(
            project_id=project.id,
            app_name=project.app_name,
            decision=ReviewDecision.MONITOR,
            reasoning=f"Project in status '{project.status.value}', no review action needed",
        )


def run_review_cycle() -> list[ReviewReport]:
    """
    Review ALL projects in the database.
    Called periodically to check on everything.
    """
    reports = []

    # Check all projects that need attention
    review_statuses = [
        ProjectStatus.UNDER_REVIEW,
        ProjectStatus.APPROVED,
        ProjectStatus.REJECTED,
        ProjectStatus.LIVE,
    ]

    for status in review_statuses:
        projects = list_projects(status=status)
        for project in projects:
            report = run_review(project)
            reports.append(report)
            _save_review_report(report)

    # Generate cycle summary
    if reports:
        _generate_cycle_summary(reports)

    return reports


def _handle_rejection(project: MiniAppProject) -> ReviewReport:
    """Analyze why the app was rejected and suggest fixes."""
    llm = get_llm(max_tokens=2048)

    # Get rejection details from submission results
    rejection_info = project.submission_results
    rejection_reasons = []
    for platform, result in rejection_info.items():
        if isinstance(result, dict) and result.get("status") == "rejected":
            rejection_reasons.append(
                f"{platform}: {result.get('reason', 'unknown')}"
            )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a mini-program submission expert. Analyze rejection reasons and provide
actionable fixes. Common rejection reasons:
- 名称不规范 (naming issues)
- 功能不完善 (incomplete functionality)
- 内容违规 (content violation)
- 隐私问题 (privacy issues)
- 类目不匹配 (category mismatch)
- 诱导关注/分享 (forced sharing)

Return JSON: {
  "root_cause": "...",
  "fixes": ["fix1", "fix2"],
  "can_auto_fix": true/false,
  "estimated_fix_hours": N,
  "should_resubmit": true/false,
  "alternative_approach": "..." (if resubmit not viable)
}""",
        ),
        (
            "human",
            """App '{app_name}' was rejected.
Rejection reasons: {reasons}
App summary: {summary}
Target platforms: {platforms}

Analyze and suggest fixes.""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        analysis = chain.invoke({
            "app_name": project.app_name,
            "reasons": "; ".join(rejection_reasons) if rejection_reasons else "Unknown",
            "summary": project.prd.summary if project.prd else "",
            "platforms": ", ".join(p.value for p in project.target_platforms),
        })

        decision = (
            ReviewDecision.RESUBMIT if analysis.get("should_resubmit", True)
            else ReviewDecision.DEPRECATE
        )

        return ReviewReport(
            project_id=project.id,
            app_name=project.app_name,
            decision=decision,
            reasoning=analysis.get("root_cause", ""),
            action_items=analysis.get("fixes", []),
            rejection_analysis=analysis,
        )

    except Exception as e:
        return ReviewReport(
            project_id=project.id,
            app_name=project.app_name,
            decision=ReviewDecision.MONITOR,
            reasoning=f"Rejection analysis failed: {e}",
            action_items=["Manual review needed"],
        )


def _handle_live_app(project: MiniAppProject) -> ReviewReport:
    """Review a live app: check metrics and decide next steps."""
    llm = get_llm(max_tokens=2048)

    # In production, fetch real metrics from platform APIs
    # For MVP, use LLM to suggest strategy based on what we know
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a growth strategist for mini-programs. Based on the app info,
suggest the best next action. Consider:
- Is this a category worth creating variants for?
- Should we push to more platforms?
- What optimizations could improve retention?

Return JSON: {
  "health": "good|average|poor",
  "next_action": "optimize|variant|scale_up|monitor",
  "optimization_ideas": [...],
  "variant_ideas": [...],
  "platforms_to_expand": [...]
}""",
        ),
        (
            "human",
            """App: {app_name}
Category: {category}
Current platforms: {platforms}
Features: {features}

What should we do next?""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        analysis = chain.invoke({
            "app_name": project.app_name,
            "category": project.opportunity.app.category if project.opportunity else "ai",
            "platforms": ", ".join(p.value for p in project.target_platforms),
            "features": json.dumps(
                project.prd.core_features if project.prd else [], ensure_ascii=False
            ),
        })

        decision_map = {
            "optimize": ReviewDecision.OPTIMIZE,
            "variant": ReviewDecision.CREATE_VARIANT,
            "scale_up": ReviewDecision.SCALE_UP,
            "monitor": ReviewDecision.MONITOR,
        }
        decision = decision_map.get(
            analysis.get("next_action", "monitor"), ReviewDecision.MONITOR
        )

        return ReviewReport(
            project_id=project.id,
            app_name=project.app_name,
            decision=decision,
            reasoning=f"App health: {analysis.get('health', 'unknown')}",
            action_items=analysis.get("optimization_ideas", []),
            variant_suggestions=analysis.get("variant_ideas", []),
            metrics={"health": analysis.get("health")},
        )

    except Exception as e:
        return ReviewReport(
            project_id=project.id,
            app_name=project.app_name,
            decision=ReviewDecision.MONITOR,
            reasoning=f"Live review failed: {e}",
        )


def _handle_pending_review(project: MiniAppProject) -> ReviewReport:
    """Handle apps that are still under platform review."""
    # Check how long it's been under review
    if project.updated_at:
        days_waiting = (datetime.now() - project.updated_at).days
    else:
        days_waiting = 0

    if days_waiting > 7:
        return ReviewReport(
            project_id=project.id,
            app_name=project.app_name,
            decision=ReviewDecision.MONITOR,
            reasoning=f"Under review for {days_waiting} days - may need manual follow-up",
            action_items=["Check platform admin console for review status"],
        )

    return ReviewReport(
        project_id=project.id,
        app_name=project.app_name,
        decision=ReviewDecision.MONITOR,
        reasoning=f"Under review for {days_waiting} days - normal timeline",
    )


def _save_review_report(report: ReviewReport) -> None:
    """Save review report to disk."""
    reports_dir = DATA_DIR / "reports" / "reviews"
    reports_dir.mkdir(parents=True, exist_ok=True)

    filename = f"review_{report.project_id}_{datetime.now().strftime('%Y%m%d')}.json"
    (reports_dir / filename).write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8",
    )


def _generate_cycle_summary(reports: list[ReviewReport]) -> None:
    """Generate a summary of the review cycle."""
    summary = {
        "cycle_date": datetime.now().isoformat(),
        "total_reviewed": len(reports),
        "decisions": {},
        "action_items_total": 0,
    }

    for report in reports:
        decision = report.decision.value
        summary["decisions"][decision] = summary["decisions"].get(decision, 0) + 1
        summary["action_items_total"] += len(report.action_items)

    reports_dir = DATA_DIR / "reports" / "reviews"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / f"cycle_summary_{datetime.now().strftime('%Y%m%d')}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Review] Cycle summary: {summary['total_reviewed']} reviewed, "
          f"{summary['action_items_total']} action items")
