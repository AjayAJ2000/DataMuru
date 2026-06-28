from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import yaml
from click.testing import CliRunner

from datamuru.api import DataMuru
from datamuru.cli.main import cli
from datamuru.core.config import load_project
from datamuru.core.engine import DataMuruEngine
from datamuru.core.plan import fingerprint, matches_target
from datamuru.core.state import resolve_state_backend
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.core.importer.engine import ImportEngine
from datamuru.errors import ImportAdoptionError, ProviderError, ValidationError
from datamuru.core.importer.models import (
    ImportCatalogResource,
    ImportDiscoveryReport,
    ImportGrantResource,
    ImportJobCheckpoint,
    ImportGroupResource,
    ImportSchemaResource,
    ImportServicePrincipalResource,
    ImportUserResource,
    ImportWorkspaceResource,
    SnowflakeToDatabricksMappingResult,
)
from datamuru.providers.databricks.client import ConnectivityProbeResult
from datamuru.providers.databricks.provider import DatabricksProvider
from datamuru.providers.factory import load_provider
from datamuru.providers.snowflake.provider import SnowflakeProvider
from datamuru.types import ResourceDescriptor


def test_snowflake_to_databricks_mapping_result_serializes():
    result = SnowflakeToDatabricksMappingResult(
        provider="snowflake",
        environment="dev",
        source_workspace="snowflake-live",
        target_workspace="databricks-dev",
        target_cloud="azure",
        mapping_file_text="migration: {}\n",
        selected_databases=["FINANCE"],
        mapped_catalogs=["sf_finance"],
    )

    assert result.to_dict()["mapped_catalogs"] == ["sf_finance"]
    assert result.to_dict()["target_cloud"] == "azure"


def _configure_snowflake_project(sample_project):
    root = sample_project / "datamuru.yml"
    root.write_text(
        root.read_text(encoding="utf-8")
        .replace("provider: databricks", "provider: snowflake", 1)
        .replace("name: databricks", "name: snowflake", 1)
        .replace("cloud: azure", "cloud: snowflake", 1)
        .replace("config: ./providers/databricks.yml", "config: ./providers/snowflake.yml", 1),
        encoding="utf-8",
    )
    (sample_project / "providers" / "snowflake.yml").write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: snowflake",
                "  account_env: SNOWFLAKE_ACCOUNT",
                "  user_env: SNOWFLAKE_USER",
                "  auth_type: externalbrowser",
                "  execution_mode: live-readonly",
                "",
            ]
        ),
        encoding="utf-8",
    )
    workspace = sample_project / "workspaces" / "alpha-dev.yml"
    workspace.write_text(
        workspace.read_text(encoding="utf-8").replace("cloud: azure", "cloud: snowflake", 1),
        encoding="utf-8",
    )
    return sample_project


