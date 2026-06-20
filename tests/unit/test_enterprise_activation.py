import json

from click.testing import CliRunner

from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.enterprise import build_activation_report


def _enable_enterprise_activation(sample_project):
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("edition: open-source", "edition: enterprise")
    text = text.replace("hosted_control_plane: false", "hosted_control_plane: true")
    text = text.replace("identity_management: false", "identity_management: true")
    text += "\n" + "\n".join(
        [
            "enterprise:",
            "  activation:",
            "    organization: Acme Data",
            "    contact_email: platform@acme.test",
            "    control_plane_url: https://control.datamuru.example",
            "    tenant_id: acme-prod",
            "    deployment_region: us-east-1",
            "    license_key_env: DATAMURU_LICENSE_KEY",
            "    purchase_reference: PO-12345",
            "    support_plan: enterprise",
            "",
        ]
    )
    config_path.write_text(text, encoding="utf-8")
    return config_path


def test_activation_report_blocks_open_source_projects(sample_project):
    project = load_project(sample_project / "datamuru.yml")

    report = build_activation_report(project, environ={})

    assert report.ready is False
    assert {check.code for check in report.checks} >= {
        "activation.edition",
        "activation.hosted_control_plane",
        "activation.config_missing",
    }
    assert report.payload["schema_version"] == "datamuru.enterprise_activation.v1"
    assert report.payload["activation"]["license_key_present"] is False


def test_activation_report_is_ready_with_enterprise_config_and_license_env(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    report = build_activation_report(project, environ={"DATAMURU_LICENSE_KEY": "secret-value"})

    assert report.ready is True
    assert report.checks == []
    assert report.payload["activation"]["organization"] == "Acme Data"
    assert report.payload["activation"]["license_key_env"] == "DATAMURU_LICENSE_KEY"
    assert report.payload["activation"]["license_key_present"] is True
    assert "secret-value" not in json.dumps(report.to_dict())


def test_activation_cli_outputs_json_and_suppresses_secret(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "check",
            "--config",
            str(config_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ready"] is True
    assert payload["payload"]["activation"]["license_key_present"] is True
    assert "secret-value" not in result.output


def test_activation_cli_fails_when_license_env_missing(sample_project):
    config_path = _enable_enterprise_activation(sample_project)

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "check",
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 1
    assert "License key environment variable" in result.output
    assert "DATAMURU_LICENSE_KEY is not set" in result.output.replace("\n", " ")
