# Snowflake To Databricks Mapping Draft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a review-only Snowflake-to-Databricks database/schema mapping draft through the Python API and `datamuru import map-databricks` CLI.

**Architecture:** Reuse the provider-neutral Snowflake discovery report, then transform selected databases and schemas into a deterministic migration YAML contract inside `ImportEngine`. Expose the result through the existing core engine, public API, and Click command layers while keeping provider mutation, state, data movement, identities, and grants outside the flow.

**Tech Stack:** Python 3.11+, Pydantic/DataMuruModel, PyYAML, Click, pytest, Ruff, MkDocs Material, GitHub Actions.

---

## File Map

- Modify `datamuru/core/importer/models.py`: add the serialized reverse-mapping result contract.
- Modify `datamuru/core/importer/engine.py`: add source validation, identifier normalization, collision detection, and YAML generation.
- Modify `datamuru/core/engine.py`: delegate the reverse-mapping operation to `ImportEngine`.
- Modify `datamuru/api.py`: expose the public Python API method.
- Modify `datamuru/cli/commands/import_.py`: add `import map-databricks` text/JSON/file output.
- Modify `tests/unit/test_import_adoption.py`: cover mapping behavior, validation, CLI, and file output.
- Create `docs/guides/snowflake-to-databricks.md`: operator workflow and review boundaries.
- Modify `docs/reference/cli.md`: exact command options and output behavior.
- Modify `docs/reference/python-api.md`: public API method.
- Modify `docs/reference/capabilities.md`: canonical partial capability status.
- Modify `docs/operations/milestone-0-5-test-runbook.md`: feature-by-feature local and live tests for both mapping directions.
- Modify `docs/product/roadmap.md`: include the bounded reverse-mapping slice in v0.5.
- Modify `docs/product/github-project-board.md`: include the tracked backlog row.
- Modify `mkdocs.yml`: add the reverse operator guide beside the forward guide.
- Modify `CHANGELOG.md`: add the unreleased capability.
- Modify `docs/superpowers/specs/2026-06-28-snowflake-to-databricks-mapping-design.md`: mark implementation status after all local gates pass.

### Task 1: Reverse Mapping Result Contract

**Files:**
- Modify: `datamuru/core/importer/models.py`
- Modify: `tests/unit/test_import_adoption.py`

- [ ] **Step 1: Write the failing result-model test**

Add imports and a focused serialization test:

```python
from datamuru.core.importer.models import SnowflakeToDatabricksMappingResult


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
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m pytest tests\unit\test_import_adoption.py::test_snowflake_to_databricks_mapping_result_serializes -q --basetemp .datamuru\pytest-map-db-result-red -p no:cacheprovider
```

Expected: collection fails because `SnowflakeToDatabricksMappingResult` does not exist.

- [ ] **Step 3: Add the minimal result model**

Add immediately after `DatabricksToSnowflakeMappingResult`:

