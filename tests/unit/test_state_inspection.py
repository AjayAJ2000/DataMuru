import json

import pytest
from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.core.state import inspect_state_backend
from datamuru.errors import StateBackendError


def _set_state_backend(sample_project, backend: str, path: str) -> None:
    config_path = sample_project / "datamuru.yml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("backend: local", f"backend: {backend}")
    text = text.replace("path: ./.datamuru/state-dev.json", f"path: {path}")
    config_path.write_text(text, encoding="utf-8")


def test_state_inspection_reports_local_backend_ready(sample_project):
    project = load_project(sample_project / "datamuru.yml")

    report = inspect_state_backend(project)

    assert report.success is True
    assert report.backend == "local"
    assert report.runtime_supported is True
    assert report.remote is False
    assert report.mode == "read-write"
    assert report.resolved_location is not None


def test_state_inspection_reports_remote_backend_contract_only(sample_project):
    _set_state_backend(sample_project, "s3", "s3://datamuru-state/sample-project/dev.json")
    project = load_project(sample_project / "datamuru.yml")

    report = inspect_state_backend(project)

    assert report.success is False
    assert report.backend == "s3"
    assert report.remote is True
    assert report.runtime_supported is False
    assert report.mode == "contract-only"
    assert any(check.code == "state.s3.not_implemented" for check in report.checks)


def test_state_backend_report_is_available_from_python_api(sample_project):
    report = DataMuru(sample_project / "datamuru.yml").state_backend_report()

    assert report.success is True
    assert report.backend == "local"


def test_state_inspect_cli_outputs_local_text(sample_project):
    result = CliRunner().invoke(
        cli,
        ["--no-banner", "state", "inspect", "--config", str(sample_project / "datamuru.yml")],
    )

    assert result.exit_code == 0
    assert "State backend" in result.output
    assert "local" in result.output
    assert "read-write" in result.output


def test_state_inspect_cli_outputs_remote_json_and_fails(sample_project):
    _set_state_backend(sample_project, "azure_blob", "https://storage.example/state/dev.json")

    result = CliRunner().invoke(
        cli,
        [
            "state",
            "inspect",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["backend"] == "azure_blob"
    assert payload["success"] is False
    assert payload["remote"] is True
    assert payload["runtime_supported"] is False
    assert payload["checks"][0]["code"] == "state.azure_blob.not_implemented"


def test_plan_fails_fast_for_remote_state_backend_contract(sample_project):
    _set_state_backend(sample_project, "s3", "s3://datamuru-state/sample-project/dev.json")

    with pytest.raises(StateBackendError) as exc_info:
        DataMuru(sample_project / "datamuru.yml").plan()

    assert exc_info.value.code == "DMR-STATE-REMOTE"
    assert exc_info.value.context["backend"] == "s3"
    assert exc_info.value.context["remote"] is True
    assert exc_info.value.context["runtime_supported"] is False
    assert exc_info.value.context["mode"] == "contract-only"
    assert "hosted control plane" in exc_info.value.suggestion
