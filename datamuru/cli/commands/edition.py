from __future__ import annotations

import json

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.group("edition")
def edition_group() -> None:
    """Inspect edition-aware product metadata."""


@edition_group.command("show")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def edition_show(config_path: str, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    summary = dm.edition_summary()
    if output_format == "json":
        console.print_json(json.dumps(summary.to_dict(), indent=2))
        return
    console.print(f"[primary]Edition[/primary]: [code]{summary.edition}[/code]")
    console.print(f"Enabled features: {', '.join(summary.enabled_features) if summary.enabled_features else 'none'}")
    console.print(
        f"Restricted features: {', '.join(summary.restricted_features) if summary.restricted_features else 'none'}"
    )