```python
class SnowflakeToDatabricksMappingResult(DataMuruModel):
    provider: str
    environment: str
    source_workspace: str
    target_workspace: str
    target_cloud: str
    mapping_file_text: str
    selected_databases: list[str] = Field(default_factory=list)
    mapped_catalogs: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump(mode="python")
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the Task 1 test command. Expected: one passing test.

### Task 2: Snowflake Discovery Transformation

**Files:**
- Modify: `datamuru/core/importer/engine.py`
- Modify: `tests/unit/test_import_adoption.py`

- [ ] **Step 1: Write the failing bounded-mapping test**

Create a Snowflake discovery report and patch the real provider boundary:

```python
def test_import_engine_maps_snowflake_database_to_databricks_catalog(
    snowflake_project, monkeypatch
):
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
```

Use the existing Snowflake project fixture pattern from `test_snowflake_provider.py`; if no reusable fixture exists, create a local helper by copying `sample_project` into `tmp_path` and changing only the provider references.

- [ ] **Step 2: Run the mapping test and verify RED**

Run the single test. Expected: `ImportEngine` has no `snowflake_to_databricks_mapping` method.

- [ ] **Step 3: Implement the minimal mapping method**

Add `import re` with the standard-library imports in `engine.py`, then add the
result-model import and this method beside `databricks_to_snowflake_mapping`:

```python
def snowflake_to_databricks_mapping(
    self,
    *,
    databases: list[str] | None = None,
    target_workspace: str = "databricks-target",
    target_cloud: str = "azure",
    catalog_prefix: str | None = None,
    identifier_case: str = "lower",
    progress: ImportProgressCallback | None = None,
) -> SnowflakeToDatabricksMappingResult:
    if identifier_case not in {"lower", "preserve"}:
        raise ValidationError(
            description="Unsupported Databricks identifier naming mode.",
            context={"identifier_case": identifier_case, "supported_modes": ["lower", "preserve"]},
            suggestion="Use identifier_case lower or preserve.",
        )
    if target_cloud not in {"azure", "aws", "gcp"}:
        raise ValidationError(
            description="Unsupported Databricks target cloud.",
            context={"target_cloud": target_cloud, "supported_clouds": ["azure", "aws", "gcp"]},
            suggestion="Use target_cloud azure, aws, or gcp.",
        )
    report = self.discover(catalogs=databases, progress=progress)
    if report.provider != "snowflake":
        raise ValidationError(
            description="Snowflake-to-Databricks mapping requires a Snowflake source provider.",
            context={"provider": report.provider},
            suggestion="Run this command from a DataMuru project configured with the Snowflake provider.",
        )
    selected_databases = sorted(databases or [catalog.name for catalog in report.workspace.catalogs])
    available_databases = {catalog.name: catalog for catalog in report.workspace.catalogs}
    missing_databases = [name for name in selected_databases if name not in available_databases]
    if missing_databases:
        raise ValidationError(
            description="Requested mapping databases were not found in the Snowflake discovery result.",
            context={
                "requested_databases": selected_databases,
                "missing_databases": missing_databases,
                "available_databases": sorted(available_databases),
            },
        )

    database_mappings: dict[str, dict] = {}
    mapped_catalogs: list[str] = []
    for database_name in selected_databases:
        source = available_databases[database_name]
        target_catalog = self._databricks_identifier(
            f"{catalog_prefix}_{database_name}" if catalog_prefix else database_name,
            identifier_case,
        )
        mapped_catalogs.append(target_catalog)
        database_mappings[database_name] = {
            "catalog": target_catalog,
            "schemas": {
                schema.name: self._databricks_identifier(schema.name, identifier_case)
                for schema in source.schemas
            },
        }

    payload = {
        "migration": {
            "name": f"{self._slug(report.workspace.name)}-to-{self._slug(target_workspace)}",
            "source": {
                "provider": "snowflake",
                "workspace": report.workspace.name,
                "environment": report.environment,
            },
            "target": {
                "provider": "databricks",
                "workspace": target_workspace,
                "cloud": target_cloud,
            },
            "naming": {
                "catalog_prefix": catalog_prefix,
                "identifier_case": identifier_case,
            },
            "mappings": {"databases": database_mappings},
            "review": {
                "status": "draft",
                "notes": [
                    "Review catalog and schema names before implementation.",
                    "This draft does not move data or apply Databricks changes.",
                ],
            },
        }
    }
    return SnowflakeToDatabricksMappingResult(
        provider=report.provider,
        environment=report.environment,
        source_workspace=report.workspace.name,
        target_workspace=target_workspace,
        target_cloud=target_cloud,
        mapping_file_text=yaml.safe_dump(payload, sort_keys=False),
        selected_databases=selected_databases,
        mapped_catalogs=mapped_catalogs,
    )
```

Add the focused helper:

```python
@staticmethod
def _databricks_identifier(value: str, identifier_case: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]+", "_", value)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized.lower() if identifier_case == "lower" else normalized
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Expected: the database/schema transformation test passes.

### Task 3: Naming And Collision Safety

**Files:**
- Modify: `datamuru/core/importer/engine.py`
- Modify: `tests/unit/test_import_adoption.py`

- [ ] **Step 1: Write failing validation tests**

Add parameterized tests for unsupported mode/cloud and explicit tests for:

```python
def test_snowflake_to_databricks_mapping_blocks_catalog_collision(...):
    report = snowflake_report(database_names=["FINANCE-RAW", "FINANCE_RAW"])
    ...
    with pytest.raises(ValidationError) as exc_info:
        engine.snowflake_to_databricks_mapping(identifier_case="lower")
    assert exc_info.value.context["target_identifier"] == "finance_raw"
    assert sorted(exc_info.value.context["source_databases"]) == ["FINANCE-RAW", "FINANCE_RAW"]


def test_snowflake_to_databricks_mapping_blocks_schema_collision(...):
    report = snowflake_report(schema_names=["RAW-ZONE", "RAW_ZONE"])
    ...
    with pytest.raises(ValidationError) as exc_info:
        engine.snowflake_to_databricks_mapping(identifier_case="lower")
    assert exc_info.value.context["target_identifier"] == "raw_zone"
```

