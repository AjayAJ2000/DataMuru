from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from datamuru.core.state.inspection import StateBackendReport, inspect_state_backend
from datamuru.enterprise.activation import ActivationReport, build_activation_report
from datamuru.modeling import DataMuruModel

if TYPE_CHECKING:
    from datamuru.core.config.models import LoadedProject


class ControlPlaneCheck(DataMuruModel):
    level: str
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class ControlPlaneContract(DataMuruModel):
    schema_version: str
    generated_at: str
    project: str
    edition: str
    provider: str
    default_environment: str
    ready: bool
    activation: ActivationReport
    state: StateBackendReport
    features: dict[str, bool]
    integration: dict[str, Any]
    boundaries: list[str] = Field(default_factory=list)
    required_follow_up: list[str] = Field(default_factory=list)
    checks: list[ControlPlaneCheck] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project": self.project,
            "edition": self.edition,
            "provider": self.provider,
            "default_environment": self.default_environment,
            "ready": self.ready,
            "activation": self.activation.to_dict(),
            "state": self.state.to_dict(),
            "features": self.features,
            "integration": self.integration,
            "boundaries": list(self.boundaries),
            "required_follow_up": list(self.required_follow_up),
            "checks": [check.to_dict() for check in self.checks],
        }


def build_control_plane_contract(
    project: LoadedProject,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> ControlPlaneContract:
    activation = build_activation_report(project, environ=environ)
    state = inspect_state_backend(project)
    checks = _build_checks(project, activation, state)
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    features = project.root.features.model_dump(mode="python")
    return ControlPlaneContract(
        schema_version="datamuru.hosted_control_plane_contract.v1",
        generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        project=project.root.project.name,
        edition=project.root.project.edition,
        provider=project.root.provider.name,
        default_environment=project.root.default_environment,
        ready=not any(check.level == "error" for check in checks),
        activation=activation,
        state=state,
        features=features,
        integration=_build_integration(project, activation, state),
        boundaries=_build_boundaries(state),
        required_follow_up=[
            "confirm commercial entitlement",
            "provision hosted tenant and environment binding",
            "attach approved secret manager or license key source",
            "select hosted state extension for multi-user execution",
            "capture activation and audit evidence",
        ],
        checks=checks,
    )


def write_control_plane_contract(
    contract: ControlPlaneContract,
    output_path: str | Path,
) -> Path:
    resolved = Path(output_path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(contract.to_dict(), indent=2) + "\n", encoding="utf-8")
    return resolved


def _build_checks(
    project: LoadedProject,
    activation: ActivationReport,
    state: StateBackendReport,
) -> list[ControlPlaneCheck]:
    checks = [
        ControlPlaneCheck(
            level=check.level,
            code=f"control_plane.{check.code}",
            path=check.path,
            message=check.message,
        )
        for check in activation.checks
    ]

    if state.mode == "unsupported":
        checks.append(
            ControlPlaneCheck(
                level="error",
                code="control_plane.state.unsupported",
                path="state.backend",
                message="Hosted control plane handoff requires a local or recognized remote state backend contract.",
            )
        )
    elif state.remote:
        checks.append(
            ControlPlaneCheck(
                level="warning",
                code="control_plane.state.remote_extension_required",
                path="state.backend",
                message="Remote state is a hosted contract; OSS will not read or write it without an extension.",
            )
        )
    else:
        checks.append(
            ControlPlaneCheck(
                level="warning",
                code="control_plane.state.local_single_user",
                path="state.backend",
                message="Local state is suitable for OSS workflows; hosted multi-user execution must choose a shared state extension.",
            )
        )

    if not project.root.features.identity_management:
        checks.append(
            ControlPlaneCheck(
                level="warning",
                code="control_plane.identity_management.recommended",
                path="features.identity_management",
                message="Hosted Enterprise onboarding should normally enable identity_management for tenant access controls.",
            )
        )

    if not project.root.features.multi_workspace:
        checks.append(
            ControlPlaneCheck(
                level="warning",
                code="control_plane.multi_workspace.optional",
                path="features.multi_workspace",
                message="Enable multi_workspace when the tenant must coordinate more than one workspace.",
            )
        )

    return checks


def _build_integration(
    project: LoadedProject,
    activation: ActivationReport,
    state: StateBackendReport,
) -> dict[str, Any]:
    activation_payload = activation.payload.get("activation", {})
    return {
        "control_plane_url": activation_payload.get("control_plane_url"),
        "tenant_id": activation_payload.get("tenant_id"),
        "deployment_region": activation_payload.get("deployment_region"),
        "license_key_env": activation_payload.get("license_key_env"),
        "license_key_present": activation_payload.get("license_key_present", False),
        "state_backend": {
            "backend": state.backend,
            "mode": state.mode,
            "remote": state.remote,
            "runtime_supported": state.runtime_supported,
        },
        "project_config": {
            "config_path": str(project.config_path),
            "root_path": str(project.root_path),
            "provider_config": project.root.provider.config,
            "environment_count": len(project.root.environments),
            "workspace_count": len(project.workspaces),
        },
    }


def _build_boundaries(state: StateBackendReport) -> list[str]:
    boundaries = [
        "OSS builds and validates this contract offline.",
        "OSS does not provision hosted tenants, licenses, or billing entitlements.",
        "The license key value is never included in the contract.",
    ]
    if state.remote:
        boundaries.append("Remote state backends are recognized as contracts, not implemented OSS runtime storage.")
    else:
        boundaries.append("Local state remains single-operator storage until a hosted state extension is configured.")
    return boundaries
