from datamuru.core.config import load_project
from datamuru.errors import ProviderError
from datamuru.providers.databricks.auth import DatabricksAuthConfig
from datamuru.providers.databricks.client import DatabricksWorkspaceClient
from datamuru.providers.factory import load_provider


def test_doctor_fails_when_pat_env_is_missing(sample_project, monkeypatch):
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: state-only",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    report = provider.doctor(project, "dev")
    assert not report.success
    assert any(check.code == "provider.token_env" for check in report.checks)
    assert any(check.code == "provider.connectivity" and "state-only" in check.message for check in report.checks)


def test_doctor_reports_live_connectivity_when_probe_succeeds(sample_project, monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-readonly",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    monkeypatch.setattr(
        provider.client,
        "probe_workspace",
        lambda: type(
            "Probe",
            (),
            {
                "level": "ok",
                "code": "provider.connectivity",
                "message": "Databricks workspace connectivity probe succeeded.",
                "current_user": "user@datamuru.dev",
            },
        )(),
    )

    report = provider.doctor(project, "dev")
    assert any(check.code == "provider.connectivity" and "user@datamuru.dev" in check.message for check in report.checks)


def test_doctor_resolves_workspace_host_from_environment(sample_project, monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    monkeypatch.setenv("DATABRICKS_HOST", "https://adb-test.azuredatabricks.net")
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: state-only",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host_env: DATABRICKS_HOST",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)

    report = provider.doctor(project, "dev")

    assert provider.auth.host == "https://adb-test.azuredatabricks.net"
    assert any(check.code == "provider.host" and check.level == "ok" for check in report.checks)


def test_doctor_reports_sql_acl_requirement_for_live_permission_bindings(sample_project, monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-readonly",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    monkeypatch.setattr(
        provider.client,
        "probe_workspace",
        lambda: type(
            "Probe",
            (),
            {
                "level": "ok",
                "code": "provider.connectivity",
                "message": "Databricks workspace connectivity probe succeeded.",
                "current_user": "user@datamuru.dev",
            },
        )(),
    )

    report = provider.doctor(project, "dev")
    assert any(check.code == "provider.sql_acl" and check.level == "error" for check in report.checks)


def test_live_readonly_apply_is_blocked(sample_project):
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-readonly",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    resource = provider.build_desired_resources(project)[0]
    try:
        provider.apply_resource(resource)
    except ProviderError as exc:
        assert "live-readonly" in exc.description.lower()
        assert "Switch execution_mode to live-apply" in exc.suggestion
    else:  # pragma: no cover
        raise AssertionError("Expected ProviderError for live-readonly mutation guard")


def test_databricks_auth_resolves_cli_profile(tmp_path, monkeypatch):
    cfg = tmp_path / ".databrickscfg"
    cfg.write_text(
        "\n".join(
            [
                "[enterprise]",
                "host = https://dbc.example.cloud.databricks.com",
                "token = profile-token",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_CONFIG_FILE", str(cfg))

    auth = DatabricksAuthConfig.model_validate(
        {
            "cloud": "azure",
            "auth_type": "databricks-cli",
            "profile": "enterprise",
            "execution_mode": "live-readonly",
        }
    )

    assert auth.host == "https://dbc.example.cloud.databricks.com"
    assert auth.resolve_token() == "profile-token"
    assert auth.workspace_headers()["Authorization"] == "Bearer profile-token"


def test_databricks_cli_profile_headers_use_sdk_unified_auth(monkeypatch):
    class FakeConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def authenticate(self):
            return {"Authorization": "Bearer sdk-profile-token"}

    monkeypatch.setattr("datamuru.providers.databricks.client.Config", FakeConfig)

    auth = DatabricksAuthConfig.model_validate(
        {
            "cloud": "azure",
            "auth_type": "databricks-cli",
            "profile": "US_POC_DEV",
            "host": "https://adb-test.azuredatabricks.net",
            "execution_mode": "live-readonly",
        }
    )

    headers = DatabricksWorkspaceClient(auth).workspace_headers()

    assert headers["Authorization"] == "Bearer sdk-profile-token"
    assert auth.supports_live_connectivity()


def test_doctor_accepts_cli_profile_without_static_token(sample_project, monkeypatch):
    cfg = sample_project / ".databrickscfg"
    cfg.write_text(
        "\n".join(
            [
                "[US_POC_DEV]",
                "host = https://adb-test.azuredatabricks.net",
                "auth_type = databricks-cli",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_CONFIG_FILE", str(cfg))
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  execution_mode: live-readonly",
                "  auth_type: databricks-cli",
                "  profile: US_POC_DEV",
                "  sql_warehouse_id: test-warehouse",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    monkeypatch.setattr(provider.client, "sdk_available", lambda: True)
    monkeypatch.setattr(
        provider.client,
        "probe_workspace",
        lambda: type(
            "Probe",
            (),
            {
                "level": "ok",
                "code": "provider.connectivity",
                "message": "Databricks Unity Catalog connectivity probe succeeded.",
                "current_user": None,
                "details": {"endpoint": "https://adb-test.azuredatabricks.net/api/2.1/unity-catalog/catalogs"},
            },
        )(),
    )

    report = provider.doctor(project, "dev")

    assert report.success
    assert any(
        check.code == "provider.auth_type" and "SDK unified auth" in check.message
        for check in report.checks
    )


def test_connectivity_probe_falls_back_when_scim_me_is_forbidden(monkeypatch):
    auth = DatabricksAuthConfig.model_validate(
        {
            "cloud": "azure",
            "auth_type": "pat",
            "host": "https://adb-test.azuredatabricks.net",
            "token_env": "DATABRICKS_TOKEN",
            "execution_mode": "live-readonly",
        }
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    calls: list[str] = []

    class FakeResponse:
        def __init__(self, status_code: int, payload: dict | None = None) -> None:
            self.status_code = status_code
            self._payload = payload or {}
            self.headers = {"Content-Type": "application/json"}
            self.text = "{}"
            self.url = "https://adb-test.azuredatabricks.net"

        def json(self):
            return self._payload

    def fake_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/api/2.0/preview/scim/v2/Me"):
            return FakeResponse(403)
        if url.endswith("/api/2.1/unity-catalog/catalogs"):
            return FakeResponse(200, {"catalogs": []})
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("datamuru.providers.databricks.client.requests.get", fake_get)

    result = DatabricksWorkspaceClient(auth).probe_workspace()

    assert result.ok
    assert result.level == "ok"
    assert "Unity Catalog connectivity probe succeeded" in result.message
    assert result.details["identity_status_code"] == 403
    assert len(calls) == 2
