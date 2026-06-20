from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import Field

from datamuru.modeling import DataMuruModel

ImportProgressCallback = Callable[[dict[str, Any]], None]


class ImportProgressEvent(DataMuruModel):
    message: str
    stage: str | None = None
    total: int | None = None
    completed: int | None = None
    advance: int | None = None
    object_type: str | None = None
    object_name: str | None = None
    checkpoint_path: str | None = None
    checkpoint_update: dict[str, Any] | None = None


class ImportSchemaResource(DataMuruModel):
    name: str


class ImportCatalogResource(DataMuruModel):
    name: str
    schemas: list[ImportSchemaResource] = Field(default_factory=list)


class ImportUserResource(DataMuruModel):
    email: str
    display_name: str | None = None


class ImportGroupResource(DataMuruModel):
    name: str
    members: dict[str, list[str]] = Field(default_factory=dict)


class ImportServicePrincipalResource(DataMuruModel):
    name: str
    application_id: str | None = None


class ImportGrantResource(DataMuruModel):
    principal: str
    privilege: str
    securable_type: str
    securable_name: str


class ImportGrantTarget(DataMuruModel):
    object_type: str
    object_name: str


class ImportJobCheckpoint(DataMuruModel):
    version: int = 1
    provider: str | None = None
    environment: str | None = None
    completed_grant_targets: list[ImportGrantTarget] = Field(default_factory=list)
    grants: list[ImportGrantResource] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump(mode="python")


class ImportWorkspaceResource(DataMuruModel):
    name: str
    cloud: str
    region: str
    catalogs: list[ImportCatalogResource] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    users: list[ImportUserResource] = Field(default_factory=list)
    service_principals: list[ImportServicePrincipalResource] = Field(default_factory=list)
    group_details: list[ImportGroupResource] = Field(default_factory=list)
    grants: list[ImportGrantResource] = Field(default_factory=list)


class ImportDiscoveryReport(DataMuruModel):
    provider: str
    environment: str
    workspace: ImportWorkspaceResource
    include_system: bool = False

    def to_dict(self) -> dict:
        return self.model_dump(mode="python")


class ImportGenerationResult(DataMuruModel):
    provider: str
    environment: str
    workspace_name: str
    workspace_file_text: str
    rbac_file_text: str | None = None
    taxonomy_file_text: str | None = None
    masking_file_text: str | None = None
    selected_catalogs: list[str] = Field(default_factory=list)
    included_groups: list[str] = Field(default_factory=list)
    included_users: list[str] = Field(default_factory=list)
    included_service_principals: list[str] = Field(default_factory=list)
    included_grants: int = 0
    suite_files: dict[str, str] = Field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.model_dump(mode="python")


class DatabricksToSnowflakeMappingResult(DataMuruModel):
    provider: str
    environment: str
    source_workspace: str
    target_account: str
    mapping_file_text: str
    selected_catalogs: list[str] = Field(default_factory=list)
    mapped_databases: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump(mode="python")


class ImportAdoptionConflict(DataMuruModel):
    address: str
    reason: str
    desired_fingerprint: str
    actual_fingerprint: str | None = None


class ImportAdoptionResult(DataMuruModel):
    provider: str
    environment: str
    targets: list[str] = Field(default_factory=list)
    candidates: list[str] = Field(default_factory=list)
    adopted: list[str] = Field(default_factory=list)
    already_managed: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    conflicts: list[ImportAdoptionConflict] = Field(default_factory=list)
    committed: bool = False

    @property
    def ready(self) -> bool:
        return bool(self.candidates or self.already_managed) and not self.missing and not self.conflicts

    def to_dict(self) -> dict:
        payload = self.model_dump(mode="python")
        payload["ready"] = self.ready
        return payload
