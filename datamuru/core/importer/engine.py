from __future__ import annotations

from pathlib import Path
import re

import yaml

from datamuru.core.config import load_project, resolve_environment_name
from datamuru.core.plan import fingerprint, matches_target
from datamuru.core.state import resolve_state_backend
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.errors import ImportAdoptionError, ValidationError
from datamuru.governance.masking import compile_masking_resources
from datamuru.governance.rbac import compile_rbac_resources
from datamuru.governance.taxonomy import compile_taxonomy_resources
from datamuru.providers.factory import load_provider

from .models import (
    DatabricksToSnowflakeMappingResult,
    ImportAdoptionConflict,
    ImportAdoptionResult,
    ImportDiscoveryReport,
    ImportGenerationResult,
    ImportProgressEvent,
    ImportProgressCallback,
    SnowflakeToDatabricksMappingResult,
)


class ImportEngine:
    def __init__(self, config_path: str | Path, environment: str | None = None) -> None:
        self.config_path = Path(config_path).resolve()
        self.environment = environment

    def _load(self):
        project = load_project(self.config_path)
        environment = resolve_environment_name(project, self.environment)
        provider = load_provider(project)
        return project, environment, provider

    def discover(
        self,
        *,
        include_system: bool = False,
        include_identities: bool = False,
        include_grants: bool = False,
        catalogs: list[str] | None = None,
        grant_scope: str = "catalog",
        max_grant_objects: int | None = 500,
        grant_object_budgets: dict[str, int] | None = None,
        resume_checkpoint: dict | None = None,
        progress: ImportProgressCallback | None = None,
    ) -> ImportDiscoveryReport:
        self._emit_progress(progress, "Loading DataMuru configuration.", total=6, completed=0)
        project, environment, provider = self._load()
        self._emit_progress(progress, "Configuration loaded. Connecting to provider.", completed=1)
        return provider.discover_importable_resources(
            project,
            environment,
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

    def generate(
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
    ) -> ImportGenerationResult:
        report = self.discover(
            include_system=include_system,
            include_identities=include_identities or include_groups,
            include_grants=include_grants,
            catalogs=catalogs,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            grant_object_budgets=grant_object_budgets,
            resume_checkpoint=resume_checkpoint,
            progress=progress,
        )
        selected_catalogs = sorted(catalogs or [catalog.name for catalog in report.workspace.catalogs])
        available_catalogs = {catalog.name: catalog for catalog in report.workspace.catalogs}
        missing_catalogs = [catalog for catalog in selected_catalogs if catalog not in available_catalogs]
        if missing_catalogs:
            raise ValidationError(
                description="Requested import catalogs were not found in the live workspace discovery result.",
                context={
                    "requested_catalogs": selected_catalogs,
                    "missing_catalogs": missing_catalogs,
                    "available_catalogs": sorted(available_catalogs),
                },
            )

        workspace_payload: dict = {
            "workspace": {
                "name": report.workspace.name,
                "cloud": report.workspace.cloud,
                "region": report.workspace.region,
                "catalogs": [
                    {
                        "name": catalog_name,
                        "schemas": [schema.name for schema in available_catalogs[catalog_name].schemas],
                    }
                    for catalog_name in selected_catalogs
                ],
            }
        }
        included_groups: list[str] = []
        if include_groups and report.workspace.groups:
            included_groups = report.workspace.groups
            workspace_payload["workspace"]["principals"] = {"groups": included_groups}
        if include_identities:
            principals = workspace_payload["workspace"].setdefault("principals", {})
            if report.workspace.users:
                principals["users"] = [
                    {
                        "email": user.email,
                        **({"display_name": user.display_name} if user.display_name else {}),
                        "lifecycle": "existing",
                    }
                    for user in report.workspace.users
                ]
            if report.workspace.group_details:
                principals["groups"] = [
                    {
                        "name": group.name,
                        "lifecycle": "existing",
                        **({"members": group.members} if group.members else {}),
                    }
                    for group in report.workspace.group_details
                ]
                included_groups = [group.name for group in report.workspace.group_details]
            elif report.workspace.groups:
                principals["groups"] = [{"name": group, "lifecycle": "existing"} for group in report.workspace.groups]
                included_groups = report.workspace.groups
            if report.workspace.service_principals:
                principals["service_principals"] = [
                    {
                        "name": principal.name,
                        **({"application_id": principal.application_id} if principal.application_id else {}),
                        "lifecycle": "existing",
                    }
                    for principal in report.workspace.service_principals
                ]

        yaml_text = yaml.safe_dump(workspace_payload, sort_keys=False)
        rbac_text = self._generate_rbac_text(report.workspace.grants, selected_catalogs) if include_grants else None
        taxonomy_text = self._generate_taxonomy_text() if include_grants or include_identities else None
        masking_text = self._generate_masking_text() if include_grants or include_identities else None
        return ImportGenerationResult(
            provider=report.provider,
            environment=report.environment,
            workspace_name=report.workspace.name,
            workspace_file_text=yaml_text,
            rbac_file_text=rbac_text,
            taxonomy_file_text=taxonomy_text,
            masking_file_text=masking_text,
            selected_catalogs=selected_catalogs,
            included_groups=included_groups,
            included_users=[user.email for user in report.workspace.users] if include_identities else [],
            included_service_principals=[principal.name for principal in report.workspace.service_principals]
            if include_identities
            else [],
            included_grants=len(report.workspace.grants) if include_grants else 0,
        )

    def write_suite(
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
    ) -> ImportGenerationResult:
        if suite_layout not in {"standard", "enterprise"}:
            raise ValidationError(
                description="Unsupported import suite layout.",
                context={"suite_layout": suite_layout, "supported_layouts": ["standard", "enterprise"]},
                suggestion="Use suite_layout='standard' for compatibility or 'enterprise' for provider-aware file names.",
            )
        result = self.generate(
            catalogs=catalogs,
            include_identities=True,
            include_grants=True,
            include_system=include_system,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            grant_object_budgets=grant_object_budgets,
            resume_checkpoint=resume_checkpoint,
            progress=progress,
        )
        root = Path(output_dir).resolve()
        workspace_dir = root / "workspaces"
        governance_dir = root / "governance"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        governance_dir.mkdir(parents=True, exist_ok=True)
        files = self._suite_paths(
            workspace_dir=workspace_dir,
            governance_dir=governance_dir,
            result=result,
            suite_layout=suite_layout,
            suite_prefix=suite_prefix,
        )
        files["workspace"].write_text(result.workspace_file_text, encoding="utf-8")
        if result.rbac_file_text:
            files["rbac"].write_text(result.rbac_file_text, encoding="utf-8")
        if result.taxonomy_file_text:
            files["taxonomy"].write_text(result.taxonomy_file_text, encoding="utf-8")
        if result.masking_file_text:
            files["masking"].write_text(result.masking_file_text, encoding="utf-8")
        return result.model_copy(update={"suite_files": {key: str(path) for key, path in files.items() if path.exists()}})

    def databricks_to_snowflake_mapping(
        self,
        *,
        catalogs: list[str] | None = None,
        target_account: str = "snowflake-account",
        target_workspace: str = "snowflake-target",
        database_prefix: str | None = None,
        schema_case: str = "upper",
        progress: ImportProgressCallback | None = None,
    ) -> DatabricksToSnowflakeMappingResult:
        if schema_case not in {"upper", "lower", "preserve"}:
            raise ValidationError(
                description="Unsupported Snowflake schema naming mode.",
                context={"schema_case": schema_case, "supported_modes": ["upper", "lower", "preserve"]},
                suggestion="Use schema_case upper, lower, or preserve.",
            )
        report = self.discover(catalogs=catalogs, progress=progress)
        if report.provider != "databricks":
            raise ValidationError(
                description="Databricks-to-Snowflake mapping requires a Databricks source provider.",
                context={"provider": report.provider},
                suggestion="Run this command from a DataMuru project configured with the Databricks provider.",
            )
        selected_catalogs = sorted(catalogs or [catalog.name for catalog in report.workspace.catalogs])
        available_catalogs = {catalog.name: catalog for catalog in report.workspace.catalogs}
        missing_catalogs = [catalog for catalog in selected_catalogs if catalog not in available_catalogs]
        if missing_catalogs:
            raise ValidationError(
                description="Requested mapping catalogs were not found in the Databricks discovery result.",
                context={
                    "requested_catalogs": selected_catalogs,
                    "missing_catalogs": missing_catalogs,
                    "available_catalogs": sorted(available_catalogs),
                },
            )

        catalog_mappings: dict[str, dict] = {}
        mapped_databases: list[str] = []
        for catalog_name in selected_catalogs:
            database_name = self._snowflake_identifier(
                f"{database_prefix}_{catalog_name}" if database_prefix else catalog_name,
                schema_case,
            )
            mapped_databases.append(database_name)
            catalog_mappings[catalog_name] = {
                "database": database_name,
                "schemas": {
                    schema.name: self._snowflake_identifier(schema.name, schema_case)
                    for schema in available_catalogs[catalog_name].schemas
                },
            }

        payload = {
            "migration": {
                "name": f"{self._slug(report.workspace.name)}-to-{self._slug(target_workspace)}",
                "source": {
                    "provider": "databricks",
                    "workspace": report.workspace.name,
                    "environment": report.environment,
                },
                "target": {
                    "provider": "snowflake",
                    "account": target_account,
                    "workspace": target_workspace,
                },
                "naming": {
                    "database_prefix": database_prefix,
                    "schema_case": schema_case,
                },
                "mappings": {"catalogs": catalog_mappings},
                "review": {
                    "status": "draft",
                    "notes": [
                        "Review database names, schema names, RBAC differences, and data-movement scope before implementation.",
                        "This draft does not move data or apply Snowflake changes.",
                    ],
                },
            }
        }
        return DatabricksToSnowflakeMappingResult(
            provider=report.provider,
            environment=report.environment,
            source_workspace=report.workspace.name,
            target_account=target_account,
            mapping_file_text=yaml.safe_dump(payload, sort_keys=False),
            selected_catalogs=selected_catalogs,
            mapped_databases=mapped_databases,
        )

    def snowflake_to_databricks_mapping(
        self,
        *,
        databases: list[str] | None = None,
        target_workspace: str = "databricks-target",
        target_cloud: str = "azure",
        catalog_prefix: str | None = None,
        identifier_case: str = "lower",
        progress: ImportProgressCallback | None = None,
    ) -> SnowflakeToDatabricksMappingResult:
        if identifier_case not in {"lower", "preserve"}:
            raise ValidationError(
                description="Unsupported Databricks identifier naming mode.",
                context={"identifier_case": identifier_case, "supported_modes": ["lower", "preserve"]},
                suggestion="Use identifier_case lower or preserve.",
            )
        if target_cloud not in {"azure", "aws", "gcp"}:
            raise ValidationError(
                description="Unsupported Databricks target cloud.",
                context={"target_cloud": target_cloud, "supported_clouds": ["azure", "aws", "gcp"]},
                suggestion="Use target_cloud azure, aws, or gcp.",
            )
        report = self.discover(catalogs=databases, progress=progress)
        if report.provider != "snowflake":
            raise ValidationError(
                description="Snowflake-to-Databricks mapping requires a Snowflake source provider.",
                context={"provider": report.provider},
                suggestion="Run this command from a DataMuru project configured with the Snowflake provider.",
            )
        selected_databases = sorted(databases or [catalog.name for catalog in report.workspace.catalogs])
        available_databases = {catalog.name: catalog for catalog in report.workspace.catalogs}
        missing_databases = [name for name in selected_databases if name not in available_databases]
        if missing_databases:
            raise ValidationError(
                description="Requested mapping databases were not found in the Snowflake discovery result.",
                context={
                    "requested_databases": selected_databases,
                    "missing_databases": missing_databases,
                    "available_databases": sorted(available_databases),
                },
            )

        database_mappings: dict[str, dict] = {}
        mapped_catalogs: list[str] = []
        catalog_sources: dict[str, list[str]] = {}
        for database_name in selected_databases:
            source = available_databases[database_name]
            target_catalog = self._databricks_identifier(
                f"{catalog_prefix}_{database_name}" if catalog_prefix else database_name,
                identifier_case,
            )
            source_databases = catalog_sources.setdefault(target_catalog, [])
            source_databases.append(database_name)
            if len(source_databases) > 1:
                raise ValidationError(
                    description=(
                        "Snowflake database names collide after Databricks identifier normalization."
                    ),
                    context={
                        "target_identifier": target_catalog,
                        "source_databases": sorted(source_databases),
                    },
                    suggestion=(
                        "Change catalog_prefix, identifier_case, source names, or mapping scope."
                    ),
                )
            schema_mappings: dict[str, str] = {}
            schema_sources: dict[str, list[str]] = {}
            for schema in source.schemas:
                target_schema = self._databricks_identifier(schema.name, identifier_case)
                source_schemas = schema_sources.setdefault(target_schema, [])
                source_schemas.append(schema.name)
                if len(source_schemas) > 1:
                    raise ValidationError(
                        description=(
                            "Snowflake schema names collide after Databricks identifier normalization."
                        ),
                        context={
                            "target_identifier": target_schema,
                            "source_database": database_name,
                            "source_schemas": sorted(source_schemas),
                        },
                        suggestion=(
                            "Change identifier_case, source names, or mapping scope."
                        ),
                    )
                schema_mappings[schema.name] = target_schema
            mapped_catalogs.append(target_catalog)
            database_mappings[database_name] = {
                "catalog": target_catalog,
                "schemas": schema_mappings,
            }

        payload = {
            "migration": {
                "name": f"{self._slug(report.workspace.name)}-to-{self._slug(target_workspace)}",
                "source": {
                    "provider": "snowflake",
                    "workspace": report.workspace.name,
                    "environment": report.environment,
                },
                "target": {
                    "provider": "databricks",
                    "workspace": target_workspace,
                    "cloud": target_cloud,
                },
                "naming": {
                    "catalog_prefix": catalog_prefix,
                    "identifier_case": identifier_case,
                },
                "mappings": {"databases": database_mappings},
                "review": {
                    "status": "draft",
                    "notes": [
                        "Review catalog and schema names before implementation.",
                        "This draft does not move data or apply Databricks changes.",
                    ],
                },
            }
        }
        return SnowflakeToDatabricksMappingResult(
            provider=report.provider,
            environment=report.environment,
            source_workspace=report.workspace.name,
            target_workspace=target_workspace,
            target_cloud=target_cloud,
            mapping_file_text=yaml.safe_dump(payload, sort_keys=False),
            selected_databases=selected_databases,
            mapped_catalogs=mapped_catalogs,
        )

    @staticmethod
    def _databricks_identifier(value: str, identifier_case: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_]+", "_", value)
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if not normalized:
            raise ValidationError(
                description="Source name cannot produce a Databricks identifier.",
                context={"source_name": value},
                suggestion="Rename the source object or select a different mapping scope.",
            )
        return normalized.lower() if identifier_case == "lower" else normalized

    @classmethod
    def _suite_paths(
        cls,
        *,
        workspace_dir: Path,
        governance_dir: Path,
        result: ImportGenerationResult,
        suite_layout: str,
        suite_prefix: str | None,
    ) -> dict[str, Path]:
        if suite_layout == "standard":
            return {
                "workspace": workspace_dir / f"imported-{result.environment}.yml",
                "rbac": governance_dir / "rbac.imported.yml",
                "taxonomy": governance_dir / "taxonomy.imported.yml",
                "masking": governance_dir / "masking.imported.yml",
            }

        prefix = suite_prefix or ".".join(
            [
                cls._slug(result.provider),
                cls._slug(result.environment),
                cls._slug(result.workspace_name),
                cls._scope_slug(result.selected_catalogs),
            ]
        )
        return {
            "workspace": workspace_dir / f"{prefix}.workspace.yml",
            "rbac": governance_dir / f"{prefix}.rbac.yml",
            "taxonomy": governance_dir / f"{prefix}.taxonomy.yml",
            "masking": governance_dir / f"{prefix}.masking.yml",
        }

    @staticmethod
    def _scope_slug(catalogs: list[str]) -> str:
        if not catalogs:
            return "all-catalogs"
        if len(catalogs) == 1:
            return ImportEngine._slug(catalogs[0])
        return f"{ImportEngine._slug(catalogs[0])}-plus-{len(catalogs) - 1}"

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
        return slug or "unnamed"

    @staticmethod
    def _snowflake_identifier(value: str, mode: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip()).strip("_")
        normalized = normalized or "UNNAMED"
        if mode == "lower":
            return normalized.lower()
        if mode == "preserve":
            return normalized
        return normalized.upper()

    @staticmethod
    def _emit_progress(
        progress: ImportProgressCallback | None,
        message: str,
        *,
        stage: str | None = None,
        total: int | None = None,
        completed: int | None = None,
        advance: int | None = None,
        checkpoint_path: str | None = None,
        checkpoint_update: dict | None = None,
    ) -> None:
        if progress is None:
            return
        progress(
            ImportProgressEvent(
                message=message,
                stage=stage,
                total=total,
                completed=completed,
                advance=advance,
                checkpoint_path=checkpoint_path,
                checkpoint_update=checkpoint_update,
            ).model_dump(mode="python", exclude_none=True)
        )

    @staticmethod
    def _generate_rbac_text(grants, selected_catalogs: list[str]) -> str:
        role_ids: dict[tuple[str, str], str] = {}
        roles: list[dict] = []
        assignments: dict[str, set[str]] = {}
        for grant in grants:
            if grant.securable_type == "catalog":
                resource = grant.securable_name
            elif grant.securable_type == "schema":
                catalog, _, schema = grant.securable_name.partition(".")
                resource = schema or grant.securable_name
            else:
                continue
            key = (grant.securable_type, grant.privilege)
            role_id = role_ids.get(key)
            if role_id is None:
                role_id = f"imported_{grant.securable_type}_{grant.privilege.lower()}"
                role_ids[key] = role_id
                roles.append(
                    {
                        "id": role_id,
                        "permissions": [
                            {
                                "action": grant.privilege,
                                "resource_type": grant.securable_type,
                                "resource": resource,
                            }
                        ],
                    }
                )
            assignments.setdefault(grant.principal, set()).add(role_id)
        payload = {
            "rbac": {
                "roles": roles,
                "assignments": [
                    {
                        "principal": principal,
                        "type": "group" if "@" not in principal else "user",
                        "roles": sorted(role_ids_for_principal),
                        "domains": selected_catalogs,
                    }
                    for principal, role_ids_for_principal in sorted(assignments.items())
                ],
            }
        }
        return yaml.safe_dump(payload, sort_keys=False)

    @staticmethod
    def _generate_taxonomy_text() -> str:
        return yaml.safe_dump(
            {
                "taxonomy": {
                    "name": "imported_workspace_taxonomy",
                    "version": "0.1",
                    "categories": [
                        {"id": "imported", "label": "Imported", "description": "Imported for review before curation."}
                    ],
                }
            },
            sort_keys=False,
        )

    @staticmethod
    def _generate_masking_text() -> str:
        return yaml.safe_dump(
            {
                "masking": {
                    "builtins": [
                        {
                            "id": "imported_review_required",
                            "strategy": "none",
                            "description": "Placeholder generated during brownfield import review.",
                        }
                    ]
                }
            },
            sort_keys=False,
        )

    def adopt(self, *, targets: list[str], commit: bool = False) -> ImportAdoptionResult:
        normalized_targets = sorted({target.strip() for target in targets if target.strip()})
        if not normalized_targets:
            raise ValidationError(
                description="Import adoption requires at least one explicit resource target.",
                suggestion="Pass --target with a declared resource address, such as catalog:analytics.",
            )

        project, environment, provider = self._load()
        desired_resources = provider.build_desired_resources(project)
        desired_resources.extend(compile_taxonomy_resources(project.governance))
        desired_resources.extend(compile_rbac_resources(project.governance))
        desired_resources.extend(compile_masking_resources(project.governance))
        selected = {
            resource.address: resource
            for resource in desired_resources
            if any(matches_target(resource.address, target) for target in normalized_targets)
        }
        unmatched_targets = [
            target
            for target in normalized_targets
            if not any(matches_target(address, target) for address in selected)
        ]
        if unmatched_targets:
            raise ValidationError(
                description="One or more adoption targets do not match declared resources.",
                context={"unmatched_targets": unmatched_targets},
                suggestion="Generate and review workspace YAML first, then target an address shown by datamuru plan.",
            )

        observed = provider.observe_current_state(project, environment)
        state_backend = resolve_state_backend(project)
        current_state = state_backend.load()
        candidates: list[str] = []
        already_managed: list[str] = []
        missing: list[str] = []
        conflicts: list[ImportAdoptionConflict] = []

        for address, resource in sorted(selected.items()):
            desired_fingerprint = fingerprint(resource)
            managed_record = current_state.resources.get(address)
            if managed_record is not None:
                if managed_record.fingerprint == desired_fingerprint:
                    already_managed.append(address)
                else:
                    conflicts.append(
                        ImportAdoptionConflict(
                            address=address,
                            reason="Local state already contains a different resource definition.",
                            desired_fingerprint=desired_fingerprint,
                            actual_fingerprint=managed_record.fingerprint,
                        )
                    )
                continue

            observed_record = observed.resources.get(address)
            if observed_record is None:
                missing.append(address)
                continue
            if observed_record.fingerprint != desired_fingerprint:
                conflicts.append(
                    ImportAdoptionConflict(
                        address=address,
                        reason="The live resource definition differs from the declared definition.",
                        desired_fingerprint=desired_fingerprint,
                        actual_fingerprint=observed_record.fingerprint,
                    )
                )
                continue
            candidates.append(address)

        result = ImportAdoptionResult(
            provider=project.root.provider.name,
            environment=environment,
            targets=normalized_targets,
            candidates=candidates,
            already_managed=already_managed,
            missing=missing,
            conflicts=conflicts,
        )
        if not commit:
            return result
        if not result.ready:
            raise ImportAdoptionError(
                description="State adoption was not committed because the preview contains blockers.",
                context={
                    "missing": missing,
                    "conflicts": [conflict.model_dump(mode="python") for conflict in conflicts],
                },
            )

        adopted_state = StateSnapshot(resources=dict(current_state.resources))
        for address in candidates:
            resource = selected[address]
            adopted_state.resources[address] = StateResourceRecord(
                fingerprint=fingerprint(resource),
                attributes=resource.attributes,
            )
        state_backend.save(adopted_state)
        return result.model_copy(update={"adopted": candidates, "committed": True})
