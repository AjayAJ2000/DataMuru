from datamuru.api import DataMuru
from datamuru.core.apply.executor import PlanExecutor
from datamuru.core.apply.models import ApplyResult
from datamuru.core.plan.models import Plan, PlanChange, ResourceDescriptor
from datamuru.core.state.backends.local import LocalStateBackend
from datamuru.core.state.models import StateSnapshot


def test_apply_makes_plan_idempotent(sample_project):
    dm = DataMuru(sample_project / "datamuru.yml")
    initial_plan = dm.plan()
    assert any(change.action == "create" for change in initial_plan.changes)

    result = dm.apply()
    assert result.success

    second_plan = dm.plan()
    assert not any(change.action in {"create", "update", "destroy"} for change in second_plan.changes)


def test_live_readonly_plan_reconciles_observed_workspace_state(sample_project, monkeypatch):
    provider_path = sample_project / "providers" / "databricks.yml"
    workspace_path = sample_project / "workspaces" / "alpha-dev.yml"
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
                "  principals:",
                "    groups:",
                "      - data-consumers",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")

    from datamuru.core.plan.models import ResourceDescriptor
    from datamuru.core.plan.renderer import fingerprint
    from datamuru.core.state.models import StateResourceRecord, StateSnapshot
    from datamuru.providers.databricks.provider import DatabricksProvider

    workspace = ResourceDescriptor(
        resource_type="workspace",
        name="alpha-dev",
        attributes={"cloud": "azure", "region": "eastus2", "tier": None},
    )
    catalog = ResourceDescriptor(
        resource_type="catalog",
        name="alpha_marketing",
        attributes={"workspace": "alpha-dev"},
    )
    schema = ResourceDescriptor(
        resource_type="schema",
        name="alpha_marketing.raw",
        attributes={"workspace": "alpha-dev", "catalog": "alpha_marketing"},
    )
    monkeypatch.setattr(
        DatabricksProvider,
        "observe_current_state",
        lambda self, project, environment: StateSnapshot(
            resources={
                workspace.address: StateResourceRecord(
                    fingerprint=fingerprint(workspace),
                    attributes=workspace.attributes,
                ),
                catalog.address: StateResourceRecord(
                    fingerprint=fingerprint(catalog),
                    attributes=catalog.attributes,
                ),
                schema.address: StateResourceRecord(
                    fingerprint=fingerprint(schema),
                    attributes=schema.attributes,
                ),
            }
        ),
    )

    dm = DataMuru(sample_project / "datamuru.yml")
    plan = dm.plan()
    indexed = {change.resource.address: change.action for change in plan.changes}
    assert indexed["workspace:alpha-dev"] == "noop"
    assert indexed["catalog:alpha_marketing"] == "noop"
    assert indexed["schema:alpha_marketing.raw"] == "noop"
    assert "group:data-consumers" not in indexed


def test_apply_skips_schema_when_parent_catalog_failed(tmp_path):
    state_backend = LocalStateBackend(tmp_path / "state.json")

    class FailingProvider:
        def apply_resource(self, resource):
            if resource.resource_type == "catalog":
                raise RuntimeError("catalog failure")
            return {}

        def destroy_resource(self, resource):
            return True

    catalog = ResourceDescriptor(resource_type="catalog", name="alpha", attributes={})
    schema = ResourceDescriptor(
        resource_type="schema",
        name="alpha.raw",
        attributes={"catalog": "alpha"},
    )
    plan = Plan(
        environment="dev",
        changes=[
            PlanChange(action="create", resource=catalog, reason="missing"),
            PlanChange(action="create", resource=schema, reason="missing"),
        ],
    )

    result: ApplyResult = PlanExecutor().execute(plan=plan, provider=FailingProvider(), state_backend=state_backend)
    reasons = {failure.resource: failure.reason for failure in result.failures}
    assert not result.success
    assert "catalog:alpha" in reasons
    assert reasons["schema:alpha.raw"] == "Skipped because parent catalog 'alpha' failed earlier in this apply."


