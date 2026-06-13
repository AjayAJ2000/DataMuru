import re
from pathlib import Path

import datamuru


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_version_matches_package_metadata():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package_version = re.search(
        r'(?ms)^\[project\].*?^version\s*=\s*"([^"]+)"',
        pyproject,
    )

    assert package_version is not None
    assert datamuru.__version__ == package_version.group(1)