Also assert an input containing only punctuation raises `ValidationError` with the source address and does not produce a result.

- [ ] **Step 2: Run validation tests and verify RED**

Expected: collision tests pass through silently or overwrite schema keys, proving safeguards are absent.

- [ ] **Step 3: Add explicit identifier and collision validation**

Change `_databricks_identifier` to raise on an empty result:

```python
if not normalized:
    raise ValidationError(
        description="Source name cannot produce a Databricks identifier.",
        context={"source_name": value},
        suggestion="Rename the source object or select a different mapping scope.",
    )
```

Before constructing the final payload, build reverse indexes for mapped catalogs and mapped schemas. If a target has more than one source, raise:

```python
raise ValidationError(
    description="Snowflake source names collide after Databricks identifier normalization.",
    context={
        "target_identifier": target_identifier,
        "source_databases": sorted(source_names),
    },
    suggestion="Change catalog_prefix, identifier_case, source names, or mapping scope.",
)
```

Use `source_schemas` and include `source_database` for schema collisions.

- [ ] **Step 4: Run all reverse-mapping engine tests and verify GREEN**

Run the new result, mapping, normalization, missing database, wrong provider, mode/cloud, and collision tests together.

### Task 4: Core, Python API, And CLI

**Files:**
- Modify: `datamuru/core/engine.py`
- Modify: `datamuru/api.py`
- Modify: `datamuru/cli/commands/import_.py`
- Modify: `tests/unit/test_import_adoption.py`

- [ ] **Step 1: Write failing API and CLI tests**

Add an API delegation test that patches `ImportEngine.snowflake_to_databricks_mapping` and asserts every option is forwarded. Add CLI tests modeled on `test_import_map_snowflake_generates_mapping_draft`:

```python
def test_import_map_databricks_generates_mapping_draft(snowflake_project, tmp_path, monkeypatch):
    ...
    result = CliRunner().invoke(
        cli,
        [
            "import", "map-databricks",
            "--config", str(snowflake_project / "datamuru.yml"),
            "--database", "FINANCE",
            "--target-workspace", "databricks-dev",
            "--target-cloud", "azure",
            "--catalog-prefix", "sf",
            "--out", str(tmp_path / "finance.mapping.yml"),
        ],
    )
    assert result.exit_code == 0
    mapping_text = (tmp_path / "finance.mapping.yml").read_text(encoding="utf-8")
    assert "provider: snowflake" in mapping_text
    assert "provider: databricks" in mapping_text
    assert "catalog: sf_finance" in mapping_text
```

Add JSON output and help tests requiring `--database`, `--target-workspace`, `--target-cloud`, `--catalog-prefix`, and `--identifier-case`.

- [ ] **Step 2: Run the API/CLI tests and verify RED**

Expected: public methods and `map-databricks` command are missing.

- [ ] **Step 3: Add core and public API delegation**

Add matching methods to `datamuru/core/engine.py` and `datamuru/api.py`:

```python
def import_snowflake_to_databricks_mapping(
    self,
    *,
    databases: list[str] | None = None,
    target_workspace: str = "databricks-target",
    target_cloud: str = "azure",
    catalog_prefix: str | None = None,
    identifier_case: str = "lower",
    progress: ImportProgressCallback | None = None,
):
    return ImportEngine(
        config_path=self.config_path,
        environment=self.environment,
    ).snowflake_to_databricks_mapping(
        databases=databases,
        target_workspace=target_workspace,
        target_cloud=target_cloud,
        catalog_prefix=catalog_prefix,
        identifier_case=identifier_case,
        progress=progress,
    )
```

The public `DataMuru` method delegates to `self.engine` with the same signature.

- [ ] **Step 4: Add the Click command**

Register `@import_group.command("map-databricks")` with the options from the spec. In JSON mode, call the API directly and print `result.to_dict()`. In text mode, wrap the call with `_import_progress("Snowflake to Databricks mapping")`. Write `mapping_file_text` only after the API returns successfully, then print a concise draft summary.

