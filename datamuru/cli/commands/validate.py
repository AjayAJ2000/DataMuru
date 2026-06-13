from __future__ import annotations

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.command("validate")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--strict", is_flag=True, default=False)
@with_cli_errors
def validate_command(config_path: str, strict: bool) -> None:
    dm = DataMuru(config_path=config_path)
    issues = dm.validate()
    errors = [issue for issue in issues if issue.level == "error"]
    for issue in issues:
        style = "error" if issue.level == "error" else "warning"
        console.print(f"[{style}][{issue.level}][/{style}] {issue.path}: {issue.message}")
    if errors:
        raise SystemExit(1)
    if strict and any(issue.level == "warning" for issue in issues):
        raise SystemExit(1)
    console.print("[success]Configuration is valid.[/success]")
