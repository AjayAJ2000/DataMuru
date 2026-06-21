from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import Field

from datamuru.modeling import DataMuruModel

if TYPE_CHECKING:
    from datamuru.core.config.models import LoadedProject


class ArchitectureComponent(DataMuruModel):
    name: str
    owner: str
    responsibility: str
    implementation: str
    boundary: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class ArchitectureDecision(DataMuruModel):
    id: str
    decision: str
    rationale: str
    status: str = "accepted"

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class ArchitectureWorkItem(DataMuruModel):
    id: str
    title: str
    phase: str
    risk: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class HostedControlPlaneArchitecture(DataMuruModel):
    schema_version: str
    generated_at: str
    project: str
    provider: str
    default_environment: str
    status: str
    objective: str
    principles: list[str] = Field(default_factory=list)
    components: list[ArchitectureComponent] = Field(default_factory=list)
    data_flows: list[dict[str, str]] = Field(default_factory=list)
    extension_points: list[dict[str, str]] = Field(default_factory=list)
    trust_boundaries: list[str] = Field(default_factory=list)
    decisions: list[ArchitectureDecision] = Field(default_factory=list)
    implementation_backlog: list[ArchitectureWorkItem] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "project": self.project,
            "provider": self.provider,
            "default_environment": self.default_environment,
            "status": self.status,
            "objective": self.objective,
            "principles": list(self.principles),
            "components": [component.to_dict() for component in self.components],
            "data_flows": list(self.data_flows),
            "extension_points": list(self.extension_points),
            "trust_boundaries": list(self.trust_boundaries),
            "decisions": [decision.to_dict() for decision in self.decisions],
            "implementation_backlog": [item.to_dict() for item in self.implementation_backlog],
            "non_goals": list(self.non_goals),
        }


def build_hosted_control_plane_architecture(
    project: LoadedProject,
    *,
    generated_at: datetime | None = None,
) -> HostedControlPlaneArchitecture:
    timestamp = (generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    return HostedControlPlaneArchitecture(
        schema_version="datamuru.hosted_control_plane_architecture.v1",
        generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        project=project.root.project.name,
        provider=project.root.provider.name,
        default_environment=project.root.default_environment,
        status="reference-architecture",
        objective=(
            "Define the hosted Enterprise control plane boundary while keeping OSS execution, "
            "provider adapters, and local contracts reusable."
        ),
        principles=[
            "OSS remains the source of truth for local configuration validation and reviewable contracts.",
            "Hosted services orchestrate team workflows, scheduling, evidence, and shared-state extensions.",
            "Provider mutations stay behind explicit plan/apply approval and provider adapters.",
            "Secrets are referenced by environment or secret-manager handles, never embedded in contracts.",
            "Every hosted action must produce audit evidence that can be exported without customer data leakage.",
        ],
        components=_components(),
        data_flows=_data_flows(),
        extension_points=_extension_points(),
        trust_boundaries=[
            "Local operator machine to hosted control plane API",
            "Hosted control plane API to job runner queue",
            "Job runner to customer cloud provider APIs",
            "Hosted state extension to durable state backend",
            "Secret manager handle to runtime secret material",
            "Audit evidence store to exported support artifacts",
        ],
        decisions=_decisions(),
        implementation_backlog=_implementation_backlog(),
        non_goals=[
            "Do not embed a web server in the OSS CLI package.",
            "Do not store license keys, provider tokens, or private keys in project YAML.",
            "Do not make remote state writes from OSS until a backend extension owns locking and concurrency.",
            "Do not bypass plan review for hosted apply workflows.",
        ],
    )


def write_hosted_control_plane_architecture(
    architecture: HostedControlPlaneArchitecture,
    output_path: str | Path,
) -> Path:
    resolved = Path(output_path).resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(architecture.to_dict(), indent=2) + "\n", encoding="utf-8")
    return resolved


