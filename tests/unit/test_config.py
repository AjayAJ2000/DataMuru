from datamuru.core.config import load_project, validate_project


def test_validate_project_has_no_errors(sample_project):
    issues = validate_project(sample_project / "datamuru.yml")
    assert not [issue for issue in issues if issue.level == "error"]


def test_load_project_reads_default_environment(sample_project):
    project = load_project(sample_project / "datamuru.yml")
    assert project.root.project.name == "sample-project"
    assert project.root.default_environment == "dev"


def test_validate_project_rejects_principals_outside_workspace(sample_project):
    workspace_path = sample_project / "workspaces" / "alpha-dev.yml"
    workspace_path.write_text(
        "\n".join(
            [
                "workspace:",
                "  name: alpha-dev",
                "  cloud: azure",
                "  region: eastus2",
                "principals:",
                "  groups:",
                "    - name: misplaced-group",
                "",
            ]
        ),
        encoding="utf-8",
    )

    issues = validate_project(sample_project / "datamuru.yml")

    assert any(
        issue.level == "error"
        and issue.path == "alpha-dev.yml.principals"
        and "nested under the workspace" in issue.message
        for issue in issues
    )


def test_validate_project_rejects_managed_example_email(sample_project):
    root_path = sample_project / "datamuru.yml"
    root_text = root_path.read_text(encoding="utf-8")
    root_text = root_text.replace("edition: open-source", "edition: enterprise")
    root_text = root_text.replace("identity_management: false", "identity_management: true")
    root_path.write_text(root_text, encoding="utf-8")

    workspace_path = sample_project / "workspaces" / "alpha-dev.yml"
    workspace_path.write_text(
        "\n".join(
            [
                "workspace:",
                "  name: alpha-dev",
                "  cloud: azure",
                "  region: eastus2",
                "  principals:",
                "    users:",
                "      - email: analyst@example.com",
                "        lifecycle: managed",
                "",
            ]
        ),
        encoding="utf-8",
    )

    issues = validate_project(root_path)

    assert any(
        issue.level == "error"
        and issue.path == "alpha-dev.yml.workspace.principals.users.0.email"
        and "real account email" in issue.message
        for issue in issues
    )
