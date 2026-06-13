from pathlib import Path

from datamuru.core.config import validate_project


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_minimal_example_is_valid():
    issues = validate_project(REPOSITORY_ROOT / "examples" / "minimal" / "datamuru.yml")
    assert not [issue for issue in issues if issue.level in {"error", "warning"}]
