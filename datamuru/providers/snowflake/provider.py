from __future__ import annotations

from datamuru.core.importer.models import ImportDiscoveryReport, ImportProgressCallback
from datamuru.core.state.models import StateSnapshot
from datamuru.errors import ProviderError
from datamuru.providers.base import DataMuruProvider
from datamuru.types import DoctorCheck, DoctorReport, ResourceDescriptor

from .auth import SnowflakeAuthConfig


class SnowflakeProvider(DataMuruProvider):
    def __init__(self, provider_data: dict) -> None:
        self.provider_data = provider_data
        self.auth = SnowflakeAuthConfig.from_provider_data(provider_data)

    def authenticate(self, credentials: dict) -> bool:
        return bool(self.auth.resolve_account())

    def doctor(self, project, environment: str) -> DoctorReport:
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
                message="Snowflake live discovery/apply is scaffolded but not enabled in this alpha build.",
            ),
        ]
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
        return StateSnapshot()

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
    ) -> ImportDiscoveryReport:
        raise ProviderError(
            description="Snowflake import discovery is not enabled yet.",
            context={
                "provider": "snowflake",
                "include_identities": include_identities,
                "include_grants": include_grants,
                "catalogs": catalogs,
                "grant_scope": grant_scope,
                "max_grant_objects": max_grant_objects,
            },
            suggestion="Use the Snowflake state-only provider scaffold now; live discovery is the next provider milestone.",
        )

    def get_resource_types(self) -> list[str]:
        return ["workspace", "catalog", "schema"]