def test_live_plan_marks_permission_binding_update_when_live_grants_are_missing(sample_project, monkeypatch):
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

    from datamuru.core.plan.models import ResourceDescriptor
    from datamuru.core.plan.renderer import fingerprint
    from datamuru.core.state.models import StateResourceRecord, StateSnapshot
    from datamuru.providers.databricks.provider import DatabricksProvider

    workspace = ResourceDescriptor(
        resource_type="workspace",
        name="alpha-dev",
        attributes={"cloud": "azure", "region": "eastus2", "tier": None},
    )
    catalog = ResourceDescriptor(
        resource_type="catalog",
        name="alpha_marketing",
        attributes={"workspace": "alpha-dev"},
    )
    schema = ResourceDescriptor(
        resource_type="schema",
        name="alpha_marketing.gold",
        attributes={"workspace": "alpha-dev", "catalog": "alpha_marketing"},
    )
    binding = ResourceDescriptor(
        resource_type="permission_binding",
        name="sample-consumers:data_consumer",
        attributes={
            "principal": "sample-consumers",
            "principal_type": "group",
            "role": "data_consumer",
            "domains": ["alpha_marketing"],
            "inherits": [],
            "permissions": [],
        },
    )

    monkeypatch.setattr(
        DatabricksProvider,
        "observe_current_state",
        lambda self, project, environment: StateSnapshot(
            resources={
                workspace.address: StateResourceRecord(
                    fingerprint=fingerprint(workspace),
                    attributes=workspace.attributes,
                ),
                catalog.address: StateResourceRecord(
                    fingerprint=fingerprint(catalog),
                    attributes=catalog.attributes,
                ),
                schema.address: StateResourceRecord(
                    fingerprint=fingerprint(schema),
                    attributes=schema.attributes,
                ),
                binding.address: StateResourceRecord(
                    fingerprint=fingerprint(binding),
                    attributes=binding.attributes,
                ),
            }
        ),
    )

    dm = DataMuru(sample_project / "datamuru.yml")
    plan = dm.plan(target="permission_binding:sample-consumers:data_consumer")
    assert len(plan.changes) == 1
    change = plan.changes[0]
    assert change.action == "update"
    assert change.resource.address == "permission_binding:sample-consumers:data_consumer"


def test_catalog_target_includes_only_its_schema_children():
    desired = [
        ResourceDescriptor(resource_type="catalog", name="sales", attributes={}),
        ResourceDescriptor(resource_type="schema", name="sales.raw", attributes={"catalog": "sales"}),
        ResourceDescriptor(resource_type="catalog", name="sales_archive", attributes={}),
        ResourceDescriptor(
            resource_type="schema",
            name="sales_archive.raw",
            attributes={"catalog": "sales_archive"},
        ),
    ]

    from datamuru.core.plan import build_plan

    plan = build_plan(
        environment="dev",
        desired_resources=desired,
        current_state=StateSnapshot(),
        target="catalog:sales",
    )

    assert {change.resource.address for change in plan.changes} == {
        "catalog:sales",
        "schema:sales.raw",
    }


def test_group_target_includes_only_its_memberships():
    desired = [
        ResourceDescriptor(resource_type="group", name="data", attributes={}),
        ResourceDescriptor(
            resource_type="group_membership",
            name="data:user:user@example.com",
            attributes={"group": "data"},
        ),
        ResourceDescriptor(resource_type="group", name="data-admins", attributes={}),
        ResourceDescriptor(
            resource_type="group_membership",
            name="data-admins:user:admin@example.com",
            attributes={"group": "data-admins"},
        ),
    ]

    from datamuru.core.plan import build_plan

    plan = build_plan(
        environment="dev",
        desired_resources=desired,
        current_state=StateSnapshot(),
        target="group:data",
    )

    assert {change.resource.address for change in plan.changes} == {
        "group:data",
        "group_membership:data:user:user@example.com",
    }


def test_exact_identity_target_does_not_match_undeclared_similar_resources():
    desired = [
        ResourceDescriptor(resource_type="user", name="analyst-team@example.com", attributes={}),
    ]

    from datamuru.core.plan import build_plan

    plan = build_plan(
        environment="dev",
        desired_resources=desired,
        current_state=StateSnapshot(),
        target="user:analyst@example.com",
    )

    assert not plan.changes
