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

    def state_backend_report(self):
        return self.engine.state_backend_report()

    def enterprise_activation_report(self):
        return self.engine.enterprise_activation_report()

    def enterprise_control_plane_contract(self):
        return self.engine.enterprise_control_plane_contract()

    def enterprise_control_plane_architecture(self):
        return self.engine.enterprise_control_plane_architecture()

    def write_enterprise_control_plane_architecture(self, output_path: str | Path):
        return self.engine.write_enterprise_control_plane_architecture(output_path)

    def write_enterprise_activation_bundle(self, output_path: str | Path):
        return self.engine.write_enterprise_activation_bundle(output_path)

    def enterprise_activation_purchase_request(self):
        return self.engine.enterprise_activation_purchase_request()

    def write_enterprise_activation_purchase_request(self, output_path: str | Path):
        return self.engine.write_enterprise_activation_purchase_request(output_path)

    def enterprise_activation_evidence_report(self):
        return self.engine.enterprise_activation_evidence_report()

    def write_enterprise_activation_evidence(self, output_path: str | Path):
        return self.engine.write_enterprise_activation_evidence(output_path)

    def write_enterprise_control_plane_contract(self, output_path: str | Path):
        return self.engine.write_enterprise_control_plane_contract(output_path)

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
        grant_object_budgets: dict[str, int] | None = None,
        resume_checkpoint: dict | None = None,
        progress: ImportProgressCallback | None = None,
    ):
        return self.engine.import_discover(
            include_system=include_system,
            include_identities=include_identities,
            include_grants=include_grants,
            catalogs=catalogs,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            grant_object_budgets=grant_object_budgets,
            resume_checkpoint=resume_checkpoint,
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
        grant_object_budgets: dict[str, int] | None = None,
        resume_checkpoint: dict | None = None,
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
            grant_object_budgets=grant_object_budgets,
            resume_checkpoint=resume_checkpoint,
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
        grant_object_budgets: dict[str, int] | None = None,
        resume_checkpoint: dict | None = None,
        suite_layout: str = "standard",
        suite_prefix: str | None = None,
        progress: ImportProgressCallback | None = None,
    ):
        return self.engine.import_suite(
            output_dir=output_dir,
            catalogs=catalogs,
            include_system=include_system,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            grant_object_budgets=grant_object_budgets,
            resume_checkpoint=resume_checkpoint,
            suite_layout=suite_layout,
            suite_prefix=suite_prefix,
            progress=progress,
        )

    def import_adopt(self, *, targets: list[str], commit: bool = False):
        return self.engine.import_adopt(targets=targets, commit=commit)

    def import_databricks_to_snowflake_mapping(
        self,
        *,
        catalogs: list[str] | None = None,
        target_account: str = "snowflake-account",
        target_workspace: str = "snowflake-target",
        database_prefix: str | None = None,
        schema_case: str = "upper",
        progress: ImportProgressCallback | None = None,
    ):
        return self.engine.import_databricks_to_snowflake_mapping(
            catalogs=catalogs,
            target_account=target_account,
            target_workspace=target_workspace,
            database_prefix=database_prefix,
            schema_case=schema_case,
            progress=progress,
        )
