from __future__ import annotations

from pathlib import Path

import pytest

from datamuru.bootstrap import ProjectScaffolder


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "sample-project"
    ProjectScaffolder().scaffold(project_root, name="sample-project")
    return project_root
