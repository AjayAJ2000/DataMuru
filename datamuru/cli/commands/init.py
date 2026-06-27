from __future__ import annotations

from pathlib import Path

import click

from datamuru.bootstrap import ProjectScaffolder

from ..guard import with_cli_errors
from ..output import console


@click.command("init")
@click.option("--name", default="datamuru-project", show_default=True)
@click.option("--provider", default="databricks", show_default=True)
@click.option("--cloud", default=None, help="Provider cloud; defaults to snowflake for Snowflake and azure otherwise.")
@click.option("--edition", default="open-source", show_default=True)
@click.option(
    "--execution-mode",
    default="state-only",
    show_default=True,
    type=click.Choice(["state-only", "live-readonly", "live-apply"]),
)
@click.option("--output-dir", default=".", show_default=True)
@with_cli_errors
def init_command(
    name: str,
    provider: str,
    cloud: str | None,
    edition: str,
    execution_mode: str,
    output_dir: str,
) -> None:
    scaffolder = ProjectScaffolder()
    resolved_cloud = cloud or ("snowflake" if provider == "snowflake" else "azure")
    created = scaffolder.scaffold(
        output_dir,
        name=name,
        provider=provider,
        cloud=resolved_cloud,
        edition=edition,
        execution_mode=execution_mode,
    )
    console.print(
        f"[success]Created[/success] {len(created)} bootstrap artifacts in [code]{Path(output_dir).resolve()}[/code]"
    )
