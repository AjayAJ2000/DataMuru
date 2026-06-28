from __future__ import annotations

import json

import pytest

from datamuru.errors import ProviderError
from datamuru.providers.snowflake.auth import SnowflakeAuthConfig
from datamuru.providers.snowflake.client import SnowflakeSqlClient
from datamuru.providers.snowflake.provider import SnowflakeProvider


def _pat_auth(**overrides: str) -> SnowflakeAuthConfig:
    data = {
        "host_env": "SNOWFLAKE_HOST",
        "user_env": "SNOWFLAKE_USERNAME",
        "token_env": "SNOWFLAKE_TOKEN",
        "auth_type": "programmatic_access_token",
        "execution_mode": "live-readonly",
    }
    data.update(overrides)
    return SnowflakeAuthConfig.model_validate(data)


def test_pat_auth_resolves_url_host_account_user_and_token(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "https://acme-analytics.snowflakecomputing.com/")
    monkeypatch.setenv("SNOWFLAKE_USERNAME", "operator")
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "pat-secret")

    auth = _pat_auth()

    assert auth.resolve_host() == "acme-analytics.snowflakecomputing.com"
    assert auth.resolve_account() == "acme-analytics"
    assert auth.resolve_user() == "operator"
    assert auth.resolve_token() == "pat-secret"
    assert auth.uses_programmatic_access_token() is True


def test_pat_auth_normalizes_hostname_without_scheme(monkeypatch) -> None:
    monkeypatch.setenv(
        "SNOWFLAKE_HOST",
        "Acme-Analytics.SnowflakeComputing.com:443/console",
    )

    auth = _pat_auth()

    assert auth.resolve_host() == "acme-analytics.snowflakecomputing.com"
    assert auth.resolve_account() == "acme-analytics"


def test_explicit_account_takes_precedence_over_environment_and_host(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "environment-account")
    monkeypatch.setenv("SNOWFLAKE_HOST", "host-account.snowflakecomputing.com")

    auth = _pat_auth(account="explicit-account", account_env="SNOWFLAKE_ACCOUNT")

    assert auth.resolve_account() == "explicit-account"


def test_account_environment_takes_precedence_over_host(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "environment-account")
    monkeypatch.setenv("SNOWFLAKE_HOST", "host-account.snowflakecomputing.com")

    auth = _pat_auth(account_env="SNOWFLAKE_ACCOUNT")

    assert auth.resolve_account() == "environment-account"


def test_non_snowflake_host_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "database.example.com")

    auth = _pat_auth()

    assert auth.resolve_host() is None
    assert auth.resolve_account() is None


def test_pat_connector_kwargs_are_explicit(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "https://acme-analytics.snowflakecomputing.com/")
    monkeypatch.setenv("SNOWFLAKE_USERNAME", "operator")
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "pat-secret")
    auth = _pat_auth(warehouse="COMPUTE_WH", role="SYSADMIN")

    assert SnowflakeSqlClient(auth)._connection_kwargs() == {
        "account": "acme-analytics",
        "host": "acme-analytics.snowflakecomputing.com",
        "user": "operator",
        "authenticator": "PROGRAMMATIC_ACCESS_TOKEN",
        "token": "pat-secret",
        "warehouse": "COMPUTE_WH",
        "role": "SYSADMIN",
    }


def test_pat_connector_missing_token_error_is_redacted(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "acme-analytics.snowflakecomputing.com")
    monkeypatch.delenv("SNOWFLAKE_TOKEN", raising=False)

    with pytest.raises(ProviderError) as exc_info:
        SnowflakeSqlClient(_pat_auth())._connection_kwargs()

    rendered = json.dumps(
        {
            "description": exc_info.value.description,
            "context": exc_info.value.context,
            "suggestion": exc_info.value.suggestion,
        }
    )
    assert exc_info.value.context == {"token_env": "SNOWFLAKE_TOKEN"}
    assert "pat-secret" not in rendered


def test_pat_connector_error_redacts_resolved_credentials(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "acme-analytics.snowflakecomputing.com")
    monkeypatch.setenv("SNOWFLAKE_USERNAME", "operator")
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "pat-secret")
    client = SnowflakeSqlClient(_pat_auth())
    message = (
        "Connection failed for operator at acme-analytics.snowflakecomputing.com "
        "using acme-analytics and pat-secret"
    )

    redacted = client._redact_error_message(message)

    assert "operator" not in redacted
    assert "acme-analytics" not in redacted
    assert "pat-secret" not in redacted
    assert redacted.count("[REDACTED]") == 4


def test_external_browser_connector_kwargs_are_preserved() -> None:
    auth = SnowflakeAuthConfig(account="acme", auth_type="externalbrowser", user="operator")

    assert SnowflakeSqlClient(auth)._connection_kwargs() == {
        "account": "acme",
        "authenticator": "externalbrowser",
        "user": "operator",
    }


def test_password_connector_kwargs_are_preserved(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "password-secret")
    auth = SnowflakeAuthConfig(
        account="acme",
        auth_type="snowflake",
        user="operator",
        password_env="SNOWFLAKE_PASSWORD",
    )

    assert SnowflakeSqlClient(auth)._connection_kwargs() == {
        "account": "acme",
        "authenticator": "snowflake",
        "user": "operator",
        "password": "password-secret",
    }


def test_pat_doctor_reports_ready_without_serializing_token(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "acme-analytics.snowflakecomputing.com")
    monkeypatch.setenv("SNOWFLAKE_USERNAME", "operator")
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "pat-secret")
    provider = SnowflakeProvider({"provider": _pat_auth().model_dump()})

    checks = {check.code: check for check in provider.doctor(None, "dev").checks}

    assert checks["provider.account"].level == "ok"
    assert checks["provider.user"].level == "ok"
    assert checks["provider.pat"].level == "ok"
    assert provider.authenticate({}) is True
    assert "pat-secret" not in json.dumps([check.model_dump() for check in checks.values()])


def test_pat_doctor_reports_missing_token_environment(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_HOST", "acme-analytics.snowflakecomputing.com")
    monkeypatch.setenv("SNOWFLAKE_USERNAME", "operator")
    monkeypatch.delenv("SNOWFLAKE_TOKEN", raising=False)
    provider = SnowflakeProvider({"provider": _pat_auth().model_dump()})

    checks = {check.code: check for check in provider.doctor(None, "dev").checks}

    assert checks["provider.pat"].level == "error"
    assert "SNOWFLAKE_TOKEN" in checks["provider.pat"].message
    assert provider.authenticate({}) is False
