from datamuru.core.config import load_project
from datamuru.errors import ProviderError
from datamuru.providers.factory import load_provider


def test_doctor_fails_when_pat_env_is_missing(sample_project):
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
    else:  # pragma: no cover
        raise AssertionError("Expected ProviderError for live-readonly mutation guard")
