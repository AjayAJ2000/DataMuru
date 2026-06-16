from __future__ import annotations

from datamuru.errors import ProviderError, UnsupportedOperationError
from datamuru.types import ResourceDescriptor

from .auth import DatabricksAuthConfig


class DatabricksExecutionPolicy:
    LIVE_APPLY_SUPPORTED_RESOURCE_TYPES = {
        "catalog",
        "schema",
        "permission_binding",
        "user",
        "group",
        "service_principal",
        "group_membership",
    }
    LOCAL_ONLY_RESOURCE_TYPES = {"workspace", "taxonomy", "classification", "rbac_role", "column_mask"}

    def __init__(self, auth: DatabricksAuthConfig) -> None:
        self.auth = auth

    def guard_mutation(self, resource: ResourceDescriptor) -> None:
        if self.auth.requires_readonly_guard():
            raise ProviderError(
                description="Live-readonly execution mode blocks Databricks mutations.",
                context={"execution_mode": self.auth.execution_mode, "resource": resource.address},
                suggestion=(
                    "Use live-readonly for planning only. Switch execution_mode to live-apply after reviewing the "
                    "plan and confirming the target workspace."
                ),
            )
        if self.auth.allows_live_mutation() and resource.resource_type not in (
            self.LIVE_APPLY_SUPPORTED_RESOURCE_TYPES | self.LOCAL_ONLY_RESOURCE_TYPES
        ):
            raise UnsupportedOperationError(
                description="Live Databricks mutations are not implemented for this alpha provider yet.",
                context={"execution_mode": self.auth.execution_mode, "resource": resource.address},
                suggestion="Use state-only mode for now. Live mutations are a follow-up milestone.",
            )
