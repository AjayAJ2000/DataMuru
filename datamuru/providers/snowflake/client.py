from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from datamuru.errors import ProviderError

from .auth import SnowflakeAuthConfig


class SnowflakeSqlClient:
    SYSTEM_DATABASE_NAMES = {"SNOWFLAKE", "SNOWFLAKE_SAMPLE_DATA"}
    SYSTEM_SCHEMA_NAMES = {"INFORMATION_SCHEMA"}

    def __init__(self, auth: SnowflakeAuthConfig) -> None:
        self.auth = auth

    @staticmethod
    def connector_available() -> bool:
        try:
            import snowflake.connector  # noqa: F401
        except ImportError:
            return False
        return True

    def list_databases(self, *, include_system: bool = False) -> list[str]:
        rows = self._execute("SHOW DATABASES")
        database_names = [str(row["name"]) for row in rows if row.get("name")]
        if include_system:
            return sorted(database_names)
        return sorted(
            database_name
            for database_name in database_names
            if database_name.upper() not in self.SYSTEM_DATABASE_NAMES
        )

    def list_schemas(self, database_name: str, *, include_system: bool = False) -> list[str]:
        rows = self._execute(f"SHOW SCHEMAS IN DATABASE {self._quote_identifier(database_name)}")
        schema_names = [str(row["name"]) for row in rows if row.get("name")]
        if include_system:
            return sorted(schema_names)
        return sorted(
            schema_name
            for schema_name in schema_names
            if schema_name.upper() not in self.SYSTEM_SCHEMA_NAMES
        )

    def _execute(self, statement: str) -> list[dict[str, Any]]:
        try:
            import snowflake.connector
        except ImportError as exc:
            raise ProviderError(
                description="Snowflake connector is not installed.",
                context={"extra": "snowflake"},
                suggestion="Install `datamuru[snowflake]` before using Snowflake live discovery.",
            ) from exc

        connection_kwargs = self._connection_kwargs()
        try:
            with snowflake.connector.connect(**connection_kwargs) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(statement)
                    columns = [column[0].lower() for column in cursor.description or []]
                    return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        except Exception as exc:  # pragma: no cover - exercised by integration tests.
            raise ProviderError(
                description="Snowflake SQL request could not be completed.",
                context={"statement": statement, "error": self._redact_error_message(str(exc))},
                suggestion="Verify Snowflake account, user, role, warehouse, authenticator, and network access.",
            ) from exc

    def _redact_error_message(self, message: str) -> str:
        sensitive_values = {
            value
            for value in (
                self.auth.resolve_host(),
                self.auth.resolve_user(),
                self.auth.resolve_token(),
                self.auth.resolve_account(),
            )
            if value
        }
        for value in sorted(sensitive_values, key=len, reverse=True):
            message = message.replace(value, "[REDACTED]")
        return message

    def _connection_kwargs(self) -> dict[str, Any]:
        account = self.auth.resolve_account()
        if not account:
            raise ProviderError(
                description="Snowflake account is required for live discovery.",
                context={"account_env": self.auth.account_env},
                suggestion="Set account or account_env in providers/snowflake.yml.",
            )
        kwargs: dict[str, Any] = {
            "account": account,
            "authenticator": self.auth.auth_type,
        }
        host = self.auth.resolve_host()
        if host:
            kwargs["host"] = host
        user = self.auth.resolve_user()
        if user:
            kwargs["user"] = user
        if self.auth.uses_programmatic_access_token():
            token = self.auth.resolve_token()
            if not token:
                raise ProviderError(
                    description=(
                        "Snowflake Programmatic Access Token is required for PAT authentication."
                    ),
                    context={"token_env": self.auth.token_env},
                    suggestion=(
                        "Set the configured token environment variable before live discovery."
                    ),
                )
            kwargs["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
            kwargs["token"] = token
        else:
            password = self.auth.resolve_password()
            if password:
                kwargs["password"] = password
        if self.auth.role:
            kwargs["role"] = self.auth.role
        if self.auth.warehouse:
            kwargs["warehouse"] = self.auth.warehouse
        return kwargs

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'


def import_schemas_by_database(
    client: SnowflakeSqlClient,
    database_names: Iterable[str],
    *,
    include_system: bool,
) -> dict[str, list[str]]:
    return {
        database_name: client.list_schemas(database_name, include_system=include_system)
        for database_name in database_names
    }
