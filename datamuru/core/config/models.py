from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field

from datamuru.modeling import DataMuruModel


class EnvironmentRef(DataMuruModel):
    name: str
    config: str


class Features(DataMuruModel):
    governance: bool = True
    data_mesh: bool = False
    ingestion: bool = False
    modeling: bool = False
    observability: bool = False
    compliance_reporting: bool = False
    multi_workspace: bool = False
    hosted_control_plane: bool = False
    identity_management: bool = False


class StateConfig(DataMuruModel):
    backend: str
    path: str


class ProviderConfig(DataMuruModel):
    name: str
    cloud: str
    config: str


class ProjectConfig(DataMuruModel):
    name: str
    version: str
    description: str
    edition: str
    provider: str


class RootConfig(DataMuruModel):
    project: ProjectConfig
    environments: list[EnvironmentRef]
    default_environment: str
    features: Features
    state: StateConfig
    provider: ProviderConfig
    ai: dict[str, Any] = Field(default_factory=dict)


class WorkspaceConfig(DataMuruModel):
    path: Path
    raw: dict[str, Any]


class GovernanceConfig(DataMuruModel):
    taxonomy: dict[str, Any] | None = None
    rbac: dict[str, Any] | None = None
    masking: dict[str, Any] | None = None


class LoadedProject(DataMuruModel):
    root_path: Path
    config_path: Path
    root: RootConfig
    environment_data: dict[str, Any]
    provider_data: dict[str, Any]
    workspaces: list[WorkspaceConfig]
    governance: GovernanceConfig
