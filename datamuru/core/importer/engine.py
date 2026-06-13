from __future__ import annotations

from pathlib import Path

import yaml

from datamuru.core.config import load_project, resolve_environment_name
from datamuru.errors import ValidationError
from datamuru.providers.factory import load_provider

from .models import ImportDiscoveryReport, ImportGenerationResult


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
