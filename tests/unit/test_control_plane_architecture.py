import json

from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.enterprise import build_hosted_control_plane_architecture


def test_hosted_control_plane_architecture_describes_reference_boundary(sample_project):
    project = load_project(sample_project / "datamuru.yml")

    architecture = build_hosted_control_plane_architecture(project)
    payload = architecture.to_dict()

    assert payload["schema_version"] == "datamuru.hosted_control_plane_architecture.v1"
    assert payload["status"] == "reference-architecture"
    assert payload["project"] == "sample-project"
    assert {component["name"] for component in payload["components"]} >= {
        "oss_cli_and_python_api",
        "hosted_control_plane_api",
        "job_runner",
        "state_extension",
        "audit_evidence_store",
    }
    assert {decision["id"] for decision in payload["decisions"]} >= {
        "HCP-001",
        "HCP-002",
        "HCP-003",
        "HCP-004",
    }
    assert any(item["id"] == "HCP-B3" for item in payload["implementation_backlog"])
    assert any("Do not store license keys" in non_goal for non_goal in payload["non_goals"])


def test_control_plane_architecture_cli_outputs_json_and_writes_file(sample_project):
    output_path = sample_project / ".datamuru" / "control-plane" / "architecture.json"

    result = CliRunner().invoke(
        cli,
        [
            "enterprise",
            "control-plane",
            "architecture",
            "--config",
            str(sample_project / "datamuru.yml"),
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
    assert stdout_payload["schema_version"] == "datamuru.hosted_control_plane_architecture.v1"
    assert file_payload["status"] == "reference-architecture"
    assert file_payload["implementation_backlog"]


def test_control_plane_architecture_writer_is_available_from_python_api(sample_project):
    output_path = sample_project / ".datamuru" / "control-plane" / "api-architecture.json"

    architecture = DataMuru(sample_project / "datamuru.yml").enterprise_control_plane_architecture()
    resolved = DataMuru(sample_project / "datamuru.yml").write_enterprise_control_plane_architecture(output_path)

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    assert architecture.schema_version == "datamuru.hosted_control_plane_architecture.v1"
    assert payload["project"] == "sample-project"
    assert payload["extension_points"]
