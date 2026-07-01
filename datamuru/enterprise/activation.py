from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from datamuru.core.config.models import LoadedProject
from datamuru.modeling import DataMuruModel


REQUIRED_ACTIVATION_FIELDS = (
    "organization",
    "contact_email",
    "control_plane_url",
    "tenant_id",
    "deployment_region",
    "license_key_env",
)

LICENSE_SECRET_HANDLING = (
    "The license key value is intentionally omitted. The receiving workflow must "
    "resolve the named environment variable or request the secret through an approved "
    "secret manager."
)


class ActivationCheck(DataMuruModel):
    level: str
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class ActivationReport(DataMuruModel):
    project: str
    edition: str
    provider: str
    default_environment: str
    ready: bool
    payload: dict[str, Any]
    checks: list[ActivationCheck]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "edition": self.edition,
            "provider": self.provider,
            "default_environment": self.default_environment,
            "ready": self.ready,
            "payload": self.payload,
            "checks": [check.to_dict() for check in self.checks],
        }


class ActivationBundle(DataMuruModel):
    schema_version: str
    generated_at: str
    status: str
    report: ActivationReport
    onboarding: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "report": self.report.to_dict(),
            "onboarding": self.onboarding,
        }


class ActivationPurchaseRequest(DataMuruModel):
    schema_version: str
    generated_at: str
    status: str
    report: ActivationReport
    commercial: dict[str, Any]
    fulfillment: dict[str, Any]
    license: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "report": self.report.to_dict(),
            "commercial": self.commercial,
            "fulfillment": self.fulfillment,
            "license": self.license,
        }


def build_activation_report(
    project: LoadedProject,
    *,
    environ: Mapping[str, str] | None = None,
) -> ActivationReport:
    environment = environ or {}
    activation = _activation_config(project)
    checks = _build_checks(project, activation, environment)
    payload = _build_payload(project, activation, environment)

    return ActivationReport(
        project=project.root.project.name,
        edition=project.root.project.edition,
        provider=project.root.provider.name,
        default_environment=project.root.default_environment,
        ready=not any(check.level == "error" for check in checks),
        payload=payload,
        checks=checks,
    )


def build_activation_bundle(
    report: ActivationReport,
    *,
    generated_at: datetime | None = None,
) -> ActivationBundle:
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    return ActivationBundle(
        schema_version="datamuru.enterprise_activation_bundle.v1",
        generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        status="ready" if report.ready else "blocked",
        report=report,
        onboarding={
            "handoff": "Share this file with the Enterprise onboarding or control plane provisioning workflow.",
            "secret_handling": (
                "The license key value is intentionally omitted. The receiving workflow must read the named "
                "environment variable or request the secret through an approved secret manager."
            ),
            "required_follow_up": [
                "confirm commercial entitlement",
                "provision or verify tenant",
                "bind tenant to control plane URL",
                "record activation evidence",
            ],
        },
    )


def build_activation_purchase_request(
    report: ActivationReport,
    *,
    generated_at: datetime | None = None,
) -> ActivationPurchaseRequest:
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    activation = report.payload.get("activation", {})
    features = report.payload.get("features", {})
    return ActivationPurchaseRequest(
        schema_version="datamuru.enterprise_purchase_request.v1",
        generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        status="ready" if report.ready else "blocked",
        report=report,
        commercial={
            "organization": activation.get("organization"),
            "contact_email": activation.get("contact_email"),
            "purchase_reference": activation.get("purchase_reference"),
            "support_plan": activation.get("support_plan"),
            "requested_entitlements": [
                name
                for name in [
                    "hosted_control_plane",
                    "identity_management",
                    "multi_workspace",
                    "compliance_reporting",
                ]
                if features.get(name)
            ],
        },
        fulfillment={
            "tenant_id": activation.get("tenant_id"),
            "deployment_region": activation.get("deployment_region"),
            "control_plane_url": activation.get("control_plane_url"),
            "required_actions": [
                "confirm commercial entitlement",
                "issue or validate enterprise license",
                "provision hosted control plane tenant",
                "bind tenant to control plane URL",
                "record activation evidence",
            ],
            "offline": True,
            "provisions_tenant": False,
            "calls_license_server": False,
        },
        license={
            "license_key_env": activation.get("license_key_env"),
            "license_key_present": activation.get("license_key_present", False),
            "secret_values_included": False,
            "secret_handling": LICENSE_SECRET_HANDLING,
        },
    )


