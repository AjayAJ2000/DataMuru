from __future__ import annotations

import json

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.group("enterprise")
def enterprise_group() -> None:
    """Inspect Enterprise activation and hosted control plane readiness."""


@enterprise_group.group("activation")
def activation_group() -> None:
    """Inspect local Enterprise activation readiness."""


@activation_group.command("check")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def activation_check(config_path: str, output_format: str) -> None:
    report = DataMuru(config_path=config_path).enterprise_activation_report()
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict(), indent=2))
    else:
        status = "ready" if report.ready else "blocked"
        style = "success" if report.ready else "error"
        console.print(f"[primary]Enterprise activation[/primary]: [{style}]{status}[/{style}]")
        console.print(f"Project: [code]{report.project}[/code]")
        console.print(f"Provider: [code]{report.provider}[/code]")
        for check in report.checks:
            style = "error" if check.level == "error" else "warning"
            console.print(f"[{style}][{check.level}][/{style}] {check.path}: {check.message}")
        if report.ready:
            console.print("[success]Activation payload is ready for Enterprise onboarding.[/success]")
    if not report.ready:
        raise SystemExit(1)
