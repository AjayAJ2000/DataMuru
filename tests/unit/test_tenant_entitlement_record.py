from datetime import UTC, datetime
import json

from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.enterprise.registry import build_tenant_entitlement_record


GENERATED_AT = datetime(2026, 6, 27, 10, 0, tzinfo=UTC)


def _enable_enterprise_activation(sample_project):
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("edition: open-source", "edition: enterprise")
    text = text.replace("hosted_control_plane: false", "hosted_control_plane: true")
    text = text.replace("identity_management: false", "identity_management: true")
    text = text.replace("compliance_reporting: false", "compliance_reporting: true")
    text = text.replace("multi_workspace: false", "multi_workspace: true")
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


def test_tenant_entitlement_record_is_ready_redacted_and_versioned(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    record = build_tenant_entitlement_record(
        project,
        environ={"DATAMURU_LICENSE_KEY": "secret-value"},
        generated_at=GENERATED_AT,
    )
    payload = record.to_dict()
    serialized = json.dumps(payload)

    assert record.schema_version == "datamuru.tenant_entitlement_record.v1"
    assert record.generated_at == "2026-06-27T10:00:00Z"
    assert record.status == "ready"
    assert record.ready is True
    assert record.record_id.startswith("ter_")
    assert len(record.record_id) == 24
    assert record.tenant["tenant_id"] == "acme-prod"
    assert record.entitlement["enabled_features"] == [
        "compliance_reporting",
        "hosted_control_plane",
        "identity_management",
        "multi_workspace",
    ]
    assert record.entitlement["license_key_env"] == "DATAMURU_LICENSE_KEY"
    assert record.entitlement["license_key_present"] is True
    assert record.security == {
        "offline": True,
        "provisions_tenant": False,
        "calls_license_server": False,
        "mutates_provider": False,
        "mutates_state": False,
        "secret_values_included": False,
    }
    assert "secret-value" not in serialized
    assert str(sample_project.resolve()) not in serialized


def test_tenant_entitlement_record_reports_blocked_activation_checks(sample_project):
    project = load_project(sample_project / "datamuru.yml")

    record = build_tenant_entitlement_record(project, environ={}, generated_at=GENERATED_AT)

    assert record.status == "blocked"
    assert record.ready is False
    assert {check.code for check in record.checks} >= {
        "activation.edition",
        "activation.hosted_control_plane",
        "activation.config_missing",
    }


def test_tenant_entitlement_record_id_is_stable_across_generation_times(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    first = build_tenant_entitlement_record(project, environ={}, generated_at=GENERATED_AT)
    second = build_tenant_entitlement_record(
        project,
        environ={},
        generated_at=datetime(2026, 6, 28, 12, 30, tzinfo=UTC),
    )

    assert first.generated_at != second.generated_at
    assert first.record_id == second.record_id


def test_tenant_entitlement_record_id_ignores_license_availability(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    absent = build_tenant_entitlement_record(project, environ={}, generated_at=GENERATED_AT)
    present = build_tenant_entitlement_record(
        project,
        environ={"DATAMURU_LICENSE_KEY": "secret-value"},
        generated_at=GENERATED_AT,
    )

    assert absent.entitlement["license_key_present"] is False
    assert present.entitlement["license_key_present"] is True
    assert absent.record_id == present.record_id


def test_tenant_entitlement_record_id_changes_with_tenant_binding(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    original = build_tenant_entitlement_record(load_project(config_path), generated_at=GENERATED_AT)
    text = config_path.read_text(encoding="utf-8").replace("tenant_id: acme-prod", "tenant_id: acme-stage")
    config_path.write_text(text, encoding="utf-8")

    changed = build_tenant_entitlement_record(load_project(config_path), generated_at=GENERATED_AT)

    assert original.record_id != changed.record_id


def test_tenant_entitlement_record_id_changes_with_entitlement(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    original = build_tenant_entitlement_record(load_project(config_path), generated_at=GENERATED_AT)
    text = config_path.read_text(encoding="utf-8").replace("support_plan: enterprise", "support_plan: standard")
    config_path.write_text(text, encoding="utf-8")

    changed = build_tenant_entitlement_record(load_project(config_path), generated_at=GENERATED_AT)

    assert original.record_id != changed.record_id


def test_tenant_entitlement_record_is_available_from_python_api(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "tenant-record-api.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")
    dm = DataMuru(config_path)

    record = dm.enterprise_tenant_entitlement_record()
    written = dm.write_enterprise_tenant_entitlement_record(output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert record.ready is True
    assert written == output_path.resolve()
    assert payload["record_id"] == record.record_id
    assert "secret-value" not in json.dumps(payload)


def test_tenant_entitlement_record_cli_writes_ready_json(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "tenant-record.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "control-plane",
            "tenant-record",
            "--config",
            str(config_path),
            "--out",
            str(output_path),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "datamuru.tenant_entitlement_record.v1"
    assert payload == written
    assert payload["ready"] is True
    assert "secret-value" not in result.output


def test_tenant_entitlement_record_cli_blocks_without_writing(sample_project):
    output_path = sample_project / ".datamuru" / "blocked-tenant-record.json"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "control-plane",
            "tenant-record",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 1
    assert "Tenant entitlement record not written" in result.output
    assert not output_path.exists()


def test_tenant_entitlement_record_cli_writes_blocked_diagnostic(sample_project):
    output_path = sample_project / ".datamuru" / "blocked-tenant-record.json"

    result = CliRunner().invoke(
        cli,
        [
            "--no-banner",
            "enterprise",
            "control-plane",
            "tenant-record",
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
    payload = json.loads(result.output)
    assert payload["status"] == "blocked"
    assert payload["ready"] is False
    assert payload["checks"]
    assert payload == json.loads(output_path.read_text(encoding="utf-8"))
