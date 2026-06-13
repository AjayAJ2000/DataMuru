from __future__ import annotations

from pathlib import Path

from .engine import ImportEngine


def discover_resources(config_path: str | Path, *, environment: str | None = None, include_system: bool = False):
    return ImportEngine(config_path=config_path, environment=environment).discover(include_system=include_system)