def _components() -> list[ArchitectureComponent]:
    return [
        ArchitectureComponent(
            name="oss_cli_and_python_api",
            owner="OSS package",
            responsibility="Validate configuration, build plans, generate contracts, and run local workflows.",
            implementation="existing",
            boundary="local",
        ),
        ArchitectureComponent(
            name="hosted_control_plane_api",
            owner="Enterprise service",
            responsibility="Accept activation contracts, manage tenants, schedule jobs, and expose team workflows.",
            implementation="planned",
            boundary="hosted",
        ),
        ArchitectureComponent(
            name="job_runner",
            owner="Enterprise service",
            responsibility="Execute approved import, plan, evidence, and apply jobs with tenant-scoped credentials.",
            implementation="planned",
            boundary="hosted-runtime",
        ),
        ArchitectureComponent(
            name="state_extension",
            owner="Enterprise extension",
            responsibility="Provide shared state locking, concurrency control, and remote backend adapters.",
            implementation="planned",
            boundary="extension",
        ),
        ArchitectureComponent(
            name="secret_source",
            owner="Customer or hosted secret manager",
            responsibility="Resolve license keys and provider credentials without writing secret values to contracts.",
            implementation="planned",
            boundary="secret",
        ),
        ArchitectureComponent(
            name="audit_evidence_store",
            owner="Enterprise service",
            responsibility="Persist activation, plan, apply, import, and support evidence with redaction metadata.",
            implementation="planned",
            boundary="hosted",
        ),
    ]


def _data_flows() -> list[dict[str, str]]:
    return [
        {
            "name": "activation_handoff",
            "source": "OSS CLI",
            "target": "Hosted control plane API",
            "payload": "enterprise activation bundle, control-plane contract, activation evidence",
        },
        {
            "name": "scheduled_import",
            "source": "Hosted scheduler",
            "target": "Job runner",
            "payload": "tenant, workspace scope, grant budgets, checkpoint location",
        },
        {
            "name": "approved_apply",
            "source": "Review workflow",
            "target": "Provider adapter",
            "payload": "saved plan, approval metadata, provider credential handle",
        },
        {
            "name": "evidence_export",
            "source": "Audit evidence store",
            "target": "Operator or support workflow",
            "payload": "redacted evidence report with mutation and secret-handling metadata",
        },
    ]


def _extension_points() -> list[dict[str, str]]:
    return [
        {
            "name": "state_backend",
            "contract": "state.backend local|s3|azure_blob|gcs plus extension-owned locking semantics",
        },
        {
            "name": "identity_provider",
            "contract": "tenant users, groups, service principals, and approval roles",
        },
        {
            "name": "secret_manager",
            "contract": "environment variable or secret-handle references only",
        },
        {
            "name": "provider_adapter",
            "contract": "DataMuru provider interface for observe, plan resources, doctor, and apply",
        },
        {
            "name": "audit_sink",
            "contract": "redacted evidence records and exportable JSON reports",
        },
    ]


def _decisions() -> list[ArchitectureDecision]:
    return [
        ArchitectureDecision(
            id="HCP-001",
            decision="Keep OSS CLI local-first and contract-producing.",
            rationale="The package remains useful without hosted infrastructure and avoids accidental SaaS coupling.",
        ),
        ArchitectureDecision(
            id="HCP-002",
            decision="Treat remote state as an Enterprise extension boundary before implementation.",
            rationale="Shared state requires locking, concurrency, secret handling, and operational support.",
        ),
        ArchitectureDecision(
            id="HCP-003",
            decision="Use redacted JSON contracts for activation and evidence handoff.",
            rationale="Support, security, and implementation teams need stable artifacts without secret leakage.",
        ),
        ArchitectureDecision(
            id="HCP-004",
            decision="Separate hosted orchestration from provider mutation.",
            rationale="Plan review and provider adapters remain the safety boundary for live infrastructure changes.",
        ),
    ]


def _implementation_backlog() -> list[ArchitectureWorkItem]:
    return [
        ArchitectureWorkItem(
            id="HCP-B1",
            title="Tenant and entitlement registry",
            phase="activation",
            risk="high",
            description="Bind organization, tenant id, deployment region, support plan, and license entitlement.",
        ),
        ArchitectureWorkItem(
            id="HCP-B2",
            title="Hosted job runner queue",
            phase="execution",
            risk="high",
            description="Run import, plan, evidence, and apply jobs with checkpoints and tenant-scoped credentials.",
        ),
        ArchitectureWorkItem(
            id="HCP-B3",
            title="Remote state extension",
            phase="state",
            risk="high",
            description="Implement shared state adapters, locking, and conflict handling for hosted workflows.",
        ),
        ArchitectureWorkItem(
            id="HCP-B4",
            title="Audit evidence store",
            phase="audit",
            risk="medium",
            description="Persist redacted evidence for activation, imports, plans, applies, and support exports.",
        ),
        ArchitectureWorkItem(
            id="HCP-B5",
            title="Team review workflow",
            phase="collaboration",
            risk="medium",
            description="Add approvals, comments, plan diffs, RBAC, and release evidence for multi-person usage.",
        ),
    ]
