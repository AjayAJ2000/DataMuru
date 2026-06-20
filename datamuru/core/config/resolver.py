from __future__ import annotations

from pathlib import Path

from datamuru.errors import ValidationError

from .models import (
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
from .parser import load_yaml
from .validator import validate_project


def resolve_environment_name(project: LoadedProject, environment: str | None = None) -> str:
    resolved = environment or project.root.default_environment
    known = {item.name for item in project.root.environments}
    if resolved not in known:
        raise ValidationError(
            description=f"Unknown environment '{resolved}'.",
            context={"requested_environment": resolved, "available_environments": sorted(known)},
        )
    return resolved


def load_project(config_path: str | Path) -> LoadedProject:
    resolved = Path(config_path).resolve()
    issues = validate_project(resolved)
    errors = [issue for issue in issues if issue.level == "error"]
    if errors:
        raise ValidationError(issues=errors)

    root_raw = load_yaml(resolved)
    root = RootConfig(
        project=ProjectConfig.model_validate(root_raw["project"]),
        environments=[EnvironmentRef.model_validate(item) for item in root_raw["environments"]],
        default_environment=root_raw["default_environment"],
        features=Features.model_validate(root_raw["features"]),
        state=StateConfig.model_validate(root_raw["state"]),
        provider=ProviderConfig.model_validate(root_raw["provider"]),
        ai=root_raw.get("ai", {}),
        enterprise=root_raw.get("enterprise", {}),
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
