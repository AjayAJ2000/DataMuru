import json

from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.enterprise import (
    build_activation_bundle,
    build_activation_evidence_report,
    build_activation_handoff_package,
    build_activation_purchase_request,
    build_activation_report,
)


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


def test_activation_purchase_request_wraps_commercial_handoff(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)
    report = build_activation_report(project, environ={"DATAMURU_LICENSE_KEY": "secret-value"})

    purchase_request = build_activation_purchase_request(report)
    payload = purchase_request.to_dict()

    assert payload["schema_version"] == "datamuru.enterprise_purchase_request.v1"
    assert payload["status"] == "ready"
    assert payload["commercial"]["organization"] == "Acme Data"
    assert payload["commercial"]["purchase_reference"] == "PO-12345"
    assert "hosted_control_plane" in payload["commercial"]["requested_entitlements"]
    assert "identity_management" in payload["commercial"]["requested_entitlements"]
    assert payload["fulfillment"]["tenant_id"] == "acme-prod"
    assert payload["fulfillment"]["offline"] is True
    assert payload["fulfillment"]["provisions_tenant"] is False
    assert payload["fulfillment"]["calls_license_server"] is False
    assert payload["license"]["license_key_env"] == "DATAMURU_LICENSE_KEY"
    assert payload["license"]["license_key_present"] is True
    assert payload["license"]["secret_values_included"] is False
    assert "secret-value" not in json.dumps(payload)


