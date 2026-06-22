from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_repository_root_does_not_track_generated_project_scaffold():
    generated_files = [
        REPOSITORY_ROOT / "datamuru.yml",
        REPOSITORY_ROOT / "environments" / "dev.yml",
        REPOSITORY_ROOT / "providers" / "databricks.yml",
        REPOSITORY_ROOT / "workspaces" / "alpha-dev.yml",
        REPOSITORY_ROOT / "governance" / "masking.yml",
        REPOSITORY_ROOT / "governance" / "rbac.yml",
        REPOSITORY_ROOT / "governance" / "taxonomy.yml",
    ]

    assert [path.relative_to(REPOSITORY_ROOT).as_posix() for path in generated_files if path.exists()] == []


def test_minimal_example_project_remains_available():
    example_root = REPOSITORY_ROOT / "examples" / "minimal"

    assert (example_root / "datamuru.yml").is_file()
    assert (example_root / "environments" / "dev.yml").is_file()
    assert (example_root / "providers" / "databricks.yml").is_file()
    assert (example_root / "workspaces" / "example-dev.yml").is_file()
    assert (example_root / "governance" / "rbac.yml").is_file()
