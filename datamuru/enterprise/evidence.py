from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from datamuru.enterprise.activation import ActivationReport, build_activation_report
from datamuru.enterprise.control_plane import ControlPlaneContract, build_control_plane_contract
from datamuru.modeling import DataMuruModel

if TYPE_CHECKING:
    from datamuru.core.config.models import LoadedProject


class EvidenceArtifact(DataMuruModel):
    name: str
    status: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class ActivationEvidenceReport(DataMuruModel):
    schema_version: str
    generated_at: str
    status: str
    project: str
    provider: str
    default_environment: str
    activation: ActivationReport
    control_plane: ControlPlaneContract
    artifacts: list[EvidenceArtifact] = Field(default_factory=list)
    audit: dict[str, Any]

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "ready": self.ready,
            "project": self.project,
            "provider": self.provider,
            "default_environment": self.default_environment,
            "activation": self.activation.to_dict(),
            "control_plane": self.control_plane.to_dict(),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "audit": self.audit,
        }


def build_activation_evidence_report(
    project: LoadedProject,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> ActivationEvidenceReport:
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    activation = build_activation_report(project, environ=environ)
    control_plane = build_control_plane_contract(project, environ=environ, generated_at=timestamp)
    status = "ready" if activation.ready and control_plane.ready else "blocked"
    return ActivationEvidenceReport(
        schema_version="datamuru.enterprise_activation_evidence.v1",
        generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        status=status,
        project=project.root.project.name,
        provider=project.root.provider.name,
        default_environment=project.root.default_environment,
        activation=activation,
        control_plane=control_plane,
        artifacts=_build_artifacts(activation, control_plane),
        audit=_build_audit(project, activation, control_plane),
    )


def write_activation_evidence_report(
    report: ActivationEvidenceReport,
    output_path: str | Path,
) -> Path:
    resolved = Path(output_path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return resolved


def _build_artifacts(
    activation: ActivationReport,
    control_plane: ControlPlaneContract,
) -> list[EvidenceArtifact]:
    return [
        EvidenceArtifact(
            name="activation_readiness",
            status="ready" if activation.ready else "blocked",
            description="Redacted activation readiness report for Enterprise onboarding.",
        ),
        EvidenceArtifact(
            name="hosted_control_plane_contract",
            status="ready" if control_plane.ready else "blocked",
            description="Hosted control plane handoff contract with state and feature posture.",
        ),
        EvidenceArtifact(
            name="secret_redaction",
            status="ready",
            description="License key values are omitted; only license_key_env and license_key_present are recorded.",
        ),
        EvidenceArtifact(
            name="operator_follow_up",
            status="required",
            description="Commercial entitlement, tenant binding, secret source, and shared state choices remain follow-up actions.",
        ),
    ]


def _build_audit(
    project: LoadedProject,
    activation: ActivationReport,
    control_plane: ControlPlaneContract,
) -> dict[str, Any]:
    return {
        "scope": "enterprise_activation_handoff",
        "offline": True,
        "mutates_provider": False,
        "mutates_state": False,
        "secret_values_included": False,
        "project_root": str(project.root_path),
        "config_path": str(project.config_path),
        "activation_check_count": len(activation.checks),
        "control_plane_check_count": len(control_plane.checks),
        "required_follow_up": list(control_plane.required_follow_up),
    }
