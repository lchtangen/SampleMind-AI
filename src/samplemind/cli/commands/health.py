"""Run system health checks and report status."""

from __future__ import annotations

import json
import sys

from rich.console import Console
from rich.table import Table
import typer

console = Console(stderr=True)


def health_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output JSON to stdout"),
) -> None:
    """Run system health checks: database connectivity and audio libraries.

    Exits 0 when all checks pass, 1 when any check fails.
    Use --json for machine-readable output (stdout only).
    """
    from samplemind.core.health import run_all_checks

    result = run_all_checks()
    all_ok = result["status"] == "ok"

    if json_output:
        print(json.dumps(result))
        sys.exit(0 if all_ok else 1)

    # ── Rich table output ─────────────────────────────────────────────────────
    table = Table(title="SampleMind Health", show_header=True, header_style="bold cyan")
    table.add_column("Check", width=16)
    table.add_column("Status", width=8)
    table.add_column("Detail")
    table.add_column("Latency", justify="right", width=10)

    for check in result["checks"]:
        status_str = "[green]✔ ok[/green]" if check["ok"] else "[red]✗ fail[/red]"
        table.add_row(
            check["name"],
            status_str,
            check["detail"],
            f"{check['latency_ms']} ms",
        )

    console.print(table)
    console.print(
        f"\n[dim]Version:[/dim] {result['version']}  "
        + (
            "[green]All checks passed.[/green]"
            if all_ok
            else "[red]One or more checks failed.[/red]"
        )
    )

    if not all_ok:
        raise typer.Exit(1)
