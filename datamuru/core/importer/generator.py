from __future__ import annotations

from pathlib import Path

from .engine import ImportEngine


def generate_import_config(
    config_path: str | Path,
    *,
    environment: str | None = None,
    catalogs: list[str] | None = None,
    include_groups: bool = False,
    include_system: bool = False,
):
    return ImportEngine(config_path=config_path, environment=environment).generate(
        catalogs=catalogs,
        include_groups=include_groups,
        include_system=include_system,
    )
