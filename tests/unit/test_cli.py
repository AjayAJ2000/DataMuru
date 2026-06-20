import json

from click.testing import CliRunner

from datamuru.cli.main import cli
from datamuru.core.config import validate_project


def test_cli_prints_branded_banner_for_human_commands(sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--config", str(sample_project / "datamuru.yml")])

    assert result.exit_code == 0
    assert "DataMuru CLI" in result.output
    assert "Provider-agnostic data infrastructure" in result.output
    assert "Configuration is valid." in result.output


def test_cli_banner_can_be_suppressed_for_automation(sample_project):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--no-banner", "validate", "--config", str(sample_project / "datamuru.yml")],
    )

    assert result.exit_code == 0
    assert "DataMuru CLI" not in result.output
    assert "Configuration is valid." in result.output


def test_cli_banner_is_suppressed_for_json_output(sample_project):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["edition", "show", "--config", str(sample_project / "datamuru.yml"), "--output", "json"],
    )

    assert result.exit_code == 0
    assert "DataMuru CLI" not in result.output
    assert json.loads(result.output)["edition"] == "open-source"


def test_validate_command(sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--config", str(sample_project / "datamuru.yml")])
    assert result.exit_code == 0
    assert "Configuration is valid." in result.output


def test_plan_command_outputs_resource_changes(sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["plan", "--config", str(sample_project / "datamuru.yml")])
    assert result.exit_code == 0
    assert "workspace:alpha-dev" in result.output


def test_init_command_creates_env_based_databricks_project(tmp_path):
    runner = CliRunner()
    output_dir = tmp_path / "generated-project"

    result = runner.invoke(
        cli,
        [
            "init",
            "--name",
            "generated-project",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    provider_config = (output_dir / "providers" / "databricks.yml").read_text(encoding="utf-8")
    workspace_config = (output_dir / "workspaces" / "alpha-dev.yml").read_text(encoding="utf-8")
    assert "host_env: DATABRICKS_HOST" in provider_config
    assert "token_env: DATABRICKS_TOKEN" in provider_config
    assert "sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID" in provider_config
    assert "execution_mode: state-only" in provider_config
    assert "host: https://adb-placeholder" not in provider_config
    assert "dm_alpha_marketing" in workspace_config
    assert (output_dir / ".env.example").exists()
    assert (output_dir / "README.md").exists()
    issues = validate_project(output_dir / "datamuru.yml")
    assert not [issue for issue in issues if issue.level == "error"]


def test_init_command_accepts_live_readonly_execution_mode(tmp_path):
    runner = CliRunner()
    output_dir = tmp_path / "readonly-project"

    result = runner.invoke(
        cli,
        [
            "init",
            "--name",
            "readonly-project",
            "--execution-mode",
            "live-readonly",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    provider_config = (output_dir / "providers" / "databricks.yml").read_text(encoding="utf-8")
    assert "execution_mode: live-readonly" in provider_config


def test_plan_command_reports_unmatched_target(sample_project):
    runner = CliRunner()
    target = "user:not-declared@company.com"
    result = runner.invoke(
        cli,
        ["plan", "--config", str(sample_project / "datamuru.yml"), "--target", target],
    )
    assert result.exit_code == 0
    assert f"No resources matched target '{target}'." in result.output


def test_apply_command_reports_unmatched_target(sample_project):
    runner = CliRunner()
    target = "user:not-declared@company.com"
    result = runner.invoke(
        cli,
        [
            "apply",
            "--config",
            str(sample_project / "datamuru.yml"),
            "--target",
            target,
            "--auto-approve",
        ],
    )
    assert result.exit_code == 0
    assert f"Target '{target}' matched nothing; apply skipped." in result.output
    assert "Applied 0 changes." not in result.output


def test_saved_plan_apply_flow(sample_project):
    runner = CliRunner()
    plan_path = sample_project / "saved-plan.dm"

    plan_result = runner.invoke(
        cli,
        ["plan", "--config", str(sample_project / "datamuru.yml"), "--out", str(plan_path)],
    )
    assert plan_result.exit_code == 0
    assert plan_path.exists()
    saved_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert saved_plan["metadata"]["schema_version"] == "datamuru.saved_plan.v1"
    assert saved_plan["metadata"]["environment"] == "dev"
    assert saved_plan["metadata"]["target"] is None
    assert saved_plan["plan"]["environment"] == "dev"

    apply_result = runner.invoke(
        cli,
        ["apply", "--config", str(sample_project / "datamuru.yml"), "--plan", str(plan_path), "--auto-approve"],
    )
    assert apply_result.exit_code == 0
    assert "Applied" in apply_result.output


def test_saved_plan_apply_rejects_stale_config(sample_project):
    runner = CliRunner()
    config_path = sample_project / "datamuru.yml"
    plan_path = sample_project / "saved-plan.dm"

    plan_result = runner.invoke(
        cli,
        ["plan", "--config", str(config_path), "--out", str(plan_path)],
    )
    assert plan_result.exit_code == 0

    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'description: "Bootstrap DataMuru project"',
            'description: "Changed after saved plan"',
        ),
        encoding="utf-8",
    )

    apply_result = runner.invoke(
        cli,
        ["apply", "--config", str(config_path), "--plan", str(plan_path), "--auto-approve"],
    )
    assert apply_result.exit_code == 1
    assert "DMR-PLAN-1001" in apply_result.output
    assert "Saved plan is stale" in apply_result.output


def test_saved_plan_apply_rejects_legacy_plan_shape(sample_project):
    runner = CliRunner()
    plan_path = sample_project / "legacy-plan.json"
    plan_path.write_text(json.dumps({"environment": "dev", "changes": []}), encoding="utf-8")

    result = runner.invoke(
        cli,
        ["apply", "--config", str(sample_project / "datamuru.yml"), "--plan", str(plan_path), "--auto-approve"],
    )
    assert result.exit_code == 1
    assert "DMR-PLAN-1001" in result.output
    assert "expected DataMuru plan contract" in result.output


def test_edition_show_command(sample_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["edition", "show", "--config", str(sample_project / "datamuru.yml")])
    assert result.exit_code == 0
    assert "Edition: open-source" in result.output


def test_doctor_command_reports_provider_setup(sample_project, monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-value")
    provider_path = sample_project / "providers" / "databricks.yml"
    provider_path.write_text(
        "\n".join(
            [
                "provider:",
                "  cloud: azure",
                "  connect_timeout_seconds: 1",
                "  credential_mode: personal-access-token",
                "  execution_mode: state-only",
                "  auth_type: pat",
                "  token_env: DATABRICKS_TOKEN",
                "  host: https://adb-test.azuredatabricks.net",
                "",
            ]
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", "--config", str(sample_project / "datamuru.yml")])
    assert result.exit_code == 0
    assert "provider.host" in result.output
