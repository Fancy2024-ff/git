"""
Task dispatcher - sends PRD to the Node.js generator service via HTTP.
"""

import json
from dataclasses import dataclass

import httpx

from shared.models import PRDDocument
from config.settings import GENERATOR_URL


@dataclass
class GeneratorResult:
    """Result from the code generator service."""

    success: bool
    project_path: str = ""
    pages_generated: int = 0
    platforms: list[str] = None
    error: str = ""

    def __post_init__(self):
        if self.platforms is None:
            self.platforms = []


def dispatch_to_generator(prd: PRDDocument, template: str = "ai-tool") -> GeneratorResult:
    """
    Send PRD to the Node.js generator service.
    Returns the generated project path and metadata.
    """
    try:
        # Convert PRD to the format expected by the generator
        payload = {
            "prd": {
                "app_name": prd.app_name,
                "summary": prd.summary,
                "core_features": prd.core_features,
                "target_platforms": [p.value for p in prd.target_platforms],
                "monetization": prd.monetization,
            },
            "template": _select_template(prd),
        }

        response = httpx.post(
            f"{GENERATOR_URL}/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        return GeneratorResult(
            success=data.get("success", False),
            project_path=data.get("project_path", ""),
            pages_generated=data.get("pages_generated", 0),
            platforms=data.get("platforms", []),
        )

    except httpx.ConnectError:
        return GeneratorResult(
            success=False,
            error=f"Cannot connect to generator service at {GENERATOR_URL}",
        )
    except Exception as e:
        return GeneratorResult(success=False, error=str(e))


def _select_template(prd: PRDDocument) -> str:
    """Select the best template based on PRD content."""
    summary_lower = prd.summary.lower()
    features_text = json.dumps(prd.core_features).lower()

    if any(kw in summary_lower or kw in features_text for kw in ["chat", "对话", "conversation"]):
        return "ai-chat"
    if any(kw in summary_lower or kw in features_text for kw in ["image", "图片", "photo", "绘画"]):
        return "ai-image"
    return "ai-tool"


def check_generator_health() -> bool:
    """Check if the generator service is running."""
    try:
        response = httpx.get(f"{GENERATOR_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
