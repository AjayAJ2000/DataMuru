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


@enterprise_group.group("control-plane")
def control_plane_group() -> None:
    """Build hosted control plane handoff contracts."""


@enterprise_group.group("activation")
def activation_group() -> None:
    """Inspect local Enterprise activation readiness."""


@control_plane_group.command("architecture")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_path", type=click.Path(dir_okay=False, path_type=str))
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def control_plane_architecture(config_path: str, output_path: str | None, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    architecture = dm.enterprise_control_plane_architecture()
    written_path = None
    if output_path:
        written_path = dm.write_enterprise_control_plane_architecture(output_path)

    if output_format == "json":
        console.print_json(json.dumps(architecture.to_dict(), indent=2))
        return

    console.print("[primary]Hosted control plane architecture[/primary]: reference-architecture")
    console.print(f"Project: [code]{architecture.project}[/code]")
    console.print(f"Provider: [code]{architecture.provider}[/code]")
    console.print(f"Components: [code]{len(architecture.components)}[/code]")
    console.print(f"Decisions: [code]{len(architecture.decisions)}[/code]")
    console.print(f"Backlog items: [code]{len(architecture.implementation_backlog)}[/code]")
    if written_path:
        console.print(f"[success]Architecture contract written:[/success] [code]{written_path}[/code]")


@control_plane_group.command("contract")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_path", type=click.Path(dir_okay=False, path_type=str))
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def control_plane_contract(config_path: str, output_path: str | None, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    contract = dm.enterprise_control_plane_contract()
    written_path = None
    if output_path:
        written_path = dm.write_enterprise_control_plane_contract(output_path)

    if output_format == "json":
        console.print_json(json.dumps(contract.to_dict(), indent=2))
    else:
        status = "ready" if contract.ready else "blocked"
        style = "success" if contract.ready else "error"
        console.print(f"[primary]Hosted control plane contract[/primary]: [{style}]{status}[/{style}]")
        console.print(f"Project: [code]{contract.project}[/code]")
        console.print(f"Provider: [code]{contract.provider}[/code]")
        console.print(f"State backend: [code]{contract.state.backend}[/code] ({contract.state.mode})")
        for check in contract.checks:
            style = "error" if check.level == "error" else "warning"
            console.print(f"[{style}][{check.level}][/{style}] {check.path}: {check.message}")
        if written_path:
            console.print(f"[success]Contract written:[/success] [code]{written_path}[/code]")
        if contract.ready:
            console.print("[success]Control plane contract is ready for Enterprise handoff.[/success]")

    if not contract.ready:
        raise SystemExit(1)


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


@activation_group.command("evidence")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_path", required=True, type=click.Path(dir_okay=False, path_type=str))
@click.option(
    "--allow-blocked",
    is_flag=True,
    help="Write blocked audit evidence with failed checks for support triage.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def activation_evidence(config_path: str, output_path: str, allow_blocked: bool, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    report = dm.enterprise_activation_evidence_report()
    if not report.ready and not allow_blocked:
        if output_format == "json":
            console.print_json(json.dumps(report.to_dict(), indent=2))
        else:
            console.print("[error]Activation evidence not written because activation is blocked.[/error]")
            for check in report.activation.checks:
                console.print(f"[error][{check.level}][/error] {check.path}: {check.message}")
            console.print("[accent]Use --allow-blocked only when support asked for blocked audit evidence.[/accent]")
        raise SystemExit(1)

    resolved = dm.write_enterprise_activation_evidence(output_path)
    payload = {"path": str(resolved), "ready": report.ready, "status": report.status}
    if output_format == "json":
        console.print_json(json.dumps(payload, indent=2))
        return

    style = "success" if report.ready else "warning"
    console.print(f"[{style}]Activation evidence written:[/{style}] [code]{resolved}[/code]")
    if not report.ready:
        console.print("[warning]Evidence includes blocked checks for support triage.[/warning]")
