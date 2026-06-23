from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from datamuru.enterprise.activation import (
    build_activation_bundle,
    build_activation_purchase_request,
    build_activation_report,
)
from datamuru.enterprise.architecture import build_hosted_control_plane_architecture
from datamuru.enterprise.control_plane import build_control_plane_contract
from datamuru.enterprise.evidence import build_activation_evidence_report
from datamuru.modeling import DataMuruModel

if TYPE_CHECKING:
    from datamuru.core.config.models import LoadedProject


class ActivationHandoffArtifact(DataMuruModel):
    name: str
    path: str
    schema_version: str
    status: str
    ready: bool

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")


class ActivationHandoffPackage(DataMuruModel):
    schema_version: str
    generated_at: str
    status: str
    ready: bool
    project: str
    provider: str
    default_environment: str
    output_dir: str
    artifacts: list[ActivationHandoffArtifact] = Field(default_factory=list)
    redaction: dict[str, Any]
    follow_up: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "ready": self.ready,
            "project": self.project,
            "provider": self.provider,
            "default_environment": self.default_environment,
            "output_dir": self.output_dir,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "redaction": self.redaction,
            "follow_up": list(self.follow_up),
        }


def build_activation_handoff_package(
    project: LoadedProject,
    output_dir: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> ActivationHandoffPackage:
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    generated_at_text = timestamp.isoformat().replace("+00:00", "Z")
    activation = build_activation_report(project, environ=environ)
    evidence = build_activation_evidence_report(project, environ=environ, generated_at=timestamp)
    contract = build_control_plane_contract(project, environ=environ, generated_at=timestamp)
    architecture = build_hosted_control_plane_architecture(project, generated_at=timestamp)
    purchase_request = build_activation_purchase_request(activation, generated_at=timestamp)
    bundle = build_activation_bundle(activation, generated_at=timestamp)
    package_ready = activation.ready and evidence.ready and contract.ready
    status = "ready" if package_ready else "blocked"
    resolved = Path(output_dir).resolve()

    return ActivationHandoffPackage(
        schema_version="datamuru.enterprise_activation_handoff_package.v1",
        generated_at=generated_at_text,
        status=status,
        ready=package_ready,
        project=project.root.project.name,
        provider=project.root.provider.name,
        default_environment=project.root.default_environment,
        output_dir=str(resolved),
        artifacts=[
            _artifact("activation_bundle", "enterprise-activation.json", bundle.to_dict(), bundle.status),
            _artifact(
                "purchase_request",
                "purchase-request.json",
                purchase_request.to_dict(),
                purchase_request.status,
            ),
            _artifact("activation_evidence", "activation-evidence.json", evidence.to_dict(), evidence.status),
            _artifact(
                "control_plane_contract",
                "control-plane-contract.json",
                contract.to_dict(),
                "ready" if contract.ready else "blocked",
            ),
            _artifact(
                "control_plane_architecture",
                "control-plane-architecture.json",
                architecture.to_dict(),
                architecture.status,
                ready=True,
            ),
        ],
        redaction={
            "secret_values_included": False,
            "license_key_value_included": False,
            "provider_token_values_included": False,
            "safe_to_attach_to_onboarding_ticket": package_ready,
        },
        follow_up=[
            "review package manifest before sharing outside the operator team",
            "confirm commercial entitlement and tenant binding",
            "resolve license key through the named environment variable or approved secret manager",
            "choose hosted state extension before multi-user execution",
        ],
    )


def write_activation_handoff_package(
    project: LoadedProject,
    output_dir: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> ActivationHandoffPackage:
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    activation = build_activation_report(project, environ=environ)
    evidence = build_activation_evidence_report(project, environ=environ, generated_at=timestamp)
    contract = build_control_plane_contract(project, environ=environ, generated_at=timestamp)
    architecture = build_hosted_control_plane_architecture(project, generated_at=timestamp)
    purchase_request = build_activation_purchase_request(activation, generated_at=timestamp)
    bundle = build_activation_bundle(activation, generated_at=timestamp)
    package = build_activation_handoff_package(
        project,
        output_dir,
        environ=environ,
        generated_at=timestamp,
    )

    resolved = Path(output_dir).resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    _write_json(resolved / "enterprise-activation.json", bundle.to_dict())
    _write_json(resolved / "purchase-request.json", purchase_request.to_dict())
    _write_json(resolved / "activation-evidence.json", evidence.to_dict())
    _write_json(resolved / "control-plane-contract.json", contract.to_dict())
    _write_json(resolved / "control-plane-architecture.json", architecture.to_dict())
    _write_json(resolved / "manifest.json", package.to_dict())
    return package


def _artifact(
    name: str,
    path: str,
    payload: dict[str, Any],
    status: str,
    *,
    ready: bool | None = None,
) -> ActivationHandoffArtifact:
    return ActivationHandoffArtifact(
        name=name,
        path=path,
        schema_version=str(payload.get("schema_version", "unknown")),
        status=status,
        ready=ready if ready is not None else status in {"ready", "reference-architecture"},
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