def test_activation_purchase_request_cli_writes_ready_request(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "activation" / "purchase-request.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "purchase-request",
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
    request = json.loads(output_path.read_text(encoding="utf-8"))
    assert cli_payload["ready"] is True
    assert request["status"] == "ready"
    assert request["commercial"]["support_plan"] == "enterprise"
    assert request["license"]["license_key_env"] == "DATAMURU_LICENSE_KEY"
    assert "secret-value" not in result.output
    assert "secret-value" not in json.dumps(request)


def test_activation_purchase_request_writer_is_available_from_python_api(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "activation" / "api-purchase-request.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    request = DataMuru(config_path).enterprise_activation_purchase_request()
    resolved = DataMuru(config_path).write_enterprise_activation_purchase_request(output_path)

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    assert request.status == "ready"
    assert payload["status"] == "ready"
    assert payload["fulfillment"]["control_plane_url"] == "https://control.datamuru.example"
    assert "secret-value" not in json.dumps(payload)


def test_activation_purchase_request_blocks_without_allow_blocked(sample_project):
    output_path = sample_project / ".datamuru" / "activation" / "blocked-purchase-request.json"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "purchase-request",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 1
    assert "Purchase request not written" in result.output
    assert not output_path.exists()


def test_activation_purchase_request_can_write_blocked_diagnostic_request(sample_project):
    output_path = sample_project / ".datamuru" / "activation" / "blocked-purchase-request.json"

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "purchase-request",
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
    request = json.loads(output_path.read_text(encoding="utf-8"))
    assert request["status"] == "blocked"
    assert request["report"]["ready"] is False
    assert request["report"]["checks"]
    assert request["license"]["secret_values_included"] is False


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


def test_activation_evidence_report_wraps_redacted_handoff_artifacts(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    report = build_activation_evidence_report(project, environ={"DATAMURU_LICENSE_KEY": "secret-value"})
    payload = report.to_dict()

    assert report.ready is True
    assert payload["schema_version"] == "datamuru.enterprise_activation_evidence.v1"
    assert payload["status"] == "ready"
    assert payload["activation"]["ready"] is True
    assert payload["control_plane"]["ready"] is True
    assert payload["audit"]["offline"] is True
    assert payload["audit"]["mutates_provider"] is False
    assert payload["audit"]["secret_values_included"] is False
    assert {artifact["name"] for artifact in payload["artifacts"]} >= {
        "activation_readiness",
        "hosted_control_plane_contract",
        "secret_redaction",
    }
    assert "secret-value" not in json.dumps(payload)


def test_activation_evidence_cli_writes_ready_report(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "activation" / "evidence.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "evidence",
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
    evidence = json.loads(output_path.read_text(encoding="utf-8"))
    assert cli_payload["ready"] is True
    assert evidence["status"] == "ready"
    assert evidence["control_plane"]["schema_version"] == "datamuru.hosted_control_plane_contract.v1"
    assert "secret-value" not in json.dumps(evidence)


def test_activation_evidence_writer_is_available_from_python_api(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "activation" / "api-evidence.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    report = DataMuru(config_path).enterprise_activation_evidence_report()
    resolved = DataMuru(config_path).write_enterprise_activation_evidence(output_path)

    evidence = json.loads(resolved.read_text(encoding="utf-8"))
    assert report.ready is True
    assert evidence["ready"] is True
    assert evidence["audit"]["mutates_state"] is False
    assert "secret-value" not in json.dumps(evidence)


def test_activation_evidence_blocks_without_allow_blocked(sample_project):
    output_path = sample_project / ".datamuru" / "activation" / "blocked-evidence.json"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "evidence",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 1
    assert "Activation evidence not written" in result.output
    assert not output_path.exists()


def test_activation_evidence_can_write_blocked_diagnostic_report(sample_project):
    output_path = sample_project / ".datamuru" / "activation" / "blocked-evidence.json"

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "evidence",
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
    evidence = json.loads(output_path.read_text(encoding="utf-8"))
    assert evidence["status"] == "blocked"
    assert evidence["activation"]["checks"]
    assert evidence["audit"]["secret_values_included"] is False


def test_activation_handoff_package_manifest_lists_redacted_artifacts(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    package = build_activation_handoff_package(
        project,
        sample_project / ".datamuru" / "activation-package",
        environ={"DATAMURU_LICENSE_KEY": "secret-value"},
    )
    payload = package.to_dict()

    assert payload["schema_version"] == "datamuru.enterprise_activation_handoff_package.v1"
    assert payload["status"] == "ready"
    assert payload["ready"] is True
    assert payload["redaction"]["secret_values_included"] is False
    assert {artifact["name"] for artifact in payload["artifacts"]} == {
        "activation_bundle",
        "purchase_request",
        "activation_evidence",
        "control_plane_contract",
        "control_plane_architecture",
    }
    assert "secret-value" not in json.dumps(payload)


def test_activation_package_cli_writes_ready_package(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_dir = sample_project / ".datamuru" / "activation-package"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "package",
            "--config",
            str(config_path),
            "--out",
            str(output_dir),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "enterprise-activation.json").exists()
    assert (output_dir / "purchase-request.json").exists()
    assert (output_dir / "activation-evidence.json").exists()
    assert (output_dir / "control-plane-contract.json").exists()
    assert (output_dir / "control-plane-architecture.json").exists()
    cli_payload = json.loads(result.output)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert cli_payload["ready"] is True
    assert manifest["status"] == "ready"
    assert manifest["redaction"]["license_key_value_included"] is False
    assert "secret-value" not in result.output
    assert "secret-value" not in json.dumps(manifest)


def test_activation_package_writer_is_available_from_python_api(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_dir = sample_project / ".datamuru" / "api-activation-package"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    package = DataMuru(config_path).enterprise_activation_handoff_package(output_dir)
    written = DataMuru(config_path).write_enterprise_activation_handoff_package(output_dir)

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert package.ready is True
    assert written.ready is True
    assert manifest["ready"] is True
    assert len(manifest["artifacts"]) == 5
    assert "secret-value" not in json.dumps(manifest)


def test_activation_package_blocks_without_allow_blocked(sample_project):
    output_dir = sample_project / ".datamuru" / "blocked-activation-package"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "activation",
            "package",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_dir),
        ],
    )

    assert result.exit_code == 1
    assert "Activation handoff package not written" in result.output
    assert not output_dir.exists()


def test_activation_package_can_write_blocked_diagnostic_package(sample_project):
    output_dir = sample_project / ".datamuru" / "blocked-activation-package"

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "activation",
            "package",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_dir),
            "--allow-blocked",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    evidence = json.loads((output_dir / "activation-evidence.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "blocked"
    assert manifest["ready"] is False
    assert evidence["activation"]["checks"]
    assert manifest["redaction"]["secret_values_included"] is False
