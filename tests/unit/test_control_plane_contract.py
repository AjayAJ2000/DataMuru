import json

from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.enterprise import build_control_plane_contract


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


def _set_state_backend(sample_project, backend: str, path: str) -> None:
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("backend: local", f"backend: {backend}")
    text = text.replace("path: ./.datamuru/state-dev.json", f"path: {path}")
    config_path.write_text(text, encoding="utf-8")


def test_control_plane_contract_blocks_open_source_projects(sample_project):
    project = load_project(sample_project / "datamuru.yml")

    contract = build_control_plane_contract(project, environ={})

    assert contract.ready is False
    assert contract.schema_version == "datamuru.hosted_control_plane_contract.v1"
    assert {check.code for check in contract.checks} >= {
        "control_plane.activation.edition",
        "control_plane.activation.hosted_control_plane",
        "control_plane.activation.config_missing",
    }


def test_control_plane_contract_is_ready_and_redacted_for_enterprise_handoff(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    project = load_project(config_path)

    contract = build_control_plane_contract(project, environ={"DATAMURU_LICENSE_KEY": "secret-value"})
    payload = contract.to_dict()

    assert contract.ready is True
    assert payload["integration"]["tenant_id"] == "acme-prod"
    assert payload["integration"]["license_key_env"] == "DATAMURU_LICENSE_KEY"
    assert payload["integration"]["license_key_present"] is True
    assert payload["state"]["backend"] == "local"
    assert "control_plane.state.local_single_user" in {check["code"] for check in payload["checks"]}
    assert "secret-value" not in json.dumps(payload)


def test_control_plane_contract_accepts_recognized_remote_state_boundary(sample_project):
    config_path = _enable_enterprise_activation(sample_project)
    _set_state_backend(sample_project, "s3", "s3://datamuru-state/sample-project/dev.json")
    project = load_project(config_path)

    contract = build_control_plane_contract(project, environ={"DATAMURU_LICENSE_KEY": "secret-value"})

    assert contract.ready is True
    assert contract.state.backend == "s3"
    assert contract.state.mode == "contract-only"
    assert any(check.code == "control_plane.state.remote_extension_required" for check in contract.checks)


def test_control_plane_contract_cli_outputs_json_and_writes_file(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "control-plane" / "contract.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "control-plane",
            "contract",
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
    stdout_payload = json.loads(result.output)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_payload["ready"] is True
    assert file_payload["ready"] is True
    assert file_payload["schema_version"] == "datamuru.hosted_control_plane_contract.v1"
    assert "secret-value" not in result.output
    assert "secret-value" not in json.dumps(file_payload)


def test_control_plane_contract_writer_is_available_from_python_api(sample_project, monkeypatch):
    config_path = _enable_enterprise_activation(sample_project)
    output_path = sample_project / ".datamuru" / "control-plane" / "api-contract.json"
    monkeypatch.setenv("DATAMURU_LICENSE_KEY", "secret-value")

    contract = DataMuru(config_path).enterprise_control_plane_contract()
    resolved = DataMuru(config_path).write_enterprise_control_plane_contract(output_path)

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    assert contract.ready is True
    assert payload["ready"] is True
    assert payload["project"] == "sample-project"
    assert "secret-value" not in json.dumps(payload)
