from __future__ import annotations

from pathlib import Path

from datamuru.core.engine import DataMuruEngine
from datamuru.core.importer.models import ImportProgressCallback


class DataMuru:
    def __init__(self, config_path: str | Path, environment: str | None = None) -> None:
        self.engine = DataMuruEngine(config_path=config_path, environment=environment)

    def validate(self):
        return self.engine.validate()

    def plan(self, target: str | None = None):
        return self.engine.plan(target=target)

    def apply(self, target: str | None = None):
        return self.engine.apply(target=target)

    def apply_saved_plan(self, plan_path: str | Path):
        return self.engine.apply_saved_plan(plan_path)

    def destroy(self, target: str | None = None):
        return self.engine.destroy(target=target)

    def save_plan(self, output_path: str | Path, target: str | None = None):
        return self.engine.save_plan(output_path=output_path, target=target)

    def edition_summary(self):
        return self.engine.edition_summary()

    def doctor(self):
        return self.engine.doctor()

    def import_discover(
        self,
        include_system: bool = False,
        include_identities: bool = False,
        include_grants: bool = False,
        catalogs: list[str] | None = None,
        grant_scope: str = "catalog",
        max_grant_objects: int | None = 500,
        progress: ImportProgressCallback | None = None,
    ):
        return self.engine.import_discover(
            include_system=include_system,
            include_identities=include_identities,
            include_grants=include_grants,
            catalogs=catalogs,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            progress=progress,
        )

    def import_generate(
        self,
        *,
        catalogs: list[str] | None = None,
        include_groups: bool = False,
        include_identities: bool = False,
        include_grants: bool = False,
        include_system: bool = False,
        grant_scope: str = "catalog",
        max_grant_objects: int | None = 500,
        progress: ImportProgressCallback | None = None,
    ):
        return self.engine.import_generate(
            catalogs=catalogs,
            include_groups=include_groups,
            include_identities=include_identities,
            include_grants=include_grants,
            include_system=include_system,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            progress=progress,
        )

    def import_suite(
        self,
        *,
        output_dir: str | Path,
        catalogs: list[str] | None = None,
        include_system: bool = False,
        grant_scope: str = "catalog",
        max_grant_objects: int | None = 500,
        progress: ImportProgressCallback | None = None,
    ):
        return self.engine.import_suite(
            output_dir=output_dir,
            catalogs=catalogs,
            include_system=include_system,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            progress=progress,
        )

    def import_adopt(self, *, targets: list[str], commit: bool = False):
        return self.engine.import_adopt(targets=targets, commit=commit)
