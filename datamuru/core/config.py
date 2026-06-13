from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from datamuru.core.models import (
    EnvironmentRef,
    Features,
    GovernanceConfig,
    LoadedProject,
    ProjectConfig,
    ProviderConfig,
    RootConfig,
    StateConfig,
    WorkspaceConfig,
)
from datamuru.core.schema import SchemaValidator
from datamuru.errors import ConfigError, ValidationError
from datamuru.types import ValidationIssue

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
        raise ConfigError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Expected mapping at root of {path}")
    return _interpolate(data)


def validate_project(config_path: Path) -> list[ValidationIssue]:
    validator = SchemaValidator()
    root_raw = load_yaml(config_path)
    issues = validator.validate_root(root_raw)
    if issues:
        return issues

    project_root = config_path.parent
    for environment in root_raw.get("environments", []):
        env_path = project_root / environment["config"]
        if not env_path.exists():
            issues.append(ValidationIssue("error", f"environments.{environment['name']}", f"Missing environment file: {env_path}"))

    provider_path = project_root / root_raw["provider"]["config"]
    if not provider_path.exists():
        issues.append(ValidationIssue("error", "provider.config", f"Missing provider config file: {provider_path}"))

    for workspace_path in sorted((project_root / "workspaces").glob("*.yml")):
        issues.extend(validator.validate_workspace(load_yaml(workspace_path), workspace_path.name))

    taxonomy_path = project_root / "governance" / "taxonomy.yml"
    if taxonomy_path.exists():
        issues.extend(validator.validate_taxonomy(load_yaml(taxonomy_path), taxonomy_path.name))
    rbac_path = project_root / "governance" / "rbac.yml"
    if rbac_path.exists():
        issues.extend(validator.validate_rbac(load_yaml(rbac_path), rbac_path.name))
    return issues


def load_project(config_path: str | Path) -> LoadedProject:
    resolved = Path(config_path).resolve()
    issues = validate_project(resolved)
    errors = [issue for issue in issues if issue.level == "error"]
    if errors:
        rendered = "; ".join(f"{issue.path}: {issue.message}" for issue in errors)
        raise ValidationError(rendered)

    root_raw = load_yaml(resolved)
    root = RootConfig(
        project=ProjectConfig(**root_raw["project"]),
        environments=[EnvironmentRef(**item) for item in root_raw["environments"]],
        default_environment=root_raw["default_environment"],
        features=Features(**root_raw["features"]),
        state=StateConfig(**root_raw["state"]),
        provider=ProviderConfig(**root_raw["provider"]),
        ai=root_raw.get("ai", {}),
    )

    project_root = resolved.parent
    default_env = next(item for item in root.environments if item.name == root.default_environment)
    environment_data = load_yaml(project_root / default_env.config)
    provider_data = load_yaml(project_root / root.provider.config)
    workspaces = [
        WorkspaceConfig(path=workspace_path, raw=load_yaml(workspace_path))
        for workspace_path in sorted((project_root / "workspaces").glob("*.yml"))
    ]
    governance = GovernanceConfig()
    taxonomy_path = project_root / "governance" / "taxonomy.yml"
    if taxonomy_path.exists():
        governance.taxonomy = load_yaml(taxonomy_path)
    rbac_path = project_root / "governance" / "rbac.yml"
    if rbac_path.exists():
        governance.rbac = load_yaml(rbac_path)
    masking_path = project_root / "governance" / "masking.yml"
    if masking_path.exists():
        governance.masking = load_yaml(masking_path)

    return LoadedProject(
        root_path=project_root,
        config_path=resolved,
        root=root,
        environment_data=environment_data,
        provider_data=provider_data,
        workspaces=workspaces,
        governance=governance,
    )
