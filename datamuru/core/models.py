from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EnvironmentRef:
    name: str
    config: str


@dataclass(slots=True)
class Features:
    governance: bool = True
    data_mesh: bool = False
    ingestion: bool = False
    modeling: bool = False
    observability: bool = False
    compliance_reporting: bool = False
    multi_workspace: bool = False
    hosted_control_plane: bool = False


@dataclass(slots=True)
class StateConfig:
    backend: str
    path: str


@dataclass(slots=True)
class ProviderConfig:
    name: str
    cloud: str
    config: str


@dataclass(slots=True)
class ProjectConfig:
    name: str
    version: str
    description: str
    edition: str
    provider: str


@dataclass(slots=True)
class RootConfig:
    project: ProjectConfig
    environments: list[EnvironmentRef]
    default_environment: str
    features: Features
    state: StateConfig
    provider: ProviderConfig
    ai: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkspaceConfig:
    path: Path
    raw: dict[str, Any]


@dataclass(slots=True)
class GovernanceConfig:
    taxonomy: dict[str, Any] | None = None
    rbac: dict[str, Any] | None = None
    masking: dict[str, Any] | None = None


@dataclass(slots=True)
class LoadedProject:
    root_path: Path
    config_path: Path
    root: RootConfig
    environment_data: dict[str, Any]
    provider_data: dict[str, Any]
    workspaces: list[WorkspaceConfig]
    governance: GovernanceConfig