def test_import_engine_maps_snowflake_database_to_databricks_catalog(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[
                ImportCatalogResource(
                    name="FINANCE",
                    schemas=[
                        ImportSchemaResource(name="RAW"),
                        ImportSchemaResource(name="CURATED"),
                    ],
                )
            ],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    result = ImportEngine(
        config_path=snowflake_project / "datamuru.yml",
        environment="dev",
    ).snowflake_to_databricks_mapping(
        databases=["FINANCE"],
        target_workspace="databricks-dev",
        target_cloud="azure",
        catalog_prefix="sf",
        identifier_case="lower",
    )

    payload = yaml.safe_load(result.mapping_file_text)["migration"]
    assert payload["source"]["provider"] == "snowflake"
    assert payload["target"] == {
        "provider": "databricks",
        "workspace": "databricks-dev",
        "cloud": "azure",
    }
    assert payload["mappings"]["databases"]["FINANCE"] == {
        "catalog": "sf_finance",
        "schemas": {"RAW": "raw", "CURATED": "curated"},
    }
    assert payload["review"]["status"] == "draft"


def test_snowflake_to_databricks_mapping_blocks_catalog_collision(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[
                ImportCatalogResource(name="FINANCE-RAW"),
                ImportCatalogResource(name="FINANCE_RAW"),
            ],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    with pytest.raises(ValidationError) as exc_info:
        ImportEngine(snowflake_project / "datamuru.yml").snowflake_to_databricks_mapping()

    assert exc_info.value.context["target_identifier"] == "finance_raw"
    assert exc_info.value.context["source_databases"] == ["FINANCE-RAW", "FINANCE_RAW"]


def test_snowflake_to_databricks_mapping_blocks_schema_collision(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[
                ImportCatalogResource(
                    name="FINANCE",
                    schemas=[
                        ImportSchemaResource(name="RAW-ZONE"),
                        ImportSchemaResource(name="RAW_ZONE"),
                    ],
                )
            ],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    with pytest.raises(ValidationError) as exc_info:
        ImportEngine(snowflake_project / "datamuru.yml").snowflake_to_databricks_mapping()

    assert exc_info.value.context["target_identifier"] == "raw_zone"
    assert exc_info.value.context["source_database"] == "FINANCE"
    assert exc_info.value.context["source_schemas"] == ["RAW-ZONE", "RAW_ZONE"]


def test_snowflake_to_databricks_mapping_rejects_empty_identifier(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[ImportCatalogResource(name="---")],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    with pytest.raises(ValidationError) as exc_info:
        ImportEngine(snowflake_project / "datamuru.yml").snowflake_to_databricks_mapping()

    assert exc_info.value.context == {"source_name": "---"}


def test_python_api_delegates_snowflake_to_databricks_mapping(sample_project, monkeypatch):
    expected = SnowflakeToDatabricksMappingResult(
        provider="snowflake",
        environment="dev",
        source_workspace="snowflake-live",
        target_workspace="databricks-dev",
        target_cloud="azure",
        mapping_file_text="migration: {}\n",
        selected_databases=["FINANCE"],
        mapped_catalogs=["sf_finance"],
    )
    captured = {}

    def fake_mapping(self, **kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        DataMuruEngine,
        "import_snowflake_to_databricks_mapping",
        fake_mapping,
        raising=False,
    )

    result = DataMuru(sample_project / "datamuru.yml").import_snowflake_to_databricks_mapping(
        databases=["FINANCE"],
        target_workspace="databricks-dev",
        target_cloud="azure",
        catalog_prefix="sf",
        identifier_case="preserve",
    )

    assert result is expected
    assert captured == {
        "databases": ["FINANCE"],
        "target_workspace": "databricks-dev",
        "target_cloud": "azure",
        "catalog_prefix": "sf",
        "identifier_case": "preserve",
        "progress": None,
    }


def test_import_map_databricks_generates_mapping_draft(sample_project, tmp_path, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[
                ImportCatalogResource(
                    name="FINANCE",
                    schemas=[ImportSchemaResource(name="RAW")],
                )
            ],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )
    output_path = tmp_path / "finance.mapping.yml"

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "map-databricks",
            "--config",
            str(snowflake_project / "datamuru.yml"),
            "--database",
            "FINANCE",
            "--target-workspace",
            "databricks-dev",
            "--target-cloud",
            "azure",
            "--catalog-prefix",
            "sf",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    mapping_text = output_path.read_text(encoding="utf-8")
    assert "provider: snowflake" in mapping_text
    assert "provider: databricks" in mapping_text
    assert "catalog: sf_finance" in mapping_text


def test_import_map_databricks_help_exposes_mapping_options():
    result = CliRunner().invoke(cli, ["import", "map-databricks", "--help"])

    assert result.exit_code == 0
    assert "--database" in result.output
    assert "--target-workspace" in result.output
    assert "--target-cloud" in result.output
    assert "--catalog-prefix" in result.output
    assert "--identifier-case" in result.output


def test_import_map_databricks_json_output(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[
                ImportCatalogResource(
                    name="Finance-Curated",
                    schemas=[ImportSchemaResource(name="Silver Layer")],
                )
            ],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "map-databricks",
            "--config",
            str(snowflake_project / "datamuru.yml"),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mapped_catalogs"] == ["finance_curated"]
    assert "Silver Layer: silver_layer" in payload["mapping_file_text"]


@pytest.mark.parametrize(
    ("option", "value", "context_key"),
    [
        ("identifier_case", "upper", "identifier_case"),
        ("target_cloud", "snowflake", "target_cloud"),
    ],
)
def test_snowflake_to_databricks_mapping_rejects_unsupported_options(
    sample_project,
    option,
    value,
    context_key,
):
    kwargs = {option: value}

    with pytest.raises(ValidationError) as exc_info:
        ImportEngine(sample_project / "datamuru.yml").snowflake_to_databricks_mapping(**kwargs)

    assert exc_info.value.context[context_key] == value


def test_snowflake_to_databricks_mapping_requires_snowflake_source(sample_project, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="databricks-live",
            cloud="azure",
            region="unknown",
        ),
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    with pytest.raises(ValidationError) as exc_info:
        ImportEngine(sample_project / "datamuru.yml").snowflake_to_databricks_mapping()

    assert exc_info.value.context == {"provider": "databricks"}


def test_snowflake_to_databricks_mapping_reports_missing_database(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[ImportCatalogResource(name="AVAILABLE")],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    with pytest.raises(ValidationError) as exc_info:
        ImportEngine(snowflake_project / "datamuru.yml").snowflake_to_databricks_mapping(
            databases=["MISSING"]
        )

    assert exc_info.value.context["missing_databases"] == ["MISSING"]


def test_snowflake_to_databricks_mapping_can_preserve_identifier_case(sample_project, monkeypatch):
    snowflake_project = _configure_snowflake_project(sample_project)
    report = ImportDiscoveryReport(
        provider="snowflake",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="snowflake-live",
            cloud="snowflake",
            region="unknown",
            catalogs=[ImportCatalogResource(name="Finance-Curated")],
        ),
    )
    monkeypatch.setattr(
        SnowflakeProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )

    result = ImportEngine(snowflake_project / "datamuru.yml").snowflake_to_databricks_mapping(
        identifier_case="preserve"
    )

    assert result.mapped_catalogs == ["Finance_Curated"]


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


def test_import_map_snowflake_generates_mapping_draft(sample_project, tmp_path, monkeypatch):
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
                    schemas=[ImportSchemaResource(name="raw"), ImportSchemaResource(name="gold")],
                )
            ],
        ),
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "discover_importable_resources",
        lambda self, project, environment, **kwargs: report,
    )
    output_path = tmp_path / "finance.mapping.yml"

    result = CliRunner().invoke(
        cli,
        [
            "import",
            "map-snowflake",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--catalog",
            "finance_raw",
            "--target-account",
            "analytics-dev",
            "--target-workspace",
            "snowflake-dev",
            "--database-prefix",
            "DM",
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    mapping_text = output_path.read_text(encoding="utf-8")
    assert "provider: databricks" in mapping_text
    assert "account: analytics-dev" in mapping_text
    assert "finance_raw:" in mapping_text
    assert "database: DM_FINANCE_RAW" in mapping_text
    assert "raw: RAW" in mapping_text
    assert "gold: GOLD" in mapping_text


def test_import_map_snowflake_json_output(sample_project, monkeypatch):
    report = ImportDiscoveryReport(
        provider="databricks",
        environment="dev",
        workspace=ImportWorkspaceResource(
            name="alpha-dev",
            cloud="azure",
            region="eastus",
            catalogs=[
                ImportCatalogResource(
                    name="Marketing-Curated",
                    schemas=[ImportSchemaResource(name="Silver Layer")],
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
            "map-snowflake",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--schema-case",
            "lower",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mapped_databases"] == ["marketing_curated"]
    assert "Silver Layer: silver_layer" in payload["mapping_file_text"]


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


def test_import_map_snowflake_help_exposes_mapping_options():
    result = CliRunner().invoke(cli, ["import", "map-snowflake", "--help"])

    assert result.exit_code == 0
    assert "--target-account" in result.output
    assert "--database-prefix" in result.output
    assert "--schema-case" in result.output


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


def test_import_job_checkpoint_accepts_writer_timestamp_round_trip():
    checkpoint = ImportJobCheckpoint.model_validate(
        {
            "version": 1,
            "completed_grant_targets": [
                {"object_type": "catalog", "object_name": "poc_platform_team"}
            ],
            "grants": [],
            "updated_at": "2026-06-22T12:26:32.376988+00:00",
        }
    )

    assert checkpoint.updated_at == "2026-06-22T12:26:32.376988+00:00"
    assert checkpoint.to_dict()["updated_at"] == "2026-06-22T12:26:32.376988+00:00"


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
