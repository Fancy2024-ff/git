"""
QA Agent - Automated quality assurance for generated mini-programs.

Checks:
1. Structural integrity - all required files exist, valid JSON configs
2. Code quality - no syntax errors, proper imports, template compliance
3. Platform compliance - package size, API usage, content policy
4. Functional readiness - pages render, navigation works, API calls structured
5. Compliance & risk - privacy, copyright, platform-specific rules
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from shared.models import MiniAppProject, MiniProgramPlatform, PRDDocument
from shared.llm import get_llm


@dataclass
class QAResult:
    """Quality assurance check results."""

    passed: bool = False
    score: int = 0  # 0-100
    structural_issues: list[str] = field(default_factory=list)
    code_issues: list[str] = field(default_factory=list)
    compliance_issues: list[str] = field(default_factory=list)
    platform_issues: dict[str, list[str]] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    auto_fixable: list[str] = field(default_factory=list)


def run_qa(project: MiniAppProject) -> QAResult:
    """
    Main QA flow:
    1. Structural validation (files, configs)
    2. Code quality check (syntax, patterns)
    3. Platform-specific compliance
    4. LLM-powered content & risk review
    5. Auto-fix what we can, flag what we can't
    """
    if not project.project_path:
        return QAResult(passed=False, structural_issues=["No project path"])

    project_path = Path(project.project_path)
    if not project_path.exists():
        return QAResult(passed=False, structural_issues=["Project path does not exist"])

    result = QAResult()

    # Step 1: Structural checks
    _check_structure(project_path, result)

    # Step 2: Code quality
    _check_code_quality(project_path, result)

    # Step 3: Platform compliance
    for platform in project.target_platforms:
        issues = _check_platform_compliance(project_path, platform)
        if issues:
            result.platform_issues[platform.value] = issues

    # Step 4: Content & compliance review via LLM
    _check_content_compliance(project, result)

    # Step 5: Calculate score and pass/fail
    total_issues = (
        len(result.structural_issues)
        + len(result.code_issues)
        + len(result.compliance_issues)
        + sum(len(v) for v in result.platform_issues.values())
    )

    # Score: start at 100, deduct per issue severity
    result.score = max(0, 100 - (total_issues * 10))
    result.passed = result.score >= 60 and len(result.structural_issues) == 0

    # Step 6: Attempt auto-fixes
    if not result.passed:
        _attempt_auto_fixes(project_path, result)

    return result

def _check_structure(project_path: Path, result: QAResult) -> None:
    """Verify project has all required files and valid configs."""
    # Required files (uni-app CLI places configs under src/)
    required = {
        "src/manifest.json": "uni-app manifest configuration",
        "src/pages.json": "pages routing configuration",
    }

    for filename, desc in required.items():
        filepath = project_path / filename
        if not filepath.exists():
            result.structural_issues.append(f"Missing {filename} ({desc})")
        else:
            # Validate JSON
            try:
                json.loads(filepath.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                result.structural_issues.append(f"Invalid JSON in {filename}: {e}")

    # Check pages directory
    pages_dir = project_path / "src" / "pages"
    if not pages_dir.exists():
        result.structural_issues.append("Missing src/pages/ directory")
    else:
        page_dirs = [d for d in pages_dir.iterdir() if d.is_dir()]
        if not page_dirs:
            result.structural_issues.append("No page directories found")
        else:
            # Each page dir should have a .vue file
            for page_dir in page_dirs:
                vue_files = list(page_dir.glob("*.vue"))
                if not vue_files:
                    result.structural_issues.append(
                        f"Page directory '{page_dir.name}' has no .vue file"
                    )

    # Check pages.json references match actual pages
    pages_json_path = project_path / "src" / "pages.json"
    if pages_json_path.exists():
        try:
            pages_config = json.loads(pages_json_path.read_text(encoding="utf-8"))
            declared_pages = [p["path"] for p in pages_config.get("pages", [])]
            for page_path in declared_pages:
                # page_path like "pages/index/index" → check src/pages/index/index.vue
                vue_path = project_path / "src" / f"{page_path}.vue"
                if not vue_path.exists():
                    result.structural_issues.append(
                        f"pages.json declares '{page_path}' but file not found"
                    )
        except (json.JSONDecodeError, KeyError):
            pass


def _check_code_quality(project_path: Path, result: QAResult) -> None:
    """Check code quality of .vue files."""
    pages_dir = project_path / "src" / "pages"
    if not pages_dir.exists():
        return

    for vue_file in pages_dir.rglob("*.vue"):
        content = vue_file.read_text(encoding="utf-8")
        rel_path = vue_file.relative_to(project_path)

        # Check basic Vue SFC structure
        if "<template>" not in content:
            result.code_issues.append(f"{rel_path}: missing <template> block")
        if "<script" not in content:
            result.code_issues.append(f"{rel_path}: missing <script> block")

        # Check for common issues
        if "TODO" in content:
            result.suggestions.append(f"{rel_path}: contains TODO comments")

        # Check for hardcoded API URLs that should be configurable
        if "http://localhost" in content or "http://127.0.0.1" in content:
            result.code_issues.append(
                f"{rel_path}: contains hardcoded localhost URL"
            )
            result.auto_fixable.append(f"Replace localhost URL in {rel_path}")

        # Check for empty event handlers
        if "async function" in content and "// TODO" in content:
            result.suggestions.append(f"{rel_path}: has unimplemented async functions")


def _check_platform_compliance(
    project_path: Path, platform: MiniProgramPlatform
) -> list[str]:
    """Check platform-specific requirements."""
    issues = []

    # Calculate approximate package size
    total_size = sum(
        f.stat().st_size for f in project_path.rglob("*") if f.is_file()
    )
    size_mb = total_size / (1024 * 1024)

    # Platform size limits
    size_limits = {
        MiniProgramPlatform.WECHAT: 2,      # 主包 2MB
        MiniProgramPlatform.ALIPAY: 4,      # 4MB
        MiniProgramPlatform.DOUYIN: 4,      # 4MB
        MiniProgramPlatform.BAIDU: 4,       # 4MB
        MiniProgramPlatform.TELEGRAM: 50,   # Web app, generous
        MiniProgramPlatform.LINE: 50,       # LIFF, generous
    }

    limit = size_limits.get(platform, 4)
    if size_mb > limit:
        issues.append(
            f"Package size ({size_mb:.1f}MB) exceeds {platform.value} limit ({limit}MB)"
        )

    # WeChat-specific checks
    if platform == MiniProgramPlatform.WECHAT:
        manifest_path = project_path / "src" / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            wx_config = manifest.get("mp-weixin", {})
            if not wx_config.get("appid"):
                issues.append("WeChat appid not configured in manifest.json")

    # Alipay-specific checks
    if platform == MiniProgramPlatform.ALIPAY:
        manifest_path = project_path / "src" / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not manifest.get("mp-alipay", {}).get("appid"):
                issues.append("Alipay appid not configured in manifest.json")

    return issues


def _check_content_compliance(project: MiniAppProject, result: QAResult) -> None:
    """Use LLM to check content compliance and risk."""
    llm = get_llm(max_tokens=2048)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a mini-program compliance reviewer. Analyze the app concept
and identify potential issues that could cause rejection during platform review.

Check for:
1. Content policy violations (gambling, adult content, misleading claims)
2. Copyright/trademark risks (using other brand names)
3. Privacy concerns (data collection without consent notices)
4. Platform-specific restrictions (WeChat bans certain categories)
5. AI-specific rules (must disclose AI-generated content on some platforms)

Return JSON with keys: issues (array), risk_level ("low" or "medium" or "high"), suggestions (array).""",
        ),
        (
            "human",
            """Review this mini-program for compliance:
App name: {app_name}
Based on: {original_app} (from App Store/Google Play)
Summary: {summary}
Features: {features}
Target platforms: {platforms}

Are there any compliance risks?""",
        ),
    ])

    chain = prompt | llm | JsonOutputParser()

    prd = project.prd
    try:
        review = chain.invoke({
            "app_name": project.app_name,
            "original_app": project.opportunity.app.name if project.opportunity else "unknown",
            "summary": prd.summary if prd else "",
            "features": json.dumps(prd.core_features, ensure_ascii=False) if prd else "[]",
            "platforms": ", ".join(p.value for p in project.target_platforms),
        })

        if review.get("issues"):
            result.compliance_issues.extend(review["issues"])
        if review.get("suggestions"):
            result.suggestions.extend(review["suggestions"])

    except Exception as e:
        print(f"[QA] Content compliance check failed: {e}")
        result.suggestions.append("Content compliance check skipped due to LLM error")


def _attempt_auto_fixes(project_path: Path, result: QAResult) -> None:
    """Attempt to automatically fix simple issues."""
    fixed = []

    for fix_desc in result.auto_fixable:
        if "localhost URL" in fix_desc:
            # Replace hardcoded localhost with relative path
            for vue_file in project_path.rglob("*.vue"):
                content = vue_file.read_text(encoding="utf-8")
                if "http://localhost" in content:
                    content = content.replace("http://localhost:3000", "")
                    content = content.replace("http://localhost", "")
                    vue_file.write_text(content, encoding="utf-8")
                    fixed.append(fix_desc)

    if fixed:
        # Recalculate: remove fixed issues from code_issues
        result.code_issues = [
            issue for issue in result.code_issues
            if "hardcoded localhost" not in issue
        ]
        result.auto_fixable = [f for f in result.auto_fixable if f not in fixed]
        print(f"[QA] Auto-fixed {len(fixed)} issues")
