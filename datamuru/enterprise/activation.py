from __future__ import annotations

from collections.abc import Mapping
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
