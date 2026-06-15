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

    def discover(self, *, include_system: bool = False) -> ImportDiscoveryReport:
        project, environment, provider = self._load()
        return provider.discover_importable_resources(project, environment, include_system=include_system)

    def generate(
        self,
        *,
        catalogs: list[str] | None = None,
        include_groups: bool = False,
        include_system: bool = False,
    ) -> ImportGenerationResult:
        report = self.discover(include_system=include_system)
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

        yaml_text = yaml.safe_dump(workspace_payload, sort_keys=False)
        return ImportGenerationResult(
            provider=report.provider,
            environment=report.environment,
            workspace_file_text=yaml_text,
            selected_catalogs=selected_catalogs,
            included_groups=included_groups,
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
