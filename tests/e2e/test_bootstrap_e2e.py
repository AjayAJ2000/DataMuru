from click.testing import CliRunner

from datamuru.cli.main import cli


def test_init_validate_plan_apply_destroy(tmp_path):
    target = tmp_path / "new-project"
    runner = CliRunner()

    init_result = runner.invoke(cli, ["init", "--name", "new-project", "--output-dir", str(target)])
    assert init_result.exit_code == 0

    config_path = target / "datamuru.yml"
    validate_result = runner.invoke(cli, ["validate", "--config", str(config_path)])
    assert validate_result.exit_code == 0

    plan_result = runner.invoke(cli, ["plan", "--config", str(config_path)])
    assert plan_result.exit_code == 0

    apply_result = runner.invoke(cli, ["apply", "--config", str(config_path), "--auto-approve"])
    assert apply_result.exit_code == 0

    destroy_result = runner.invoke(cli, ["destroy", "--config", str(config_path), "--confirm-destroy"])
    assert destroy_result.exit_code == 0
