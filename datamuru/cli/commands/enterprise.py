from __future__ import annotations

import json

import click

from datamuru.api import DataMuru
from datamuru.enterprise import (
    write_activation_bundle,
    write_activation_purchase_request,
    write_tenant_entitlement_record,
)
from datamuru.enterprise.fulfillment import write_fulfillment

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


@control_plane_group.command("tenant-record")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_path", required=True, type=click.Path(dir_okay=False, path_type=str))
@click.option(
    "--allow-blocked",
    is_flag=True,
    help="Write a blocked tenant entitlement record with failed checks for support triage.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def tenant_entitlement_record(
    config_path: str,
    output_path: str,
    allow_blocked: bool,
    output_format: str,
) -> None:
    record = DataMuru(config_path=config_path).enterprise_tenant_entitlement_record()
    if not record.ready and not allow_blocked:
        if output_format == "json":
            console.print_json(json.dumps(record.to_dict(), indent=2))
        else:
            console.print("[error]Tenant entitlement record not written because activation is blocked.[/error]")
            for check in record.checks:
                console.print(f"[error][{check.level}][/error] {check.path}: {check.message}")
            console.print("[accent]Use --allow-blocked only when support asked for a diagnostic record.[/accent]")
        raise SystemExit(1)

    resolved = write_tenant_entitlement_record(record, output_path)
    if output_format == "json":
        console.print_json(json.dumps(record.to_dict(), indent=2))
        return

    style = "success" if record.ready else "warning"
    console.print(f"[{style}]Tenant entitlement record written:[/{style}] [code]{resolved}[/code]")
    console.print(f"Record ID: [code]{record.record_id}[/code]")
    if not record.ready:
        console.print("[warning]Record includes blocked checks for support triage.[/warning]")


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


@activation_group.command("purchase-request")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_path", required=True, type=click.Path(dir_okay=False, path_type=str))
@click.option(
    "--allow-blocked",
    is_flag=True,
    help="Write a blocked purchase request with failed checks for support triage.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def activation_purchase_request(config_path: str, output_path: str, allow_blocked: bool, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    report = dm.enterprise_activation_report()
    if not report.ready and not allow_blocked:
        if output_format == "json":
            console.print_json(json.dumps(report.to_dict(), indent=2))
        else:
            console.print("[error]Purchase request not written because activation is blocked.[/error]")
            for check in report.checks:
                console.print(f"[error][{check.level}][/error] {check.path}: {check.message}")
            console.print("[accent]Use --allow-blocked only when support asked for a blocked diagnostic request.[/accent]")
        raise SystemExit(1)

    resolved = write_activation_purchase_request(report, output_path)
    payload = {"path": str(resolved), "ready": report.ready, "status": "ready" if report.ready else "blocked"}
    if output_format == "json":
        console.print_json(json.dumps(payload, indent=2))
        return

    style = "success" if report.ready else "warning"
    console.print(f"[{style}]Purchase request written:[/{style}] [code]{resolved}[/code]")
    if not report.ready:
        console.print("[warning]Purchase request includes blocked checks for support triage.[/warning]")


@activation_group.command("fulfill")
@click.option("--request", "request_path", required=True, type=click.Path(dir_okay=False, path_type=str))
@click.option("--decision", required=True, type=click.Choice(["approve", "reject"]))
@click.option("--operator", required=True, help="Operator identity recording the commercial decision.")
@click.option("--decision-reference", required=True, help="CRM, ticket, or approval reference for the decision.")
@click.option("--out", "output_dir", required=True, type=click.Path(file_okay=False, path_type=str))
@click.option("--notes", default=None, help="Optional non-secret decision notes.")
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def activation_fulfill(
    request_path: str,
    decision: str,
    operator: str,
    decision_reference: str,
    output_dir: str,
    notes: str | None,
    output_format: str,
) -> None:
    result = write_fulfillment(
        request_path,
        output_dir,
        decision=decision,
        operator=operator,
        decision_reference=decision_reference,
        notes=notes,
    )
    if output_format == "json":
        console.print_json(json.dumps(result.to_dict(), indent=2))
        return

    style = "success" if decision == "approve" else "warning"
    verb = "approved" if decision == "approve" else "rejected"
    console.print(f"[{style}]Enterprise activation request {verb}.[/{style}]")
    console.print(f"Decision ID: [code]{result.decision.decision_id}[/code]")
    console.print(f"Decision record: [code]{result.decision_path}[/code]")
    if result.receipt is not None and result.receipt_path is not None:
        console.print(f"Activation receipt: [code]{result.receipt_path}[/code]")
    console.print("[accent]Offline evidence only; no payment, license signing, or tenant provisioning occurred.[/accent]")


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


@activation_group.command("package")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--out", "output_dir", required=True, type=click.Path(file_okay=False, path_type=str))
@click.option(
    "--allow-blocked",
    is_flag=True,
    help="Write a blocked package with failed checks for support triage.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def activation_package(config_path: str, output_dir: str, allow_blocked: bool, output_format: str) -> None:
    dm = DataMuru(config_path=config_path)
    package = dm.enterprise_activation_handoff_package(output_dir)
    if not package.ready and not allow_blocked:
        if output_format == "json":
            console.print_json(json.dumps(package.to_dict(), indent=2))
        else:
            console.print("[error]Activation handoff package not written because activation is blocked.[/error]")
            console.print("[accent]Use --allow-blocked only when support asked for a blocked package.[/accent]")
        raise SystemExit(1)

    written = dm.write_enterprise_activation_handoff_package(output_dir)
    payload = {
        "path": str(output_dir),
        "ready": written.ready,
        "status": written.status,
        "artifacts": [artifact.to_dict() for artifact in written.artifacts],
    }
    if output_format == "json":
        console.print_json(json.dumps(payload, indent=2))
        return

    style = "success" if written.ready else "warning"
    console.print(f"[{style}]Activation handoff package written:[/{style}] [code]{output_dir}[/code]")
    console.print(f"Artifacts: [code]{len(written.artifacts) + 1}[/code]")
    if not written.ready:
        console.print("[warning]Package includes blocked checks for support triage.[/warning]")
