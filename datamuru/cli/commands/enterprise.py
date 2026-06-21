from __future__ import annotations

import json

import click

from datamuru.api import DataMuru
from datamuru.enterprise import write_activation_bundle

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


@activation_group.command("export")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_path", required=True, type=click.Path(dir_okay=False, path_type=str))
@click.option(
    "--allow-blocked",
    is_flag=True,
    help="Write a blocked bundle with failed checks for support triage.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def activation_export(config_path: str, output_path: str, allow_blocked: bool, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    report = dm.enterprise_activation_report()
    if not report.ready and not allow_blocked:
        if output_format == "json":
            console.print_json(json.dumps(report.to_dict(), indent=2))
        else:
            console.print("[error]Activation bundle not written because activation is blocked.[/error]")
            for check in report.checks:
                console.print(f"[error][{check.level}][/error] {check.path}: {check.message}")
            console.print("[accent]Use --allow-blocked only when support asked for a blocked diagnostic bundle.[/accent]")
        raise SystemExit(1)

    resolved = write_activation_bundle(report, output_path)
    payload = {"path": str(resolved), "ready": report.ready, "status": "ready" if report.ready else "blocked"}
    if output_format == "json":
        console.print_json(json.dumps(payload, indent=2))
        return

    style = "success" if report.ready else "warning"
    console.print(f"[{style}]Activation bundle written:[/{style}] [code]{resolved}[/code]")
    if not report.ready:
        console.print("[warning]Bundle includes blocked checks for support triage.[/warning]")
