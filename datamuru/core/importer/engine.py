from __future__ import annotations

from pathlib import Path

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
    ImportAdoptionConflict,
    ImportAdoptionResult,
    ImportDiscoveryReport,
    ImportGenerationResult,
    ImportProgressCallback,
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
        progress: ImportProgressCallback | None = None,
    ) -> ImportGenerationResult:
        report = self.discover(
            include_system=include_system,
            include_identities=include_identities or include_groups,
            include_grants=include_grants,
            catalogs=catalogs,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
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
        progress: ImportProgressCallback | None = None,
    ) -> ImportGenerationResult:
        result = self.generate(
            catalogs=catalogs,
            include_identities=True,
            include_grants=True,
            include_system=include_system,
            grant_scope=grant_scope,
            max_grant_objects=max_grant_objects,
            progress=progress,
        )
        root = Path(output_dir).resolve()
        workspace_dir = root / "workspaces"
        governance_dir = root / "governance"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        governance_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "workspace": workspace_dir / f"imported-{result.environment}.yml",
            "rbac": governance_dir / "rbac.imported.yml",
            "taxonomy": governance_dir / "taxonomy.imported.yml",
            "masking": governance_dir / "masking.imported.yml",
        }
        files["workspace"].write_text(result.workspace_file_text, encoding="utf-8")
        if result.rbac_file_text:
            files["rbac"].write_text(result.rbac_file_text, encoding="utf-8")
        if result.taxonomy_file_text:
            files["taxonomy"].write_text(result.taxonomy_file_text, encoding="utf-8")
        if result.masking_file_text:
            files["masking"].write_text(result.masking_file_text, encoding="utf-8")
        return result.model_copy(update={"suite_files": {key: str(path) for key, path in files.items() if path.exists()}})

    @staticmethod
    def _emit_progress(
        progress: ImportProgressCallback | None,
        message: str,
        *,
        total: int | None = None,
        completed: int | None = None,
        advance: int | None = None,
    ) -> None:
        if progress is None:
            return
        event: dict = {"message": message}
        if total is not None:
            event["total"] = total
        if completed is not None:
            event["completed"] = completed
        if advance is not None:
            event["advance"] = advance
        progress(event)

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
