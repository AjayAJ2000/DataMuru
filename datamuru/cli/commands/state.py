from __future__ import annotations

import json

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.group("state")
def state_group() -> None:
    """Inspect state backend readiness and execution boundaries."""


@state_group.command("inspect")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def state_inspect(config_path: str, output_format: str) -> None:
    report = DataMuru(config_path=config_path).state_backend_report()
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict(), indent=2))
        if not report.success:
            raise SystemExit(1)
        return

    status = "ready" if report.success else "blocked"
    style = "success" if report.success else "error"
    console.print(f"[primary]State backend[/primary]: [code]{report.backend}[/code] [{style}]{status}[/{style}]")
    console.print(f"Location: [code]{report.location}[/code]")
    if report.resolved_location:
        console.print(f"Resolved location: [code]{report.resolved_location}[/code]")
    console.print(f"Mode: [code]{report.mode}[/code]")
    for check in report.checks:
        style = "success" if check.level == "ok" else "warning" if check.level == "warning" else "error"
        console.print(f"[{style}][{check.level}][/{style}] {check.code}: {check.message}")
    if not report.success:
        raise SystemExit(1)
