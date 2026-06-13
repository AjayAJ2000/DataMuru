from __future__ import annotations

import json

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console, render_plan_symbol


@click.command("plan")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--target", default=None)
@click.option("--out", "out_path", default=None)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def plan_command(config_path: str, target: str | None, out_path: str | None, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    result = dm.plan(target=target)
    if out_path:
        dm.save_plan(output_path=out_path, target=target)
    if output_format == "json":
        console.print_json(json.dumps(result.to_dict(), indent=2))
        return
    console.print(f"[primary]DataMuru Plan[/primary] - environment: [code]{result.environment}[/code]")
    if target and not result.changes:
        console.print(f"[warning]No resources matched target '{target}'.[/warning]")
        return
    for change in result.changes:
        console.print(f"  {render_plan_symbol(change.action)} {change.resource.address} [muted]({change.reason})[/muted]")
