from __future__ import annotations

import json
from pathlib import Path

import click

from datamuru.agile import export_github_issue_drafts

from ..guard import with_cli_errors
from ..output import console


@click.group("agile")
def agile_group() -> None:
    """Export agile planning artifacts from DataMuru roadmap docs."""


@agile_group.command("export")
@click.option(
    "--format",
    "export_format",
    default="github-issues",
    show_default=True,
    type=click.Choice(["github-issues"]),
    help="Export format.",
)
@click.option(
    "--source",
    "source_path",
    default="docs/product/github-project-board.md",
    show_default=True,
    help="Markdown source containing the backlog table.",
)
@click.option("--out", "output_dir", required=True, help="Directory where issue drafts will be written.")
@click.option("--release-target", default=None, help="Only export rows for one release target, for example 0.5.0a0.")
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def agile_export_command(
    export_format: str,
    source_path: str,
    output_dir: str,
    release_target: str | None,
    output_format: str,
) -> None:
    if export_format != "github-issues":  # pragma: no cover - click choice prevents this.
        raise click.ClickException(f"Unsupported agile export format: {export_format}")
    result = export_github_issue_drafts(
        source_path=source_path,
        output_dir=output_dir,
        release_target=release_target,
    )
    if output_format == "json":
        console.print_json(json.dumps(result.to_dict(), indent=2))
        return
    console.print(
        f"[success]Exported[/success] {len(result.drafts)} GitHub issue draft(s) to "
        f"[code]{Path(output_dir).resolve()}[/code]"
    )
    console.print(f"Manifest: [code]{result.manifest_path}[/code]")
