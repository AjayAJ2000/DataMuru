from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from datamuru.errors import ConfigLoadError

ENV_PATTERN = re.compile(r"\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}")


def _interpolate(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _interpolate(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_interpolate(item) for item in value]
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigLoadError(
            description=f"Configuration file not found: {path}",
            context={"path": str(path)},
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - depends on malformed input
        raise ConfigLoadError(
            description=f"YAML parsing failed for {path}.",
            context={"path": str(path), "yaml_error": str(exc)},
        ) from exc
    if not isinstance(data, dict):
        raise ConfigLoadError(
            description=f"Expected mapping at root of {path}.",
            context={"path": str(path)},
        )
    return _interpolate(data)
