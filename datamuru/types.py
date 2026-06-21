from __future__ import annotations

from typing import Any

from pydantic import Field

from datamuru.modeling import DataMuruModel


class ValidationIssue(DataMuruModel):
    level: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class DoctorCheck(DataMuruModel):
    level: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return self.model_dump(mode="python")


class DoctorReport(DataMuruModel):
    provider: str
    environment: str
    checks: list[DoctorCheck] = Field(default_factory=list)

    @property
    def success(self) -> bool:
        return not any(check.level == "error" for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "environment": self.environment,
            "success": self.success,
            "checks": [check.to_dict() for check in self.checks],
        }


class EditionSummary(DataMuruModel):
    edition: str
    enabled_features: list[str]
    restricted_features: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")


# Import compatibility contracts after the legacy declarations above to avoid a
# circular import while preserving the public datamuru.types surface.
from datamuru.core.apply.models import ApplyFailure, ApplyResult
from datamuru.core.plan.models import Plan, PlanChange, ResourceDescriptor
from datamuru.core.plan.saved import SavedPlanDocument, SavedPlanMetadata
from datamuru.core.state.inspection import StateBackendCheck, StateBackendReport
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.enterprise.activation import ActivationBundle, ActivationCheck, ActivationReport
from datamuru.enterprise.control_plane import ControlPlaneCheck, ControlPlaneContract
from datamuru.enterprise.evidence import ActivationEvidenceReport, EvidenceArtifact

__all__ = [
    "ActivationBundle",
    "ActivationCheck",
    "ActivationEvidenceReport",
    "ActivationReport",
    "ApplyFailure",
    "ApplyResult",
    "DataMuruModel",
    "DoctorCheck",
    "DoctorReport",
    "ControlPlaneCheck",
    "ControlPlaneContract",
    "EditionSummary",
    "EvidenceArtifact",
    "Plan",
    "PlanChange",
    "ResourceDescriptor",
    "SavedPlanDocument",
    "SavedPlanMetadata",
    "StateBackendCheck",
    "StateBackendReport",
    "StateResourceRecord",
    "StateSnapshot",
    "ValidationIssue",
]
