from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.core.plan import fingerprint, matches_target
from datamuru.core.state import resolve_state_backend
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.errors import ImportAdoptionError, ProviderError
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
from datamuru.providers.databricks.client import ConnectivityProbeResult
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


def test_import_generate_enterprise_suite_uses_provider_workspace_scope_names(sample_project, tmp_path, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="us-poc-dev",
            cloud="azure",
            region="eastus",
            catalogs=[
                ImportCatalogResource(
                    name="finance_raw",
                    schemas=[ImportSchemaResource(name="raw")],
                )
            ],
            grants=[
                ImportGrantResource(
                    principal="finance-readers",
                    privilege="USE_CATALOG",
                    securable_type="catalog",
                    securable_name="finance_raw",
                )
            ],
        ),
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    result = DataMuru(sample_project / "datamuru.yml").import_suite(
        output_dir=tmp_path,
        catalogs=["finance_raw"],
        suite_layout="enterprise",
    )

    workspace_path = tmp_path / "workspaces" / "databricks.dev.us-poc-dev.finance-raw.workspace.yml"
    rbac_path = tmp_path / "governance" / "databricks.dev.us-poc-dev.finance-raw.rbac.yml"
    assert workspace_path.exists()
    assert rbac_path.exists()
    assert result.suite_files["workspace"] == str(workspace_path)
    assert result.workspace_name == "us-poc-dev"


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


def test_import_generate_cli_accepts_enterprise_suite_layout(sample_project, tmp_path, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="alpha-dev",
            cloud="azure",
            region="eastus",
            catalogs=[ImportCatalogResource(name="dm_imported", schemas=[])],
            grants=[
                ImportGrantResource(
                    principal="analysts",
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

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "generate",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--catalog",
            "dm_imported",
            "--suite-out",
            str(tmp_path),
            "--suite-layout",
            "enterprise",
        ],
    )

    assert result.exit_code == 0
    assert "enterprise" in result.output
    assert (tmp_path / "workspaces" / "databricks.dev.alpha-dev.dm-imported.workspace.yml").exists()


def test_import_discover_help_exposes_enterprise_scan_guards():
    result = CliRunner().invoke(cli, ["import", "discover", "--help"])

    assert result.exit_code == 0
    assert "--grant-scope" in result.output
    assert "--max-grant-objects" in result.output
    assert "--max-catalog-grant-objects" in result.output
    assert "--max-schema-grant-objects" in result.output
    assert "--progress-checkpoint" in result.output
    assert "--job-checkpoint" in result.output
    assert "--resume-from" in result.output


def test_import_discover_writes_progress_checkpoint_for_json_output(sample_project, tmp_path, monkeypatch):
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

    def fake_discover(self, project, environment, **kwargs):
        progress = kwargs.get("progress")
        if progress:
            progress(
                {
                    "stage": "catalog_inventory",
                    "message": "Discovered 1 catalog.",
                    "total": 2,
                    "completed": 1,
                }
            )
        return report

    monkeypatch.setattr(DatabricksProvider, "discover_importable_resources", fake_discover)
    checkpoint = tmp_path / "import-progress.json"

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "discover",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--output",
            "json",
            "--progress-checkpoint",
            str(checkpoint),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["event"]["stage"] == "catalog_inventory"
    assert payload["event"]["completed"] == 1


def test_import_discover_writes_resumable_job_checkpoint(sample_project, tmp_path, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="alpha-dev",
            cloud="azure",
            region="eastus",
            catalogs=[ImportCatalogResource(name="dm_imported", schemas=[])],
            grants=[
                ImportGrantResource(
                    principal="analysts",
                    privilege="USE_CATALOG",
                    securable_type="catalog",
                    securable_name="dm_imported",
                )
            ],
        ),
    )

    def fake_discover(self, project, environment, **kwargs):
        progress = kwargs.get("progress")
        if progress:
            progress(
                {
                    "stage": "grant_scan",
                    "message": "Scanned grants for catalog dm_imported.",
                    "checkpoint_update": {
                        "completed_grant_target": {
                            "object_type": "catalog",
                            "object_name": "dm_imported",
                        },
                        "grants": [
                            {
                                "principal": "analysts",
                                "privilege": "USE_CATALOG",
                                "securable_type": "catalog",
                                "securable_name": "dm_imported",
                            }
                        ],
                    },
                }
            )
        return report

    monkeypatch.setattr(DatabricksProvider, "discover_importable_resources", fake_discover)
    checkpoint = tmp_path / "import-job.json"

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "discover",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--output",
            "json",
            "--job-checkpoint",
            str(checkpoint),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["completed_grant_targets"] == [
        {"object_type": "catalog", "object_name": "dm_imported"}
    ]
    assert payload["grants"][0]["principal"] == "analysts"


