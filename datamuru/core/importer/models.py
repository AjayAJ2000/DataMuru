from __future__ import annotations

from pydantic import Field

from datamuru.modeling import DataMuruModel


class ImportSchemaResource(DataMuruModel):
    name: str


class ImportCatalogResource(DataMuruModel):
    name: str
    schemas: list[ImportSchemaResource] = Field(default_factory=list)


class ImportWorkspaceResource(DataMuruModel):
    name: str
    cloud: str
    region: str
    catalogs: list[ImportCatalogResource] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)


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
    workspace_file_text: str
    selected_catalogs: list[str] = Field(default_factory=list)
    included_groups: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump(mode="python")
