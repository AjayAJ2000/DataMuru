from __future__ import annotations

import json

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.command("doctor")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def doctor_command(config_path: str, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    report = dm.doctor()
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict(), indent=2))
        if not report.success:
            raise SystemExit(1)
        return
    console.print(f"[primary]Provider[/primary]: [code]{report.provider}[/code]")
    console.print(f"[primary]Environment[/primary]: [code]{report.environment}[/code]")
    for check in report.checks:
        style = "success" if check.level == "ok" else "warning" if check.level == "warning" else "error"
        console.print(f"[{style}][{check.level}][/{style}] {check.code}: {check.message}")
    if not report.success:
        raise SystemExit(1)
