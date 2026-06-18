from __future__ import annotations

from datamuru.core.config import load_project, validate_project
from datamuru.providers.factory import load_provider


def test_snowflake_provider_scaffold_plans_state_only_resources(sample_project):
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
                "  execution_mode: state-only",
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

    issues = validate_project(root)
    project = load_project(root)
    provider = load_provider(project)
    resources = provider.build_desired_resources(project)

    assert not [issue for issue in issues if issue.level == "error"]
    assert provider.__class__.__name__ == "SnowflakeProvider"
    assert any(resource.address == "catalog:dm_alpha_marketing" for resource in resources)
