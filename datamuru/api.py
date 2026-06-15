from __future__ import annotations

from pathlib import Path

from datamuru.core.engine import DataMuruEngine


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

    def import_discover(self, include_system: bool = False):
        return self.engine.import_discover(include_system=include_system)

    def import_generate(
        self,
        *,
        catalogs: list[str] | None = None,
        include_groups: bool = False,
        include_system: bool = False,
    ):
        return self.engine.import_generate(
            catalogs=catalogs,
            include_groups=include_groups,
            include_system=include_system,
        )

    def import_adopt(self, *, targets: list[str], commit: bool = False):
        return self.engine.import_adopt(targets=targets, commit=commit)
