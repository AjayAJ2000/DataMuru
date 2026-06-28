from __future__ import annotations

from datamuru.core.importer.models import (
    ImportCatalogResource,
    ImportDiscoveryReport,
    ImportProgressCallback,
    ImportProgressEvent,
    ImportSchemaResource,
    ImportWorkspaceResource,
)
from datamuru.core.plan.renderer import fingerprint
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.errors import ProviderError
from datamuru.providers.base import DataMuruProvider
from datamuru.types import DoctorCheck, DoctorReport, ResourceDescriptor

from .auth import SnowflakeAuthConfig
from .client import SnowflakeSqlClient, import_schemas_by_database


class SnowflakeProvider(DataMuruProvider):
    def __init__(self, provider_data: dict) -> None:
        self.provider_data = provider_data
        self.auth = SnowflakeAuthConfig.from_provider_data(provider_data)
        self.client = SnowflakeSqlClient(self.auth)

    def authenticate(self, credentials: dict) -> bool:
        account_ready = bool(self.auth.resolve_account())
        if self.auth.uses_programmatic_access_token():
            return account_ready and bool(self.auth.resolve_token())
        return account_ready

    def doctor(self, project, environment: str) -> DoctorReport:
        connector_available = self.client.connector_available()
        checks = [
            DoctorCheck(
                level="ok" if self.auth.resolve_account() else "error",
                code="provider.account",
                message=(
                    "Snowflake account is configured."
                    if self.auth.resolve_account()
                    else "Snowflake account is missing. Set account or account_env."
                ),
            ),
            DoctorCheck(
                level="ok" if self.auth.resolve_user() else "warning",
                code="provider.user",
                message=(
                    "Snowflake user is configured."
                    if self.auth.resolve_user()
                    else "Snowflake user is not configured; SSO/externalbrowser may resolve it interactively later."
                ),
            ),
            DoctorCheck(
                level="ok",
                code="provider.execution_mode",
                message=f"Snowflake execution mode is '{self.auth.execution_mode}'.",
            ),
            DoctorCheck(
                level="warning",
                code="provider.live",
                message=(
                    "Snowflake live discovery is available in live-readonly mode; live apply/destroy remains disabled."
                    if self.auth.should_probe_connectivity()
                    else "Snowflake live discovery is available after switching to live-readonly; live apply/destroy remains disabled."
                ),
            ),
            DoctorCheck(
                level="ok" if connector_available else "warning",
                code="provider.connector",
                message=(
                    "snowflake-connector-python is available for live discovery."
                    if connector_available
                    else "snowflake-connector-python is not installed; install `datamuru[snowflake]` before live discovery."
                ),
            ),
        ]
        if self.auth.uses_programmatic_access_token():
            token_ready = bool(self.auth.resolve_token())
            checks.append(
                DoctorCheck(
                    level="ok" if token_ready else "error",
                    code="provider.pat",
                    message=(
                        "Snowflake Programmatic Access Token is available."
                        if token_ready
                        else (
                            "Snowflake Programmatic Access Token is missing. Set "
                            f"{self.auth.token_env or 'the configured token environment variable'}."
                        )
                    ),
                )
            )
        return DoctorReport(provider="snowflake", environment=environment, checks=checks)

    def build_desired_resources(self, project) -> list[ResourceDescriptor]:
        resources: list[ResourceDescriptor] = []
        for workspace_config in project.workspaces:
            workspace = workspace_config.raw.get("workspace", {})
            workspace_name = workspace.get("name", "snowflake-account")
            resources.append(
                ResourceDescriptor(
                    resource_type="workspace",
                    name=workspace_name,
                    attributes={
                        "cloud": workspace.get("cloud", "snowflake"),
                        "region": workspace.get("region"),
                        "tier": workspace.get("tier"),
                    },
                )
            )
            for catalog in workspace.get("catalogs", []):
                catalog_name = catalog["name"] if isinstance(catalog, dict) else str(catalog)
                resources.append(
                    ResourceDescriptor(
                        resource_type="catalog",
                        name=catalog_name,
                        attributes={"workspace": workspace_name, "snowflake_type": "database"},
                    )
                )
                schemas = catalog.get("schemas", []) if isinstance(catalog, dict) else []
                for schema in schemas:
                    schema_name = schema["name"] if isinstance(schema, dict) else str(schema)
                    resources.append(
                        ResourceDescriptor(
                            resource_type="schema",
                            name=f"{catalog_name}.{schema_name}",
                            attributes={
                                "workspace": workspace_name,
                                "catalog": catalog_name,
                                "snowflake_type": "schema",
                            },
                        )
                    )
        return resources

    def apply_resource(self, resource: ResourceDescriptor) -> dict:
        if self.auth.allows_live_mutation():
            raise ProviderError(
                description="Snowflake live apply is not enabled yet.",
                context={"resource": resource.address},
                suggestion="Use state-only for modeling until the Snowflake SQL executor is released and tested.",
            )
        return {"applied": resource.address, "provider": "snowflake", "mode": "state-only"}

    def destroy_resource(self, resource: ResourceDescriptor) -> bool:
        if self.auth.allows_live_mutation():
            raise ProviderError(
                description="Snowflake live destroy is not enabled yet.",
                context={"resource": resource.address},
                suggestion="Use state-only for modeling until Snowflake destroy safety checks are released.",
            )
        return True

    def observe_current_state(self, project, environment: str) -> StateSnapshot:
        if not self.auth.should_probe_connectivity():
            return StateSnapshot()
        if len(project.workspaces) != 1:
            return StateSnapshot()
        workspace_config = project.workspaces[0]
        workspace = workspace_config.raw.get("workspace", {})
        workspace_name = workspace.get("name", "snowflake-account")
        desired_catalogs, desired_schemas = self._desired_resource_index(project)
        observed_resources: dict[str, StateResourceRecord] = {}

        workspace_descriptor = ResourceDescriptor(
            resource_type="workspace",
            name=workspace_name,
            attributes={
                "cloud": workspace.get("cloud", "snowflake"),
                "region": workspace.get("region"),
                "tier": workspace.get("tier"),
            },
        )
        observed_resources[workspace_descriptor.address] = StateResourceRecord(
            fingerprint=fingerprint(workspace_descriptor),
            attributes=workspace_descriptor.attributes,
        )

        for database_name in self.client.list_databases(include_system=False):
            if database_name not in desired_catalogs:
                continue
            catalog_descriptor = ResourceDescriptor(
                resource_type="catalog",
                name=database_name,
                attributes={"workspace": workspace_name, "snowflake_type": "database"},
            )
            observed_resources[catalog_descriptor.address] = StateResourceRecord(
                fingerprint=fingerprint(catalog_descriptor),
                attributes=catalog_descriptor.attributes,
            )
            wanted_schemas = desired_schemas.get(database_name, set())
            for schema_name in self.client.list_schemas(database_name, include_system=False):
                if schema_name not in wanted_schemas:
                    continue
                schema_descriptor = ResourceDescriptor(
                    resource_type="schema",
                    name=f"{database_name}.{schema_name}",
                    attributes={
                        "workspace": workspace_name,
                        "catalog": database_name,
                        "snowflake_type": "schema",
                    },
                )
                observed_resources[schema_descriptor.address] = StateResourceRecord(
                    fingerprint=fingerprint(schema_descriptor),
                    attributes=schema_descriptor.attributes,
                )
        return StateSnapshot(resources=observed_resources)

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
        resume_checkpoint: dict | None = None,
        progress: ImportProgressCallback | None = None,
    ) -> ImportDiscoveryReport:
        if include_identities or include_grants:
            raise ProviderError(
                description="Snowflake import discovery currently supports database and schema inventory only.",
                context={
                    "include_identities": include_identities,
                    "include_grants": include_grants,
                    "grant_scope": grant_scope,
                    "max_grant_objects": max_grant_objects,
                    "grant_object_budgets": grant_object_budgets,
                    "resume_checkpoint": bool(resume_checkpoint),
                },
                suggestion="Run Snowflake discovery without identities or grants until Snowflake RBAC import is released.",
            )
        if not self.auth.should_probe_connectivity():
            raise ProviderError(
                description="Snowflake import discovery requires a live Snowflake execution mode.",
                context={"execution_mode": self.auth.execution_mode},
                suggestion="Use live-readonly before running Snowflake import discovery.",
            )
        if len(project.workspaces) != 1:
            raise ProviderError(
                description="Snowflake import discovery currently requires exactly one workspace declaration.",
                context={"workspace_count": len(project.workspaces)},
                suggestion="Keep one Snowflake workspace YAML in scope while using the alpha import flow.",
            )

        workspace_config = project.workspaces[0]
        workspace = workspace_config.raw.get("workspace", {})
        workspace_name = workspace.get("name", "snowflake-account")
        self._emit_import_progress(progress, "Listing Snowflake databases.", total=3, completed=1)
        database_names = self.client.list_databases(include_system=include_system)
        catalog_filter = {catalog.casefold() for catalog in catalogs or []}
        if catalog_filter:
            database_names = [
                database_name for database_name in database_names if database_name.casefold() in catalog_filter
            ]
        self._emit_import_progress(
            progress,
            f"Discovered {len(database_names)} Snowflake database(s) in scope.",
            total=max(2 + len(database_names), 3),
            completed=2,
        )
        schemas_by_database = import_schemas_by_database(
            self.client,
            database_names,
            include_system=include_system,
        )
        import_catalogs = [
            ImportCatalogResource(
                name=database_name,
                schemas=[
                    ImportSchemaResource(name=schema_name)
                    for schema_name in schemas_by_database.get(database_name, [])
                ],
            )
            for database_name in database_names
        ]
        self._emit_import_progress(progress, "Snowflake import discovery complete.")
        return ImportDiscoveryReport(
            provider="snowflake",
            environment=environment,
            include_system=include_system,
            workspace=ImportWorkspaceResource(
                name=workspace_name,
                cloud="snowflake",
                region=workspace.get("region", "unknown"),
                catalogs=import_catalogs,
            ),
        )

    def get_resource_types(self) -> list[str]:
        return ["workspace", "catalog", "schema"]

    @staticmethod
    def _emit_import_progress(
        progress: ImportProgressCallback | None,
        message: str,
        *,
        total: int | None = None,
        completed: int | None = None,
    ) -> None:
        if progress is None:
            return
        progress(
            ImportProgressEvent(
                message=message,
                total=total,
                completed=completed,
            ).model_dump(mode="python", exclude_none=True)
        )

    @staticmethod
    def _desired_resource_index(project) -> tuple[set[str], dict[str, set[str]]]:
        desired_catalogs: set[str] = set()
        desired_schemas: dict[str, set[str]] = {}
        for workspace_config in project.workspaces:
            workspace = workspace_config.raw.get("workspace", {})
            for catalog in workspace.get("catalogs", []):
                catalog_name = catalog["name"] if isinstance(catalog, dict) else str(catalog)
                desired_catalogs.add(catalog_name)
                desired_schemas.setdefault(catalog_name, set())
                schemas = catalog.get("schemas", []) if isinstance(catalog, dict) else []
                for schema in schemas:
                    schema_name = schema["name"] if isinstance(schema, dict) else str(schema)
                    desired_schemas[catalog_name].add(schema_name)
        return desired_catalogs, desired_schemas
