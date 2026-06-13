from __future__ import annotations

import os
from typing import Any

from datamuru.errors import ProviderError
from datamuru.modeling import DataMuruModel


class DatabricksAuthConfig(DataMuruModel):
    account_id: str | None = None
    auth_type: str = "pat"
    cloud: str
    connect_timeout_seconds: int = 10
    credential_mode: str | None = None
    execution_mode: str = "state-only"
    host: str
    sql_warehouse_id: str | None = None
    sql_warehouse_id_env: str | None = None
    token_env: str | None = None

    @classmethod
    def from_provider_data(cls, provider_data: dict[str, Any]) -> "DatabricksAuthConfig":
        provider = provider_data.get("provider", {})
        return cls.model_validate(provider)

    def resolve_token(self) -> str | None:
        if not self.token_env:
            return None
        return os.getenv(self.token_env)

    def has_pat(self) -> bool:
        return bool(self.auth_type == "pat" and self.resolve_token())

    def resolve_sql_warehouse_id(self) -> str | None:
        if self.sql_warehouse_id:
            return self.sql_warehouse_id
        if self.sql_warehouse_id_env:
            return os.getenv(self.sql_warehouse_id_env)
        return None

    def supports_live_connectivity(self) -> bool:
        if self.auth_type == "pat":
            return self.has_pat()
        return self.auth_type in {"databricks-cli", "oauth", "azure-managed-identity"}

    def allows_live_mutation(self) -> bool:
        return self.execution_mode == "live-apply"

    def requires_readonly_guard(self) -> bool:
        return self.execution_mode == "live-readonly"

    def should_probe_connectivity(self) -> bool:
        return self.execution_mode in {"live-readonly", "live-apply"}

    def workspace_headers(self) -> dict[str, str]:
        token = self.resolve_token()
        if self.auth_type != "pat" or not token:
            raise ProviderError(
                description="PAT-based workspace headers were requested without an available PAT token.",
                context={"auth_type": self.auth_type, "token_env": self.token_env},
                suggestion="Set the configured token environment variable or switch to a supported auth mode.",
            )
        return {"Authorization": f"Bearer {token}"}