def test_databricks_import_resume_skips_completed_grant_targets(monkeypatch):
    provider = DatabricksProvider(
        {
            "provider": {
                "cloud": "azure",
                "execution_mode": "live-readonly",
                "host": "https://example.cloud.databricks.com",
                "token_env": "DATABRICKS_TOKEN",
                "sql_warehouse_id": "warehouse-1",
            }
        }
    )
    project = SimpleNamespace(
        workspaces=[
            SimpleNamespace(
                raw={
                    "workspace": {
                        "name": "enterprise-dev",
                        "cloud": "azure",
                        "region": "eastus",
                    }
                }
            )
        ]
    )
    grant_calls: list[tuple[str, str]] = []
    progress_events: list[dict] = []
    monkeypatch.setattr(
        provider.client,
        "probe_workspace",
        lambda: ConnectivityProbeResult(ok=True, code="provider.connectivity", message="ok"),
    )
    monkeypatch.setattr(provider, "_safe_list_groups", lambda include_system: [])
    monkeypatch.setattr(provider, "_safe_discover_identities", lambda include_system, enabled: ([], [], []))
    monkeypatch.setattr(provider, "_safe_list_catalogs", lambda include_system: ["finance"])
    monkeypatch.setattr(provider, "_safe_list_schemas", lambda catalog_name, include_system: ["raw"])

    def fake_show_grants(securable_type, securable_name):
        grant_calls.append((securable_type, securable_name))
        return [
            ImportGrantResource(
                principal="raw-editors",
                privilege="USE_SCHEMA",
                securable_type=securable_type,
                securable_name=securable_name,
            )
        ]

    monkeypatch.setattr(provider, "_safe_show_grants", fake_show_grants)

    report = provider.discover_importable_resources(
        project,
        "dev",
        include_grants=True,
        grant_scope="all",
        resume_checkpoint={
            "completed_grant_targets": [{"object_type": "catalog", "object_name": "finance"}],
            "grants": [
                {
                    "principal": "analysts",
                    "privilege": "USE_CATALOG",
                    "securable_type": "catalog",
                    "securable_name": "finance",
                }
            ],
        },
        progress=progress_events.append,
    )

    assert grant_calls == [("schema", "finance.raw")]
    assert [grant.principal for grant in report.workspace.grants] == ["analysts", "raw-editors"]
    assert any("Skipped completed grant scan for catalog finance." in event["message"] for event in progress_events)
    assert any(
        event.get("checkpoint_update", {}).get("completed_grant_target")
        == {"object_type": "schema", "object_name": "finance.raw"}
        for event in progress_events
    )


def test_databricks_import_stops_before_schema_grant_scan_when_type_budget_exceeded(monkeypatch):
    provider = DatabricksProvider(
        {
            "provider": {
                "cloud": "azure",
                "execution_mode": "live-readonly",
                "host": "https://example.cloud.databricks.com",
                "token_env": "DATABRICKS_TOKEN",
                "sql_warehouse_id": "warehouse-1",
            }
        }
    )
    project = SimpleNamespace(
        workspaces=[
            SimpleNamespace(
                raw={
                    "workspace": {
                        "name": "enterprise-dev",
                        "cloud": "azure",
                        "region": "eastus",
                    }
                }
            )
        ]
    )
    grant_calls: list[str] = []
    monkeypatch.setattr(
        provider.client,
        "probe_workspace",
        lambda: ConnectivityProbeResult(ok=True, code="provider.connectivity", message="ok"),
    )
    monkeypatch.setattr(provider, "_safe_list_groups", lambda include_system: [])
    monkeypatch.setattr(provider, "_safe_discover_identities", lambda include_system, enabled: ([], [], []))
    monkeypatch.setattr(provider, "_safe_list_catalogs", lambda include_system: ["finance"])
    monkeypatch.setattr(provider, "_safe_list_schemas", lambda catalog_name, include_system: ["raw", "silver"])
    monkeypatch.setattr(
        provider,
        "_safe_show_grants",
        lambda securable_type, securable_name: grant_calls.append(securable_name) or [],
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.discover_importable_resources(
            project,
            "dev",
            include_grants=True,
            grant_scope="all",
            grant_object_budgets={"schema": 1},
        )

    assert exc_info.value.description == "Import grant discovery was stopped by an object-type scan budget."
    assert exc_info.value.context["object_type"] == "schema"
    assert exc_info.value.context["objects_in_scope"] == 2
    assert grant_calls == []


def test_local_web_ui_is_not_public_cli_surface():
    result = CliRunner().invoke(cli, ["ui", "--help"])

    assert result.exit_code != 0
    assert "No such command 'ui'" in result.output
