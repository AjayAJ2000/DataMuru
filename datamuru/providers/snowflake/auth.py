from __future__ import annotations

import os
from typing import Any

from datamuru.modeling import DataMuruModel


class SnowflakeAuthConfig(DataMuruModel):
    account: str | None = None
    account_env: str | None = None
    auth_type: str = "externalbrowser"
    cloud: str = "snowflake"
    execution_mode: str = "state-only"
    password_env: str | None = None
    private_key_path: str | None = None
    role: str | None = None
    user: str | None = None
    user_env: str | None = None
    warehouse: str | None = None

    @classmethod
    def from_provider_data(cls, provider_data: dict[str, Any]) -> "SnowflakeAuthConfig":
        return cls.model_validate(provider_data.get("provider", {}))

    def resolve_account(self) -> str | None:
        if self.account:
            return self.account
        if self.account_env:
            return os.getenv(self.account_env)
        return None

    def resolve_user(self) -> str | None:
        if self.user:
            return self.user
        if self.user_env:
            return os.getenv(self.user_env)
        return None

    def allows_live_mutation(self) -> bool:
        return self.execution_mode == "live-apply"

    def should_probe_connectivity(self) -> bool:
        return self.execution_mode in {"live-readonly", "live-apply"}
