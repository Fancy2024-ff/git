"""
Opportunity Analyzer - Evaluates each discovered app against 8 key questions.

For every discovered app, the system must answer:
1. 这个 App 背后的需求是否真实存在？ (Is the demand real?)
2. 用户是否愿意使用或付费？ (Will users pay?)
3. 国内外小程序平台有没有同类产品？ (Existing competition?)
4. 如果有，是否已经覆盖充分？ (Coverage sufficient?)
5. 这个需求是否适合做成小程序？ (Suitable for mini-program?)
6. 首版 MVP 能不能快速实现？ (MVP feasible quickly?)
7. 有没有合规、版权、平台审核风险？ (Compliance risks?)
8. 做出来后适合上架到哪个小程序平台？ (Best target platforms?)
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from shared.models import AppInfo, GapOpportunity, MiniProgramPlatform
from shared.llm import get_llm


class OpportunityEvaluation(BaseModel):
    """Full 8-question evaluation for an opportunity."""

    # Q1: Is demand real?
    demand_real: bool = True
    demand_evidence: str = ""
    demand_score: int = 0  # 0-100

    # Q2: Will users pay?
    monetization_viable: bool = True
    monetization_model: str = ""
    monetization_score: int = 0

    # Q3: Existing competition?
    has_competition: bool = False
    competitors: list[str] = Field(default_factory=list)

    # Q4: Coverage sufficient?
    coverage_sufficient: bool = False
    coverage_gaps: list[str] = Field(default_factory=list)

    # Q5: Suitable for mini-program?
    suitable_for_miniprogram: bool = True
    suitability_issues: list[str] = Field(default_factory=list)
    suitability_score: int = 0

    # Q6: MVP feasible quickly?
    mvp_feasible: bool = True
    estimated_days: int = 7
    mvp_scope: list[str] = Field(default_factory=list)

    # Q7: Compliance risks?
    compliance_risk: str = "low"  # low/medium/high
    risk_details: list[str] = Field(default_factory=list)

    # Q8: Best platforms?
    recommended_platforms: list[str] = Field(default_factory=list)
    platform_reasoning: str = ""

    # Overall
    overall_score: int = 0  # 0-100, weighted composite
    go_no_go: bool = True
    summary: str = ""


def evaluate_opportunity(opportunity: GapOpportunity) -> OpportunityEvaluation:
    """
    Run the full 8-question evaluation using LLM analysis.
    Returns a scored evaluation that determines go/no-go.
    """
    llm = get_llm(max_tokens=4096)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior product strategist evaluating mini-program business opportunities.
For each app, answer 8 critical questions to determine if it's worth building as a mini-program.

Be rigorous. Not every app translates well to mini-programs. Consider:
- Mini-program limitations (2MB package, no background execution, limited APIs)
- Chinese market preferences (WeChat ecosystem dominance)
- Platform review strictness (especially WeChat)
- Monetization constraints in mini-programs

Return a JSON evaluation.""",
        ),
        (
            "human",
            """Evaluate this opportunity:

App: {app_name}
Category: {category}
Description: {description}
Features: {features}
Downloads: {downloads}
Rating: {rating}
Missing from platforms: {missing_platforms}

Answer these 8 questions (return JSON):

1. demand_real (bool), demand_evidence (string), demand_score (0-100)
   - Is the need behind this app genuine? What's the evidence?

2. monetization_viable (bool), monetization_model (string), monetization_score (0-100)
   - Will mini-program users pay? What model works? (ads/subscription/one-time/freemium)

3. has_competition (bool), competitors (array of names)
   - Are there existing mini-programs doing similar things?

4. coverage_sufficient (bool), coverage_gaps (array)
   - If competitors exist, what gaps remain? What's not covered?

5. suitable_for_miniprogram (bool), suitability_issues (array), suitability_score (0-100)
   - Can this actually work within mini-program constraints?

6. mvp_feasible (bool), estimated_days (int), mvp_scope (array of MVP features)
   - Can we build a working MVP in under 2 weeks?

7. compliance_risk ("low"/"medium"/"high"), risk_details (array)
   - Copyright, content, privacy, platform-specific rules?

8. recommended_platforms (array of: "wechat"/"alipay"/"douyin"/"telegram"/"line"),
   platform_reasoning (string)
   - Which platforms are best for this app and why?

Also provide:
- overall_score (0-100): weighted average of all scores
- go_no_go (bool): should we build this?
- summary (string): one paragraph decision rationale""",
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
            "missing_platforms": ", ".join(p.value for p in opportunity.missing_platforms),
        })

        evaluation = OpportunityEvaluation(**result)

        # Recalculate overall score with weights
        evaluation.overall_score = _calculate_weighted_score(evaluation)
        evaluation.go_no_go = evaluation.overall_score >= 60

        return evaluation

    except Exception as e:
        print(f"[Analyzer] Evaluation failed for {opportunity.app.name}: {e}")
        # Return a conservative default
        return OpportunityEvaluation(
            overall_score=50,
            go_no_go=False,
            summary=f"Evaluation failed: {e}. Manual review recommended.",
        )


def _calculate_weighted_score(eval: OpportunityEvaluation) -> int:
    """Calculate weighted composite score."""
    weights = {
        "demand": 0.20,
        "monetization": 0.15,
        "suitability": 0.25,
        "feasibility": 0.15,
        "competition": 0.15,
        "compliance": 0.10,
    }

    score = 0.0
    score += eval.demand_score * weights["demand"]
    score += eval.monetization_score * weights["monetization"]
    score += eval.suitability_score * weights["suitability"]

    # Feasibility: convert days to score (fewer days = higher score)
    feasibility_score = max(0, 100 - (eval.estimated_days * 5)) if eval.mvp_feasible else 20
    score += feasibility_score * weights["feasibility"]

    # Competition: less coverage = higher opportunity
    competition_score = 80 if not eval.coverage_sufficient else 30
    score += competition_score * weights["competition"]

    # Compliance: lower risk = higher score
    compliance_scores = {"low": 90, "medium": 50, "high": 10}
    score += compliance_scores.get(eval.compliance_risk, 50) * weights["compliance"]

    return int(min(100, max(0, score)))


def filter_opportunities(
    opportunities: list[GapOpportunity],
    min_score: int = 60,
) -> list[tuple[GapOpportunity, OpportunityEvaluation]]:
    """
    Evaluate and filter opportunities. Only keep those that pass the 8-question test.
    Returns sorted list of (opportunity, evaluation) tuples.
    """
    evaluated = []

    for opp in opportunities:
        evaluation = evaluate_opportunity(opp)
        if evaluation.go_no_go and evaluation.overall_score >= min_score:
            evaluated.append((opp, evaluation))
            print(
                f"[Analyzer] ✅ {opp.app.name}: score={evaluation.overall_score}, GO"
            )
        else:
            print(
                f"[Analyzer] ❌ {opp.app.name}: score={evaluation.overall_score}, NO-GO"
            )

    # Sort by score descending
    evaluated.sort(key=lambda x: x[1].overall_score, reverse=True)
    return evaluated
