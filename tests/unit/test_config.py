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


def test_validate_project_rejects_mismatched_provider_name(sample_project):
    root_path = sample_project / "datamuru.yml"
    root_path.write_text(
        root_path.read_text(encoding="utf-8").replace("provider: databricks", "provider: snowflake", 1),
        encoding="utf-8",
    )

    issues = validate_project(root_path)

    assert any(
        issue.level == "error"
        and issue.path == "provider.name"
        and "must match project.provider" in issue.message
        for issue in issues
    )


def test_validate_project_rejects_duplicate_environments(sample_project):
    root_path = sample_project / "datamuru.yml"
    root_path.write_text(
        root_path.read_text(encoding="utf-8").replace(
            "environments:\n  - name: dev\n    config: ./environments/dev.yml",
            "\n".join(
                [
                    "environments:",
                    "  - name: dev",
                    "    config: ./environments/dev.yml",
                    "  - name: dev",
                    "    config: ./environments/dev-copy.yml",
                ]
            ),
        ),
        encoding="utf-8",
    )

    issues = validate_project(root_path)

    assert any(
        issue.level == "error"
        and issue.path == "environments.1.name"
        and "declared more than once" in issue.message
        for issue in issues
    )


def test_validate_project_rejects_workspace_cloud_mismatch(sample_project):
    workspace_path = sample_project / "workspaces" / "alpha-dev.yml"
    workspace_path.write_text(
        workspace_path.read_text(encoding="utf-8").replace("cloud: azure", "cloud: aws"),
        encoding="utf-8",
    )

    issues = validate_project(sample_project / "datamuru.yml")

    assert any(
        issue.level == "error"
        and issue.path == "alpha-dev.yml.workspace.cloud"
        and "must match root provider.cloud" in issue.message
        for issue in issues
    )


def test_validate_project_rejects_duplicate_catalog_and_schema(sample_project):
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
                "        - raw",
                "    - name: alpha_marketing",
                "      schemas:",
                "        - information_schema",
                "",
            ]
        ),
        encoding="utf-8",
    )

    issues = validate_project(sample_project / "datamuru.yml")

    assert any("Catalog 'alpha_marketing' is declared more than once" in issue.message for issue in issues)
    assert any("Schema 'raw' is declared more than once" in issue.message for issue in issues)
    assert any("information_schema is system-owned" in issue.message for issue in issues)


def test_validate_project_rejects_unknown_rbac_assignment_role(sample_project):
    rbac_path = sample_project / "governance" / "rbac.yml"
    rbac_path.write_text(
        "\n".join(
            [
                "rbac:",
                "  roles:",
                "    - id: reader",
                "      permissions:",
                "        - resource_type: schema",
                "          resource_pattern: '*.gold'",
                "          privilege: SELECT",
                "  assignments:",
                "    - principal: sample-consumers",
                "      type: group",
                "      roles:",
                "        - missing_role",
                "",
            ]
        ),
        encoding="utf-8",
    )

    issues = validate_project(sample_project / "datamuru.yml")

    assert any(
        issue.level == "error"
        and issue.path == "rbac.yml.rbac.assignments.0.roles"
        and "unknown role 'missing_role'" in issue.message
        for issue in issues
    )
