import json

from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.enterprise import build_activation_bundle, build_activation_report


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


def test_activation_bundle_wraps_redacted_report(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)
    report = build_activation_report(project, environ={"DATAMURU_LICENSE_KEY": "secret-value"})

    bundle = build_activation_bundle(report)
    payload = bundle.to_dict()

    assert payload["schema_version"] == "datamuru.enterprise_activation_bundle.v1"
    assert payload["status"] == "ready"
    assert payload["report"]["ready"] is True
    assert payload["report"]["payload"]["activation"]["license_key_present"] is True
    assert "secret-value" not in json.dumps(payload)


def test_activation_export_writes_ready_bundle(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "activation" / "bundle.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "export",
            "--config",
            str(config_path),
            "--out",
            str(output_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    cli_payload = json.loads(result.output)
    bundle = json.loads(output_path.read_text(encoding="utf-8"))
    assert cli_payload["ready"] is True
    assert bundle["status"] == "ready"
    assert bundle["report"]["payload"]["activation"]["license_key_env"] == "DATAMURU_LICENSE_KEY"
    assert "secret-value" not in json.dumps(bundle)


def test_activation_bundle_writer_is_available_from_python_api(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "activation" / "api-bundle.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    resolved = DataMuru(config_path).write_enterprise_activation_bundle(output_path)

    bundle = json.loads(resolved.read_text(encoding="utf-8"))
    assert bundle["status"] == "ready"
    assert bundle["report"]["ready"] is True
    assert "secret-value" not in json.dumps(bundle)


def test_activation_export_blocks_without_allow_blocked(sample_project):
    output_path = sample_project / ".datamuru" / "activation" / "blocked.json"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "export",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 1
    assert "Activation bundle not written" in result.output
    assert not output_path.exists()


def test_activation_export_can_write_blocked_diagnostic_bundle(sample_project):
    output_path = sample_project / ".datamuru" / "activation" / "blocked.json"

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "export",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_path),
            "--allow-blocked",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    bundle = json.loads(output_path.read_text(encoding="utf-8"))
    assert bundle["status"] == "blocked"
    assert bundle["report"]["ready"] is False
    assert bundle["report"]["checks"]