- [ ] **Step 5: Run API/CLI tests and verify GREEN**

Expected: file, JSON, help, and delegation tests pass while existing `map-snowflake` tests remain green.

### Task 5: Public Documentation And Test Runbook

**Files:**
- Create: `docs/guides/snowflake-to-databricks.md`
- Modify: `docs/reference/cli.md`
- Modify: `docs/reference/python-api.md`
- Modify: `docs/reference/capabilities.md`
- Modify: `docs/operations/milestone-0-5-test-runbook.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/product/github-project-board.md`
- Modify: `mkdocs.yml`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/specs/2026-06-28-snowflake-to-databricks-mapping-design.md`

- [ ] **Step 1: Write failing documentation assertions**

Extend `tests/unit/test_documentation.py` to require:

```python
assert "map-databricks" in (repo_root / "docs/reference/cli.md").read_text(encoding="utf-8")
assert "Snowflake to Databricks" in (repo_root / "docs/operations/milestone-0-5-test-runbook.md").read_text(encoding="utf-8")
assert "snowflake-to-databricks.md" in (repo_root / "mkdocs.yml").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run documentation tests and verify RED**

Expected: all three assertions fail because public documentation is absent.

- [ ] **Step 3: Add operator and reference documentation**

Document:

- exact command and Python API signatures;
- database-to-catalog and schema-to-schema mapping;
- naming modes, prefixing, and collision failures;
- draft-only/no-data-movement/no-mutation boundary;
- absence of role, grant, table, and masking migration;
- both live credentials referenced only through environment-variable names;
- redacted aggregate-only live evidence.

Add a runbook section that runs both `map-snowflake` and `map-databricks`, verifies source/target providers and draft status, records only aggregate mapping counts, and includes the existing bug-capture template.

Mark the canonical capability as `Partial`, add the v0.5 roadmap/project-board row, add the guide to MkDocs navigation, add an Unreleased changelog item, and change the design status to `implemented, pending milestone release` only after all local gates pass.

- [ ] **Step 4: Verify documentation GREEN**

Run:

```powershell
python -m pytest tests\unit\test_documentation.py -q --basetemp .datamuru\pytest-map-db-docs -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
```

Expected: documentation tests and strict build pass.

### Task 6: Live Validation, Full Gate, And Deployment

**Files:**
- Generate ignored artifacts only under `.datamuru/snowflake-to-databricks-live/`.
- Update GitHub issue `#89` and private project item `PVTI_lAHOBH-DuM4BbIGVzgxDDDE`.

- [ ] **Step 1: Run redacted live reverse mapping**

Load `SNOWFLAKE_HOST`, `SNOWFLAKE_USERNAME`, and `SNOWFLAKE_TOKEN` from Windows User scope. Use the ignored Snowflake PAT project and call:

```python
result = datamuru.import_snowflake_to_databricks_mapping(
    target_workspace="databricks-live-readonly",
    target_cloud="azure",
    catalog_prefix="sf",
)
payload = yaml.safe_load(result.mapping_file_text)["migration"]
```

Print only mapping success, source/target provider booleans, draft-status boolean, selected database count, and mapped catalog count. Do not print inventory names or mapping text.

- [ ] **Step 2: Re-run the forward live mapping**

Load the three Databricks variables from User scope and run the existing `import_databricks_to_snowflake_mapping`. Print only draft validity and aggregate counts. Expected: both directions produce draft contracts without mutation.

- [ ] **Step 3: Verify token absence**

Search Git-tracked files and the two ignored live-test directories for both resolved token values without printing either value. Expected: zero tracked matches and zero generated-artifact matches.

- [ ] **Step 4: Run the complete local gate**

```powershell
python -m ruff check datamuru tests
python -m pytest -q --basetemp .datamuru\pytest-map-db-final -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
git diff --check
```

Expected: every command exits zero.

- [ ] **Step 5: Commit and push**

```powershell
git add CHANGELOG.md datamuru docs mkdocs.yml tests
git commit -m "Add Snowflake to Databricks mapping draft"
git push origin main
```

- [ ] **Step 6: Verify deployment and close tracking**

Require CI, Documentation, and Documentation Links for the implementation SHA to conclude `success`. Add the commit URL to issue `#89` and the project's Evidence link, move the item to `Done`, and close issue `#89` only after all three workflows are green.
