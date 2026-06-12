"""
LangGraph Pipeline - The main orchestrator that drives the entire factory loop.

Flow: Discovery → Research → Coding → QA → Publishing → Review → (loop back)
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from shared.models import (
    GapOpportunity,
    MiniAppProject,
    PRDDocument,
    ProjectStatus,
)
from shared.database import save_project, list_projects
from discovery.agent import run_discovery
from research.agent import run_research
from coding.agent import run_coding
from qa.agent import run_qa, QAResult
from publisher.agent import run_publisher
from review.agent import run_review, ReviewDecision


class PipelineState(TypedDict):
    """State shared across the pipeline."""

    opportunities: list[GapOpportunity]
    current_project: MiniAppProject | None
    prd: PRDDocument | None
    project_path: str
    qa_result: dict
    publish_result: dict
    review_result: dict
    error: str
    should_continue: bool


def discovery_node(state: PipelineState) -> dict:
    """Discovery Agent: find apps that exist in stores but not in mini-programs."""
    try:
        opportunities = run_discovery()
        if not opportunities:
            return {"error": "No opportunities found", "should_continue": False}

        # Pick the best opportunity (highest gap_score)
        best = max(opportunities, key=lambda x: x.gap_score)

        # Create project record
        import uuid
        project = MiniAppProject(
            id=str(uuid.uuid4())[:8],
            app_name=best.app.name,
            status=ProjectStatus.DISCOVERED,
            opportunity=best,
            target_platforms=best.missing_platforms,
        )
        save_project(project)

        return {
            "opportunities": opportunities,
            "current_project": project,
            "should_continue": True,
        }
    except Exception as e:
        return {"error": f"Discovery failed: {e}", "should_continue": False}


def research_node(state: PipelineState) -> dict:
    """Research Agent: analyze the app and generate PRD."""
    project = state["current_project"]
    if not project or not project.opportunity:
        return {"error": "No project to research", "should_continue": False}

    try:
        project.status = ProjectStatus.ANALYZING
        save_project(project)

        prd = run_research(project.opportunity)

        project.status = ProjectStatus.PRD_READY
        project.prd = prd
        save_project(project)

        return {"prd": prd, "current_project": project, "should_continue": True}
    except Exception as e:
        return {"error": f"Research failed: {e}", "should_continue": False}


def coding_node(state: PipelineState) -> dict:
    """Coding Agent: generate mini-program code from PRD."""
    project = state["current_project"]
    prd = state["prd"]
    if not project or not prd:
        return {"error": "No PRD to code from", "should_continue": False}

    try:
        project.status = ProjectStatus.CODING
        save_project(project)

        project_path = run_coding(prd)

        project.status = ProjectStatus.CODE_READY
        project.project_path = project_path
        save_project(project)

        return {"project_path": project_path, "current_project": project, "should_continue": True}
    except Exception as e:
        return {"error": f"Coding failed: {e}", "should_continue": False}


def publisher_node(state: PipelineState) -> dict:
    """Publisher Agent: submit to mini-program platforms."""
    project = state["current_project"]
    if not project or not project.project_path:
        return {"error": "No project to publish", "should_continue": False}

    try:
        project.status = ProjectStatus.SUBMITTING
        save_project(project)

        result = run_publisher(project)

        project.status = ProjectStatus.UNDER_REVIEW
        project.submission_results = result
        save_project(project)

        return {"publish_result": result, "should_continue": True}
    except Exception as e:
        return {"error": f"Publishing failed: {e}", "should_continue": False}


def qa_node(state: PipelineState) -> dict:
    """QA Agent: validate the generated project before publishing."""
    project = state["current_project"]
    if not project or not project.project_path:
        return {"error": "No project to QA", "should_continue": False}

    try:
        qa_result = run_qa(project)

        if qa_result.passed:
            print(f"[QA] Passed with score {qa_result.score}/100")
            return {"qa_result": {"passed": True, "score": qa_result.score}, "should_continue": True}
        else:
            print(f"[QA] Failed with score {qa_result.score}/100")
            print(f"[QA] Issues: {qa_result.structural_issues + qa_result.code_issues}")
            # Still continue but mark the issues
            return {
                "qa_result": {
                    "passed": False,
                    "score": qa_result.score,
                    "issues": qa_result.structural_issues + qa_result.code_issues,
                    "compliance": qa_result.compliance_issues,
                },
                "should_continue": qa_result.score >= 40,  # Hard fail below 40
            }
    except Exception as e:
        return {"error": f"QA failed: {e}", "should_continue": True}  # Don't block on QA errors


def review_node(state: PipelineState) -> dict:
    """Review Agent: analyze results and decide next action."""
    project = state["current_project"]
    if not project:
        return {"should_continue": False}

    try:
        report = run_review(project)

        review_data = {
            "decision": report.decision.value,
            "reasoning": report.reasoning,
            "action_items": report.action_items,
        }

        # Decide whether to loop back for another app
        should_loop = report.decision in (
            ReviewDecision.MONITOR,
            ReviewDecision.SCALE_UP,
        )

        return {"review_result": review_data, "should_continue": should_loop}
    except Exception as e:
        return {"error": f"Review failed: {e}", "should_continue": False}


def should_continue_after_qa(state: PipelineState) -> str:
    """After QA: proceed to publish only if passed or score is acceptable."""
    qa = state.get("qa_result", {})
    if not state.get("should_continue", False):
        return END
    if qa.get("passed", False) or qa.get("score", 0) >= 40:
        return "publisher"
    return END


def should_continue_after_review(state: PipelineState) -> str:
    """After review: decide whether to loop back for another opportunity."""
    if not state.get("should_continue", False):
        return END
    if state.get("error"):
        return END
    return "discovery"


# Build the graph
def build_pipeline() -> StateGraph:
    """Build and compile the LangGraph pipeline."""
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("discovery", discovery_node)
    workflow.add_node("research", research_node)
    workflow.add_node("coding", coding_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("publisher", publisher_node)
    workflow.add_node("review", review_node)

    # Linear flow with conditional gates
    workflow.set_entry_point("discovery")
    workflow.add_edge("discovery", "research")
    workflow.add_edge("research", "coding")
    workflow.add_edge("coding", "qa")

    # QA gate: only proceed to publish if quality is acceptable
    workflow.add_conditional_edges("qa", should_continue_after_qa)

    workflow.add_edge("publisher", "review")

    # Review decides: loop back or end
    workflow.add_conditional_edges("review", should_continue_after_review)

    return workflow.compile()


def run_pipeline_once():
    """Run the pipeline for one iteration (discover + build one app)."""
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "opportunities": [],
        "current_project": None,
        "prd": None,
        "project_path": "",
        "qa_result": {},
        "publish_result": {},
        "review_result": {},
        "error": "",
        "should_continue": True,
    }

    result = pipeline.invoke(initial_state)
    return result
