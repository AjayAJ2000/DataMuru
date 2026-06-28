from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from datamuru.modeling import DataMuruModel


def normalize_snowflake_host(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    candidate = value.strip()
    parsed = urlparse(candidate if "://" in candidate else f"//{candidate}")
    hostname = parsed.hostname
    if not hostname:
        return None
    hostname = hostname.rstrip(".").lower()
    if not hostname.endswith(".snowflakecomputing.com"):
        return None
    return hostname


class SnowflakeAuthConfig(DataMuruModel):
    account: str | None = None
    account_env: str | None = None
    auth_type: str = "externalbrowser"
    cloud: str = "snowflake"
    execution_mode: str = "state-only"
    host: str | None = None
    host_env: str | None = None
    password_env: str | None = None
    private_key_path: str | None = None
    role: str | None = None
    token_env: str | None = None
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
            account = os.getenv(self.account_env)
            if account:
                return account
        host = self.resolve_host()
        return host.split(".", 1)[0] if host else None

    def resolve_host(self) -> str | None:
        value = self.host
        if not value and self.host_env:
            value = os.getenv(self.host_env)
        return normalize_snowflake_host(value)

    def resolve_user(self) -> str | None:
        if self.user:
            return self.user
        if self.user_env:
            return os.getenv(self.user_env)
        return None

    def resolve_password(self) -> str | None:
        if self.password_env:
            return os.getenv(self.password_env)
        return None

    def resolve_token(self) -> str | None:
        if self.token_env:
            return os.getenv(self.token_env)
        return None

    def uses_programmatic_access_token(self) -> bool:
        return self.auth_type.casefold() == "programmatic_access_token"

    def allows_live_mutation(self) -> bool:
        return self.execution_mode == "live-apply"

    def should_probe_connectivity(self) -> bool:
        return self.execution_mode in {"live-readonly", "live-apply"}
