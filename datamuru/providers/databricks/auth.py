from __future__ import annotations

import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any

from pydantic import model_validator

from datamuru.errors import ProviderError
from datamuru.modeling import DataMuruModel


class DatabricksAuthConfig(DataMuruModel):
    account_id: str | None = None
    auth_type: str = "pat"
    cloud: str
    connect_timeout_seconds: int = 10
    credential_mode: str | None = None
    execution_mode: str = "state-only"
    host: str = ""
    host_env: str | None = None
    profile: str | None = None
    config_file: str | None = None
    sql_warehouse_id: str | None = None
    sql_warehouse_id_env: str | None = None
    token_env: str | None = None

    @classmethod
    def from_provider_data(cls, provider_data: dict[str, Any]) -> "DatabricksAuthConfig":
        provider = provider_data.get("provider", {})
        return cls.model_validate(provider)

    @model_validator(mode="after")
    def resolve_host_from_environment_or_profile(self) -> "DatabricksAuthConfig":
        if self.host_env and (not self.host or "your-workspace" in self.host):
            env_host = os.getenv(self.host_env)
            if env_host:
                self.host = env_host
        profile = self.resolve_cli_profile()
        if profile and (not self.host or "your-workspace" in self.host):
            profile_host = profile.get("host")
            if profile_host:
                self.host = profile_host
        return self

    def resolve_token(self) -> str | None:
        if self.token_env:
            token = os.getenv(self.token_env)
            if token:
                return token
        profile = self.resolve_cli_profile()
        if profile:
            return profile.get("token") or profile.get("access_token")
        return None

    def resolve_cli_profile(self) -> dict[str, str]:
        if self.auth_type != "databricks-cli" and not self.profile:
            return {}
        profile_name = self.profile or os.getenv("DATABRICKS_CONFIG_PROFILE") or "DEFAULT"
        config_path = Path(
            self.config_file
            or os.getenv("DATABRICKS_CONFIG_FILE", "")
            or Path.home() / ".databrickscfg"
        ).expanduser()
        if not config_path.exists():
            return {}
        parser = ConfigParser()
        parser.read(config_path, encoding="utf-8")
        if not parser.has_section(profile_name):
            return {}
        return {key: value for key, value in parser.items(profile_name)}

    def has_pat(self) -> bool:
        return bool(self.auth_type == "pat" and self.resolve_token())

    def resolve_sql_warehouse_id(self) -> str | None:
        if self.sql_warehouse_id:
            return self.sql_warehouse_id
        if self.sql_warehouse_id_env:
            return os.getenv(self.sql_warehouse_id_env)
        return None

    def supports_live_connectivity(self) -> bool:
        if self.auth_type in {"pat", "databricks-cli", "oauth"}:
            return bool(self.resolve_token())
        return self.auth_type == "azure-managed-identity"

    def allows_live_mutation(self) -> bool:
        return self.execution_mode == "live-apply"

    def requires_readonly_guard(self) -> bool:
        return self.execution_mode == "live-readonly"

    def should_probe_connectivity(self) -> bool:
        return self.execution_mode in {"live-readonly", "live-apply"}

    def workspace_headers(self) -> dict[str, str]:
        token = self.resolve_token()
        if self.auth_type in {"pat", "databricks-cli", "oauth"} and token:
            return {"Authorization": f"Bearer {token}"}
        if not token:
            raise ProviderError(
                description="Databricks workspace headers were requested without an available bearer token.",
                context={"auth_type": self.auth_type, "token_env": self.token_env},
                suggestion=(
                    "Set the configured token environment variable, configure a Databricks CLI profile with a token, "
                    "or use a supported enterprise auth extension."
                ),
            )
        return {"Authorization": f"Bearer {token}"}
