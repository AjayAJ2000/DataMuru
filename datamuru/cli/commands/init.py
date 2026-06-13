from __future__ import annotations

from pathlib import Path

import click

from datamuru.bootstrap import ProjectScaffolder

from ..guard import with_cli_errors
from ..output import console


@click.command("init")
@click.option("--name", default="datamuru-project", show_default=True)
@click.option("--provider", default="databricks", show_default=True)
@click.option("--cloud", default="azure", show_default=True)
@click.option("--edition", default="open-source", show_default=True)
@click.option("--output-dir", default=".", show_default=True)
@with_cli_errors
def init_command(name: str, provider: str, cloud: str, edition: str, output_dir: str) -> None:
    scaffolder = ProjectScaffolder()
    created = scaffolder.scaffold(output_dir, name=name, provider=provider, cloud=cloud, edition=edition)
    console.print(
        f"[success]Created[/success] {len(created)} bootstrap artifacts in [code]{Path(output_dir).resolve()}[/code]"
    )
