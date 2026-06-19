from __future__ import annotations

import pytest
from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.core.plan import fingerprint, matches_target
from datamuru.core.state import resolve_state_backend
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.errors import ImportAdoptionError
from datamuru.core.importer.models import (
    ImportCatalogResource,
    ImportDiscoveryReport,
    ImportGrantResource,
    ImportGroupResource,
    ImportSchemaResource,
    ImportServicePrincipalResource,
    ImportUserResource,
    ImportWorkspaceResource,
)
from datamuru.providers.databricks.provider import DatabricksProvider
from datamuru.providers.factory import load_provider
from datamuru.types import ResourceDescriptor


def _observed_catalog_state(sample_project, target: str) -> StateSnapshot:
    project = load_project(sample_project / "datamuru.yml")
    resources = load_provider(project).build_desired_resources(project)
    return StateSnapshot(
        resources={
            resource.address: StateResourceRecord(
                fingerprint=fingerprint(resource),
                attributes=resource.attributes,
            )
            for resource in resources
            if matches_target(resource.address, target)
        }
    )


def test_import_adopt_previews_then_commits_matching_live_resources(sample_project, monkeypatch):
    target = "catalog:dm_alpha_marketing"
    observed = _observed_catalog_state(sample_project, target)
    monkeypatch.setattr(
        DatabricksProvider,
        "observe_current_state",
        lambda self, project, environment: observed,
    )
    dm = DataMuru(sample_project / "datamuru.yml")

    preview = dm.import_adopt(targets=[target])
    assert preview.ready
    assert preview.committed is False
    assert preview.candidates
    assert resolve_state_backend(load_project(sample_project / "datamuru.yml")).load().resources == {}

    result = dm.import_adopt(targets=[target], commit=True)
    state = resolve_state_backend(load_project(sample_project / "datamuru.yml")).load()
    assert result.committed
    assert result.adopted == preview.candidates
    assert set(result.adopted).issubset(state.resources)


def test_import_adopt_blocks_live_definition_conflict(sample_project, monkeypatch):
    target = "catalog:dm_alpha_marketing"
    conflicting_catalog = ResourceDescriptor(
        resource_type="catalog",
        name="dm_alpha_marketing",
        attributes={"workspace": "another-workspace"},
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "observe_current_state",
        lambda self, project, environment: StateSnapshot(
            resources={
                conflicting_catalog.address: StateResourceRecord(
                    fingerprint=fingerprint(conflicting_catalog),
                    attributes=conflicting_catalog.attributes,
                )
            }
        ),
    )
    dm = DataMuru(sample_project / "datamuru.yml")

    preview = dm.import_adopt(targets=[target])
    assert not preview.ready
    assert preview.conflicts
    assert preview.missing
    with pytest.raises(ImportAdoptionError):
        dm.import_adopt(targets=[target], commit=True)


def test_import_adopt_cli_requires_approval_to_write_state(sample_project, monkeypatch):
    target = "catalog:dm_alpha_marketing"
    observed = _observed_catalog_state(sample_project, target)
    monkeypatch.setattr(
        DatabricksProvider,
        "observe_current_state",
        lambda self, project, environment: observed,
    )
    runner = CliRunner()
    config_path = str(sample_project / "datamuru.yml")

    preview = runner.invoke(cli, ["import", "adopt", "--config", config_path, "--target", target])
    assert preview.exit_code == 0
    assert "Preview only" in preview.output

    applied = runner.invoke(
        cli,
        ["import", "adopt", "--config", config_path, "--target", target, "--auto-approve"],
    )
    assert applied.exit_code == 0
    assert "Adopted" in applied.output


def test_import_generate_suite_writes_workspace_and_governance_files(sample_project, tmp_path, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="alpha-dev",
            cloud="azure",
            region="eastus",
            catalogs=[
                ImportCatalogResource(
                    name="dm_imported",
                    schemas=[ImportSchemaResource(name="raw")],
                )
            ],
            users=[ImportUserResource(email="analyst@company.com", display_name="Analyst")],
            group_details=[
                ImportGroupResource(
                    name="dm-analysts",
                    members={"users": ["analyst@company.com"]},
                )
            ],
            service_principals=[
                ImportServicePrincipalResource(name="dm-loader", application_id="app-123")
            ],
            grants=[
                ImportGrantResource(
                    principal="dm-analysts",
                    privilege="USE_CATALOG",
                    securable_type="catalog",
                    securable_name="dm_imported",
                )
            ],
        ),
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    result = DataMuru(sample_project / "datamuru.yml").import_suite(output_dir=tmp_path)

    assert "workspace" in result.suite_files
    assert "rbac" in result.suite_files
    workspace_text = (tmp_path / "workspaces" / "imported-dev.yml").read_text(encoding="utf-8")
    rbac_text = (tmp_path / "governance" / "rbac.imported.yml").read_text(encoding="utf-8")
    assert "analyst@company.com" in workspace_text
    assert "dm-analysts" in workspace_text
    assert "imported_catalog_use_catalog" in rbac_text


def test_import_generate_cli_suite_outputs_written_files(sample_project, tmp_path, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="alpha-dev",
            cloud="azure",
            region="eastus",
            catalogs=[ImportCatalogResource(name="dm_imported", schemas=[])],
        ),
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "generate",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--suite-out",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "import review suite" in result.output
    assert (tmp_path / "workspaces" / "imported-dev.yml").exists()


def test_import_discover_help_exposes_enterprise_scan_guards():
    result = CliRunner().invoke(cli, ["import", "discover", "--help"])

    assert result.exit_code == 0
    assert "--grant-scope" in result.output
    assert "--max-grant-objects" in result.output


def test_ui_help_is_registered():
    result = CliRunner().invoke(cli, ["ui", "--help"])

    assert result.exit_code == 0
    assert "local DataMuru project dashboard" in result.output
