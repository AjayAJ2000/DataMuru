from __future__ import annotations

from abc import ABC, abstractmethod

from datamuru.core.importer.models import ImportProgressCallback
from datamuru.core.state.models import StateSnapshot
from datamuru.types import DoctorReport, ResourceDescriptor


class DataMuruProvider(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict) -> bool: ...

    @abstractmethod
    def build_desired_resources(self, project) -> list[ResourceDescriptor]: ...

    @abstractmethod
    def apply_resource(self, resource: ResourceDescriptor) -> dict: ...

    @abstractmethod
    def destroy_resource(self, resource: ResourceDescriptor) -> bool: ...

    @abstractmethod
    def get_resource_types(self) -> list[str]: ...

    @abstractmethod
    def doctor(self, project, environment: str) -> DoctorReport: ...

    @abstractmethod
    def observe_current_state(self, project, environment: str) -> StateSnapshot: ...

    @abstractmethod
    def discover_importable_resources(
        self,
        project,
        environment: str,
        *,
        include_system: bool = False,
        include_identities: bool = False,
        include_grants: bool = False,
        catalogs: list[str] | None = None,
        grant_scope: str = "catalog",
        max_grant_objects: int | None = 500,
        grant_object_budgets: dict[str, int] | None = None,
        progress: ImportProgressCallback | None = None,
    ): ...