def write_activation_purchase_request(
    report: ActivationReport,
    output_path: str | Path,
    *,
    generated_at: datetime | None = None,
) -> Path:
    request = build_activation_purchase_request(report, generated_at=generated_at)
    resolved = Path(output_path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(request.to_dict(), indent=2) + "\n", encoding="utf-8")
    return resolved


def write_activation_bundle(
    report: ActivationReport,
    output_path: str | Path,
    *,
    generated_at: datetime | None = None,
) -> Path:
    bundle = build_activation_bundle(report, generated_at=generated_at)
    resolved = Path(output_path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n", encoding="utf-8")
    return resolved


def _activation_config(project: LoadedProject) -> dict[str, Any]:
    enterprise = project.root.enterprise or {}
    activation = enterprise.get("activation", {})
    return activation if isinstance(activation, dict) else {}


def _build_checks(
    project: LoadedProject,
    activation: dict[str, Any],
    environment: Mapping[str, str],
) -> list[ActivationCheck]:
    checks: list[ActivationCheck] = []
    if project.root.project.edition != "enterprise":
        checks.append(
            ActivationCheck(
                level="error",
                code="activation.edition",
                path="project.edition",
                message="Enterprise activation requires project.edition: enterprise.",
            )
        )

    if not project.root.features.hosted_control_plane:
        checks.append(
            ActivationCheck(
                level="error",
                code="activation.hosted_control_plane",
                path="features.hosted_control_plane",
                message="Hosted control plane activation requires features.hosted_control_plane: true.",
            )
        )

    if "activation" not in (project.root.enterprise or {}):
        checks.append(
            ActivationCheck(
                level="error",
                code="activation.config_missing",
                path="enterprise.activation",
                message="Add enterprise.activation fields before requesting Enterprise activation.",
            )
        )

    for field_name in REQUIRED_ACTIVATION_FIELDS:
        value = activation.get(field_name)
        if not isinstance(value, str) or not value.strip():
            checks.append(
                ActivationCheck(
                    level="error",
                    code=f"activation.{field_name}.required",
                    path=f"enterprise.activation.{field_name}",
                    message=f"Enterprise activation requires {field_name}.",
                )
            )

    contact_email = activation.get("contact_email")
    if isinstance(contact_email, str) and contact_email.strip() and "@" not in contact_email:
        checks.append(
            ActivationCheck(
                level="error",
                code="activation.contact_email.invalid",
                path="enterprise.activation.contact_email",
                message="Activation contact_email must be an email address.",
            )
        )

    license_key_env = activation.get("license_key_env")
    if isinstance(license_key_env, str) and license_key_env.strip():
        if not environment.get(license_key_env):
            checks.append(
                ActivationCheck(
                    level="error",
                    code="activation.license_key_env.missing",
                    path="enterprise.activation.license_key_env",
                    message=f"License key environment variable {license_key_env} is not set.",
                )
            )

    return checks


def _build_payload(
    project: LoadedProject,
    activation: dict[str, Any],
    environment: Mapping[str, str],
) -> dict[str, Any]:
    license_key_env = activation.get("license_key_env")
    license_key_present = bool(
        isinstance(license_key_env, str) and license_key_env.strip() and environment.get(license_key_env)
    )
    return {
        "schema_version": "datamuru.enterprise_activation.v1",
        "project": {
            "name": project.root.project.name,
            "version": project.root.project.version,
            "provider": project.root.provider.name,
            "default_environment": project.root.default_environment,
        },
        "activation": {
            "organization": activation.get("organization"),
            "contact_email": activation.get("contact_email"),
            "control_plane_url": activation.get("control_plane_url"),
            "tenant_id": activation.get("tenant_id"),
            "deployment_region": activation.get("deployment_region"),
            "purchase_reference": activation.get("purchase_reference"),
            "support_plan": activation.get("support_plan"),
            "license_key_env": license_key_env,
            "license_key_present": license_key_present,
        },
        "features": {
            "hosted_control_plane": project.root.features.hosted_control_plane,
            "identity_management": project.root.features.identity_management,
            "multi_workspace": project.root.features.multi_workspace,
            "compliance_reporting": project.root.features.compliance_reporting,
        },
    }
