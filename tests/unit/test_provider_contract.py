from datamuru.core.config import load_project
from datamuru.errors import ProviderError
from datamuru.providers.factory import load_provider


def test_provider_contract_surface(sample_project):
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    assert provider.authenticate({})
    resources = provider.build_desired_resources(project)
    resource_types = {resource.resource_type for resource in resources}
    assert {"workspace", "catalog", "schema"}.issubset(resource_types)


def test_provider_observes_live_state_when_enabled(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-readonly",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    workspace_path = sample_project / "workspaces" / "alpha-dev.yml"
    workspace_path.write_text(
        "\n".join(
            [
                "workspace:",
                "  name: alpha-dev",
                "  cloud: azure",
                "  region: eastus2",
                "  catalogs:",
                "    - name: alpha_marketing",
                "      schemas:",
                "        - raw",
                "        - bronze",
                "  principals:",
                "    groups:",
                "      - data-consumers",
                "",
            ]
        ),
        encoding="utf-8",
    )
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    monkeypatch.setattr(provider.client, "probe_workspace", lambda: type("Probe", (), {"ok": True})())
    monkeypatch.setattr(provider.client, "list_groups", lambda: ["data-consumers"])
    monkeypatch.setattr(provider.client, "list_catalogs", lambda: ["alpha_marketing"])
    monkeypatch.setattr(provider.client, "list_schemas", lambda catalog_name: ["raw", "bronze"])

    observed = provider.observe_current_state(project, "dev")
    assert "workspace:alpha-dev" in observed.resources
    assert "group:data-consumers" not in observed.resources
    assert "catalog:alpha_marketing" in observed.resources
    assert "schema:alpha_marketing.raw" in observed.resources


def test_provider_observe_state_ignores_system_schemas(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-readonly",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    monkeypatch.setattr(provider.client, "probe_workspace", lambda: type("Probe", (), {"ok": True})())
    monkeypatch.setattr(provider.client, "list_groups", lambda: [])
    monkeypatch.setattr(provider.client, "list_catalogs", lambda: ["dm_alpha_marketing"])
    monkeypatch.setattr(provider.client, "list_schemas", lambda catalog_name: ["default", "information_schema", "raw"])

    observed = provider.observe_current_state(project, "dev")
    assert "schema:dm_alpha_marketing.raw" in observed.resources
    assert "schema:dm_alpha_marketing.default" not in observed.resources
    assert "schema:dm_alpha_marketing.information_schema" not in observed.resources


def test_provider_observes_live_permission_bindings(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-readonly",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "  sql_warehouse_id: warehouse-123",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    monkeypatch.setattr(provider.client, "probe_workspace", lambda: type("Probe", (), {"ok": True})())
    monkeypatch.setattr(provider.client, "list_groups", lambda: [])
    monkeypatch.setattr(provider.client, "list_catalogs", lambda: ["dm_alpha_marketing"])
    monkeypatch.setattr(provider.client, "list_schemas", lambda catalog_name: ["raw", "bronze", "silver", "gold"])
    monkeypatch.setattr(
        provider.client,
        "show_grants",
        lambda **kwargs: [
            {
                "principal": "sample-consumers",
                "privilege": "SELECT",
                "securable_type": "schema",
                "securable_name": "dm_alpha_marketing.gold",
            }
        ],
    )

    observed = provider.observe_current_state(project, "dev")
    binding = observed.resources["permission_binding:sample-consumers:data_consumer"]
    assert binding.attributes["principal"] == "sample-consumers"
    assert binding.attributes["permissions"] == [
        {
            "resource_type": "schema",
            "resource_pattern": "*.gold",
            "privilege": "SELECT",
        }
    ]


def test_provider_live_apply_creates_catalog_and_schema(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-apply",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    created: list[tuple[str, str]] = []
    monkeypatch.setattr(
        provider.client,
        "create_catalog_with_default_storage",
        lambda name: created.append(("catalog", name)) or {},
    )
    monkeypatch.setattr(
        provider.client,
        "create_schema",
        lambda catalog_name, schema_name, managed_location=None: created.append(
            ("schema", f"{catalog_name}.{schema_name}")
        )
        or {},
    )

    resources = provider.build_desired_resources(project)
    catalog = next(resource for resource in resources if resource.resource_type == "catalog")
    schema = next(resource for resource in resources if resource.resource_type == "schema")
    provider.apply_resource(catalog)
    provider.apply_resource(schema)

    assert ("catalog", "dm_alpha_marketing") in created
    assert ("schema", "dm_alpha_marketing.raw") in created


def test_provider_live_apply_passes_managed_locations(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    workspace_path = sample_project / "workspaces" / "alpha-dev.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-apply",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    workspace_path.write_text(
        "\n".join(
            [
                "workspace:",
                "  name: alpha-dev",
                "  cloud: azure",
                "  region: eastus2",
                "  catalogs:",
                "    - name: alpha_marketing",
                "      managed_location: abfss://catalog-root@datamuru.dfs.core.windows.net/alpha_marketing",
                "      schemas:",
                "        - name: raw",
                "          managed_location: abfss://schema-root@datamuru.dfs.core.windows.net/alpha_marketing/raw",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    captured: dict[str, tuple[str, str | None]] = {}
    monkeypatch.setattr(
        provider.client,
        "create_catalog",
        lambda name, managed_location=None: captured.__setitem__("catalog", (name, managed_location)) or {},
    )
    monkeypatch.setattr(
        provider.client,
        "create_schema",
        lambda catalog_name, schema_name, managed_location=None: captured.__setitem__(
            "schema",
            (f"{catalog_name}.{schema_name}", managed_location),
        )
        or {},
    )

    resources = provider.build_desired_resources(project)
    catalog = next(resource for resource in resources if resource.resource_type == "catalog")
    schema = next(resource for resource in resources if resource.resource_type == "schema")
    provider.apply_resource(catalog)
    provider.apply_resource(schema)

    assert captured["catalog"][1] == "abfss://catalog-root@datamuru.dfs.core.windows.net/alpha_marketing"
    assert captured["schema"][1] == "abfss://schema-root@datamuru.dfs.core.windows.net/alpha_marketing/raw"


def test_provider_live_apply_blocks_unmanaged_group_mutation(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: live-apply",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    project = load_project(sample_project / "datamuru.yml")
    provider = load_provider(project)
    from datamuru.core.plan.models import ResourceDescriptor

    group = ResourceDescriptor(resource_type="group", name="data-consumers", attributes={"workspace": "alpha-dev"})

    try:
        provider.apply_resource(group)
    except ProviderError as exc:
        assert "enterprise identity management" in exc.description.lower()
    else:  # pragma: no cover
        raise AssertionError("Expected ProviderError for unmanaged live group mutation")
