"""
Run the miniapp-factory pipeline.
Entry point for executing the full Discovery → Research → Coding → Publisher flow.

Usage:
    python scripts/run_pipeline.py                  # Run one full cycle
    python scripts/run_pipeline.py --discovery-only # Only run discovery
    python scripts/run_pipeline.py --category photo # Search a specific category
"""

import sys
import os
import argparse
from pathlib import Path

# Fix Windows encoding for emoji/unicode output
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add agents/ to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "core" / "agents"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from orchestrator.pipeline import run_pipeline_once, build_pipeline
from discovery.agent import run_discovery
from shared.database import list_projects

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Mini-program Factory Pipeline")
    parser.add_argument(
        "--discovery-only",
        action="store_true",
        help="Only run discovery phase (find opportunities)",
    )
    parser.add_argument(
        "--category",
        default="ai",
        help="App category to search (default: ai)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max apps to analyze (default: 50)",
    )
    parser.add_argument(
        "--list-projects",
        action="store_true",
        help="List all projects in the database",
    )
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold blue]🏭 Mini-program Factory[/bold blue]\n"
        "Automated discovery → research → coding → publishing",
        border_style="blue",
    ))

    if args.list_projects:
        _show_projects()
        return

    if args.discovery_only:
        _run_discovery_only(args.category, args.limit)
        return

    # Run full pipeline
    console.print("\n[bold]Starting full pipeline...[/bold]\n")

    try:
        result = run_pipeline_once()

        if result.get("error"):
            console.print(f"[red]Pipeline error:[/red] {result['error']}")
        else:
            project = result.get("current_project")
            if project:
                console.print(f"\n[green]✅ Pipeline complete![/green]")
                console.print(f"   App: {project.app_name}")
                console.print(f"   Status: {project.status.value}")
                console.print(f"   Path: {project.project_path}")
            else:
                console.print("[yellow]Pipeline finished but no project created.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Pipeline failed:[/red] {e}")
        raise


def _run_discovery_only(category: str, limit: int):
    """Run only the discovery phase and display results."""
    console.print(f"\n[bold]🔍 Running discovery for category: {category}[/bold]\n")

    opportunities = run_discovery(category=category, limit=limit)

    if not opportunities:
        console.print("[yellow]No opportunities found.[/yellow]")
        return

    table = Table(title=f"Found {len(opportunities)} Opportunities")
    table.add_column("App", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Missing Platforms", style="yellow")
    table.add_column("Difficulty", style="magenta")
    table.add_column("Competition", style="red")

    for opp in opportunities[:20]:  # Show top 20
        table.add_row(
            opp.app.name,
            f"{opp.gap_score:.0f}",
            ", ".join(p.value for p in opp.missing_platforms),
            opp.estimated_difficulty,
            opp.competition_level,
        )

    console.print(table)


def _show_projects():
    """Display all projects in the database."""
    projects = list_projects()
    if not projects:
        console.print("[yellow]No projects in database.[/yellow]")
        return

    table = Table(title="All Projects")
    table.add_column("ID", style="dim")
    table.add_column("App Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Platforms", style="yellow")
    table.add_column("Updated", style="dim")

    for p in projects:
        table.add_row(
            p.id,
            p.app_name,
            p.status.value,
            ", ".join(pl.value for pl in p.target_platforms),
            p.updated_at.strftime("%Y-%m-%d %H:%M") if p.updated_at else "-",
        )

    console.print(table)


if __name__ == "__main__":
    main()
