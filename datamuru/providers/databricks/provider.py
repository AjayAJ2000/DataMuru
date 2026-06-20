from __future__ import annotations

from urllib.parse import urlparse

from datamuru.core.importer.models import (
    ImportCatalogResource,
    ImportDiscoveryReport,
    ImportGrantResource,
    ImportGroupResource,
    ImportProgressCallback,
    ImportProgressEvent,
    ImportSchemaResource,
    ImportServicePrincipalResource,
    ImportUserResource,
    ImportWorkspaceResource,
)
from datamuru.core.plan.renderer import fingerprint
from datamuru.core.state.models import StateResourceRecord, StateSnapshot
from datamuru.errors import ProviderError
from datamuru.governance.rbac import compile_rbac_resources
from datamuru.providers.base import DataMuruProvider
from datamuru.types import DoctorCheck, DoctorReport, ResourceDescriptor

from .auth import DatabricksAuthConfig
from .client import DatabricksWorkspaceClient
from .execution import DatabricksExecutionPolicy


class DatabricksProvider(DataMuruProvider):
    SYSTEM_CATALOG_NAMES = {"samples", "system", "workspace"}
    SYSTEM_GROUP_NAMES = {"admins", "users"}
    SYSTEM_SCHEMA_NAMES = {"default", "information_schema"}

    def __init__(self, provider_data: dict) -> None:
        self.provider_data = provider_data
        self.auth = DatabricksAuthConfig.from_provider_data(provider_data)
        self.client = DatabricksWorkspaceClient(self.auth)
        self.execution_policy = DatabricksExecutionPolicy(self.auth)

    def authenticate(self, credentials: dict) -> bool:
        has_host_reference = self._is_valid_url(self.auth.host) or bool(self.auth.host_env)
        return self.auth.cloud in {"azure", "aws", "gcp"} and has_host_reference

    def doctor(self, project, environment: str) -> DoctorReport:
        checks: list[DoctorCheck] = []
        host = self.auth.host
        auth_type = self.auth.auth_type
        token_env = self.auth.token_env
        cloud = self.auth.cloud

        if cloud in {"azure", "aws", "gcp"}:
            checks.append(
                DoctorCheck(level="ok", code="provider.cloud", message=f"Databricks cloud is set to '{cloud}'.")
            )
        else:
            checks.append(
                DoctorCheck(
                    level="error",
                    code="provider.cloud",
                    message="Provider cloud must be azure, aws, or gcp.",
                )
            )

        if host and self._is_valid_url(host):
            checks.append(
                DoctorCheck(level="ok", code="provider.host", message="Databricks workspace host URL is configured.")
            )
        else:
            level = "error" if self.auth.should_probe_connectivity() else "warning"
            host_env = self.auth.host_env
            if host_env and not self.auth.host:
                message = f"Environment variable '{host_env}' is not set for Databricks workspace host."
            elif host and "your-workspace" in host:
                message = "Databricks workspace host URL is still the placeholder value."
            else:
                message = "Databricks workspace host URL is missing or invalid."
            checks.append(
                DoctorCheck(
                    level=level,
                    code="provider.host",
                    message=message,
                )
            )

        if auth_type == "pat":
            if not token_env:
                checks.append(
                    DoctorCheck(
                        level="error",
                        code="provider.token_env",
                        message="PAT authentication requires token_env in providers/databricks.yml.",
                    )
                )
            elif self.auth.resolve_token():
                checks.append(
                    DoctorCheck(
                        level="ok",
                        code="provider.token_env",
                        message=f"Environment variable '{token_env}' is available for PAT auth.",
                    )
                )
            else:
                checks.append(
                    DoctorCheck(
                        level="error",
                        code="provider.token_env",
                        message=f"Environment variable '{token_env}' is not set.",
                    )
                )
        elif auth_type == "databricks-cli":
            profile = self.auth.profile or "DEFAULT"
            profile_data = self.auth.resolve_cli_profile()
            profile_ready = bool(profile_data or self.auth.profile)
            sdk_ready = self.client.sdk_available()
            checks.append(
                DoctorCheck(
                    level="ok" if profile_ready and sdk_ready else "error",
                    code="provider.auth_type",
                    message=(
                        f"Databricks CLI profile auth is configured for profile '{profile}' using Databricks SDK unified auth."
                        if profile_ready and sdk_ready
                        else (
                            f"Databricks CLI profile '{profile}' is not ready for DataMuru. "
                            "Run `databricks auth login`, verify `databricks catalogs list --profile <profile>`, "
                            "and install `datamuru[databricks]`."
                        )
                    ),
                )
            )
        elif auth_type == "oauth":
            checks.append(
                DoctorCheck(
                    level="ok" if self.auth.resolve_token() else "error",
                    code="provider.auth_type",
                    message=(
                        "OAuth bearer-token authentication is configured."
                        if self.auth.resolve_token()
                        else "OAuth auth requires token_env or an Enterprise auth extension to provide a bearer token."
                    ),
                )
            )
        elif auth_type == "azure-managed-identity":
            checks.append(
                DoctorCheck(
                    level="warning",
                    code="provider.auth_type",
                    message=(
                        "Azure managed identity is reserved for Enterprise auth extensions; "
                        "the OSS alpha does not yet mint managed identity tokens directly."
                    ),
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    level="warning",
                    code="provider.auth_type",
                    message="Auth type is not one of the currently documented modes (pat, azure-managed-identity, databricks-cli, oauth).",
                    )
                )

        checks.append(
            DoctorCheck(
                level="ok",
                code="provider.execution_mode",
                message=f"Databricks execution mode is '{self.auth.execution_mode}'.",
            )
        )

        checks.append(
            DoctorCheck(
                level="ok" if self.client.sdk_available() else "warning",
                code="provider.sdk",
                message=(
                    "databricks-sdk is available for future live provider operations."
                    if self.client.sdk_available()
                    else "databricks-sdk is not installed; read-only probe can still use raw HTTPS."
                ),
            )
        )

        if self._uses_default_storage_catalogs(project):
            warehouse_id = self.auth.resolve_sql_warehouse_id()
            if warehouse_id:
                checks.append(
                    DoctorCheck(
                        level="ok",
                        code="provider.sql_warehouse",
                        message="SQL warehouse ID is configured for default-storage catalog creation.",
                    )
                )
            else:
                level = "error" if self.auth.allows_live_mutation() else "warning"
                checks.append(
                    DoctorCheck(
                        level=level,
                        code="provider.sql_warehouse",
                        message=(
                            "At least one catalog uses default storage, but no SQL warehouse ID is configured. "
                            "Set sql_warehouse_id or sql_warehouse_id_env before live-apply."
                        ),
                    )
                )

        if self._uses_permission_bindings(project):
            warehouse_id = self.auth.resolve_sql_warehouse_id()
            if warehouse_id:
                checks.append(
                    DoctorCheck(
                        level="ok",
                        code="provider.sql_acl",
                        message="SQL warehouse ID is configured for live ACL discovery and grant application.",
                    )
                )
            else:
                level = "error" if self.auth.should_probe_connectivity() else "warning"
                checks.append(
                    DoctorCheck(
                        level=level,
                        code="provider.sql_acl",
                        message=(
                            "RBAC permission bindings are declared, but no SQL warehouse ID is configured. "
                            "Set sql_warehouse_id or sql_warehouse_id_env in providers/databricks.yml."
                        ),
                    )
                )

        managed_identities = self._managed_identity_resources(project)
        if managed_identities:
            capability = self.client.probe_identity_management()
            checks.append(
                DoctorCheck(
                    level=capability.level,
                    code=capability.code,
                    message=capability.message,
                )
            )

        workspace_count = len(project.workspaces)
        if workspace_count:
            checks.append(
                DoctorCheck(
                    level="ok",
                    code="workspaces.count",
                    message=f"{workspace_count} workspace declaration(s) found for environment '{environment}'.",
                )
            )
        else:
            checks.append(
                DoctorCheck(level="warning", code="workspaces.count", message="No workspace declarations were found.")
            )

        if self._is_valid_url(host) and self.auth.should_probe_connectivity():
            connectivity = self.client.probe_workspace()
            details = ""
            if connectivity.current_user:
                details = f" Current user: {connectivity.current_user}."
            connectivity_details = getattr(connectivity, "details", None)
            if connectivity_details:
                detail_parts = [f"{key}={value}" for key, value in connectivity_details.items()]
                details = f"{details} Details: {'; '.join(detail_parts)}."
            checks.append(
                DoctorCheck(
                    level=connectivity.level,
                    code=connectivity.code,
                    message=f"{connectivity.message}{details}",
                )
            )
        elif self._is_valid_url(host):
            checks.append(
                DoctorCheck(
                    level="warning",
                    code="provider.connectivity",
                    message="Live connectivity probe skipped because execution mode is state-only.",
                )
            )

        return DoctorReport(provider="databricks", environment=environment, checks=checks)

    def observe_current_state(self, project, environment: str) -> StateSnapshot:
        if not self.auth.should_probe_connectivity():
            return StateSnapshot()
        if len(project.workspaces) != 1:
            return StateSnapshot()

        connectivity = self.client.probe_workspace()
        if not connectivity.ok:
            return StateSnapshot()

        workspace_config = project.workspaces[0]
        workspace = workspace_config.raw.get("workspace", {})
        workspace_name = workspace.get("name", "workspace")
        desired_groups, desired_catalogs, desired_schemas = self._desired_resource_index(project)
        desired_bindings = self._desired_permission_bindings(project)
        observed_resources: dict[str, StateResourceRecord] = {}

        workspace_descriptor = ResourceDescriptor(
            resource_type="workspace",
            name=workspace_name,
            attributes={
                "cloud": workspace.get("cloud"),
                "region": workspace.get("region"),
                "tier": workspace.get("tier"),
            },
        )
        observed_resources[workspace_descriptor.address] = StateResourceRecord(
            fingerprint=fingerprint(workspace_descriptor),
            attributes=workspace_descriptor.attributes,
        )

        try:
            group_names = self.client.list_groups()
        except ProviderError:
            group_names = []
        for group_name in group_names:
            if group_name not in desired_groups:
                continue
            descriptor = ResourceDescriptor(
                resource_type="group",
                name=group_name,
                attributes={"workspace": workspace_name},
            )
            observed_resources[descriptor.address] = StateResourceRecord(
                fingerprint=fingerprint(descriptor),
                attributes=descriptor.attributes,
            )

        try:
            catalog_names = self.client.list_catalogs()
        except ProviderError:
            catalog_names = []
        for catalog_name in catalog_names:
            if catalog_name not in desired_catalogs:
                continue
            catalog_descriptor = ResourceDescriptor(
                resource_type="catalog",
                name=catalog_name,
                attributes={"workspace": workspace_name},
            )
            observed_resources[catalog_descriptor.address] = StateResourceRecord(
                fingerprint=fingerprint(catalog_descriptor),
                attributes=catalog_descriptor.attributes,
            )
            try:
                schema_names = self.client.list_schemas(catalog_name)
            except ProviderError:
                schema_names = []
            wanted_schema_names = desired_schemas.get(catalog_name, set())
            for schema_name in schema_names:
                if schema_name.lower() in self.SYSTEM_SCHEMA_NAMES:
                    continue
                if schema_name not in wanted_schema_names:
                    continue
                schema_descriptor = ResourceDescriptor(
                    resource_type="schema",
                    name=f"{catalog_name}.{schema_name}",
                    attributes={"workspace": workspace_name, "catalog": catalog_name},
                )
                observed_resources[schema_descriptor.address] = StateResourceRecord(
                    fingerprint=fingerprint(schema_descriptor),
                    attributes=schema_descriptor.attributes,
                )

        if desired_bindings:
            live_grants = self._live_grant_index(desired_bindings)
            for binding in desired_bindings:
                observed_binding = self._observed_permission_binding(binding, live_grants)
                observed_resources[observed_binding.address] = StateResourceRecord(
                    fingerprint=fingerprint(observed_binding),
                    attributes=observed_binding.attributes,
                )

        observed_resources.update(self._observe_managed_identities(project))

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
        progress: ImportProgressCallback | None = None,
    ) -> ImportDiscoveryReport:
        normalized_grant_scope = grant_scope.lower()
        if normalized_grant_scope not in {"catalog", "schema", "all"}:
            raise ProviderError(
                description="Import grant discovery received an unsupported grant scope.",
                context={"grant_scope": grant_scope, "supported_scopes": ["catalog", "schema", "all"]},
                suggestion="Use grant_scope catalog, schema, or all.",
            )
        self._emit_import_progress(progress, "Checking Databricks import prerequisites.", total=6, completed=1)
        if not self.auth.should_probe_connectivity():
            raise ProviderError(
                description="Import discovery requires a live Databricks execution mode.",
                context={"execution_mode": self.auth.execution_mode},
                suggestion="Use live-readonly or live-apply before running import discovery.",
            )
        if len(project.workspaces) != 1:
            raise ProviderError(
                description="Import discovery currently requires exactly one workspace declaration.",
                context={"workspace_count": len(project.workspaces)},
                suggestion="Keep one workspace YAML in scope while using the alpha import flow.",
            )

        self._emit_import_progress(progress, "Verifying Databricks workspace connectivity.", completed=2)
        connectivity = self.client.probe_workspace()
        if not connectivity.ok:
            raise ProviderError(
                description="Import discovery could not verify Databricks connectivity first.",
                context={"connectivity_code": connectivity.code, "message": connectivity.message},
                suggestion="Run `datamuru doctor` and fix connectivity before using import discovery.",
            )

        workspace_config = project.workspaces[0]
        workspace = workspace_config.raw.get("workspace", {})
        workspace_name = workspace.get("name", "workspace")
        self._emit_import_progress(progress, "Discovering workspace groups.", completed=3)
        group_names = self._safe_list_groups(include_system=include_system)
        self._emit_import_progress(progress, "Discovering account identities.", completed=4)
        users, group_details, service_principals = self._safe_discover_identities(
            include_system=include_system,
            enabled=include_identities,
        )
        import_catalogs: list[ImportCatalogResource] = []
        grants: list[ImportGrantResource] = []
        catalog_filter = {catalog.casefold() for catalog in catalogs or []}
        self._emit_import_progress(progress, "Listing Unity Catalog catalogs.", completed=5)
        discovered_catalog_names = self._safe_list_catalogs(include_system=include_system)
        if catalog_filter:
            discovered_catalog_names = [
                catalog_name for catalog_name in discovered_catalog_names if catalog_name.casefold() in catalog_filter
            ]
        self._emit_import_progress(
            progress,
            f"Discovered {len(discovered_catalog_names)} catalog(s) in scope.",
            total=max(6 + len(discovered_catalog_names), 6),
            completed=6,
        )
        grant_scan_counts = {"catalog": 0, "schema": 0}
        grant_scan_completed = 0
        catalog_schema_pairs: list[tuple[str, list[ImportSchemaResource]]] = []
        for catalog_name in discovered_catalog_names:
            self._emit_import_progress(
                progress,
                f"Listing schemas in catalog {catalog_name}.",
                advance=1,
            )
            schema_resources = [
                ImportSchemaResource(name=schema_name)
                for schema_name in self._safe_list_schemas(catalog_name, include_system=include_system)
            ]
            catalog_schema_pairs.append((catalog_name, schema_resources))
            import_catalogs.append(ImportCatalogResource(name=catalog_name, schemas=schema_resources))
            catalog_count, schema_count = self._grant_target_counts(
                schema_count=len(schema_resources),
                grant_scope=normalized_grant_scope,
            )
            grant_scan_counts["catalog"] += catalog_count
            grant_scan_counts["schema"] += schema_count
        if include_grants:
            grant_scan_total = sum(grant_scan_counts.values())
            if max_grant_objects is not None and grant_scan_total > max_grant_objects:
                raise ProviderError(
                    description="Import grant discovery was stopped before launching an expensive scan.",
                    context={
                        "grant_scope": normalized_grant_scope,
                        "grant_objects_in_scope": grant_scan_total,
                        "max_grant_objects": max_grant_objects,
                        "catalogs_in_scope": len(discovered_catalog_names),
                        "grant_objects_by_type": grant_scan_counts,
                    },
                    suggestion=(
                        "Use --catalog to scope the import, keep --grant-scope catalog for inventory review, "
                        "or raise --max-grant-objects after estimating warehouse cost."
                    ),
                )
            self._validate_grant_object_budgets(
                grant_scan_counts=grant_scan_counts,
                grant_object_budgets=grant_object_budgets,
                grant_scope=normalized_grant_scope,
                catalog_count=len(discovered_catalog_names),
            )
            progress_base = 6 + len(discovered_catalog_names)
            self._emit_import_progress(
                progress,
                f"Scanning Unity Catalog {normalized_grant_scope} grants across {grant_scan_total} object(s).",
                total=progress_base + max(grant_scan_total, 1),
                completed=progress_base,
            )
            for catalog_name, schema_resources in catalog_schema_pairs:
                if normalized_grant_scope in {"catalog", "all"}:
                    grants.extend(self._safe_show_grants("catalog", catalog_name))
                    grant_scan_completed += 1
                    self._emit_import_progress(
                        progress,
                        f"Scanned grants for catalog {catalog_name}.",
                        completed=progress_base + grant_scan_completed,
                        stage="grant_scan",
                        object_type="catalog",
                        object_name=catalog_name,
                    )
                if normalized_grant_scope in {"schema", "all"}:
                    for schema_resource in schema_resources:
                        grants.extend(self._safe_show_grants("schema", f"{catalog_name}.{schema_resource.name}"))
                        grant_scan_completed += 1
                        self._emit_import_progress(
                            progress,
                            f"Scanned grants for schema {catalog_name}.{schema_resource.name}.",
                            completed=progress_base + grant_scan_completed,
                            stage="grant_scan",
                            object_type="schema",
                            object_name=f"{catalog_name}.{schema_resource.name}",
                        )

        self._emit_import_progress(progress, "Import discovery complete.")

        return ImportDiscoveryReport(
            provider="databricks",
            environment=environment,
            include_system=include_system,
            workspace=ImportWorkspaceResource(
                name=workspace_name,
                cloud=workspace.get("cloud", self.auth.cloud),
                region=workspace.get("region", "unknown"),
                catalogs=sorted(import_catalogs, key=lambda item: item.name),
                groups=sorted(group_names),
                users=sorted(users, key=lambda item: item.email),
                group_details=sorted(group_details, key=lambda item: item.name),
                service_principals=sorted(service_principals, key=lambda item: item.name),
                grants=sorted(
                    grants,
                    key=lambda item: (
                        item.securable_type,
                        item.securable_name,
                        item.principal,
                        item.privilege,
                    ),
                ),
            ),
        )

    @staticmethod
    def _grant_target_counts(*, schema_count: int, grant_scope: str) -> tuple[int, int]:
        if grant_scope == "catalog":
            return 1, 0
        if grant_scope == "schema":
            return 0, schema_count
        return 1, schema_count

    @staticmethod
    def _validate_grant_object_budgets(
        *,
        grant_scan_counts: dict[str, int],
        grant_object_budgets: dict[str, int] | None,
        grant_scope: str,
        catalog_count: int,
    ) -> None:
        if not grant_object_budgets:
            return
        supported_budget_types = {"catalog", "schema", "table", "view", "volume"}
        unsupported = sorted(set(grant_object_budgets) - supported_budget_types)
        if unsupported:
            raise ProviderError(
                description="Import grant discovery received unsupported grant object budget types.",
                context={
                    "unsupported_budget_types": unsupported,
                    "supported_budget_types": sorted(supported_budget_types),
                },
                suggestion="Use catalog/schema budgets today; table, view, and volume budgets are reserved for the next discovery surface.",
            )
        for object_type, scanned_count in grant_scan_counts.items():
            budget = grant_object_budgets.get(object_type)
            if budget is not None and scanned_count > budget:
                raise ProviderError(
                    description="Import grant discovery was stopped by an object-type scan budget.",
                    context={
                        "grant_scope": grant_scope,
                        "object_type": object_type,
                        "objects_in_scope": scanned_count,
                        "max_objects_for_type": budget,
                        "catalogs_in_scope": catalog_count,
                        "grant_objects_by_type": grant_scan_counts,
                    },
                    suggestion=(
                        f"Use --catalog to reduce {object_type} grant scope, lower --grant-scope, "
                        f"or raise --max-{object_type}-grant-objects after reviewing warehouse cost."
                    ),
                )

    @staticmethod
    def _emit_import_progress(
        progress: ImportProgressCallback | None,
        message: str,
        *,
        stage: str | None = None,
        total: int | None = None,
        completed: int | None = None,
        advance: int | None = None,
        object_type: str | None = None,
        object_name: str | None = None,
        checkpoint_path: str | None = None,
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
                object_type=object_type,
                object_name=object_name,
                checkpoint_path=checkpoint_path,
            ).model_dump(mode="python", exclude_none=True)
        )

    def build_desired_resources(self, project) -> list[ResourceDescriptor]:
        resources: list[ResourceDescriptor] = []
        for workspace_config in project.workspaces:
            workspace = workspace_config.raw.get("workspace", {})
            workspace_name = workspace["name"]
            resources.append(
                ResourceDescriptor(
                    resource_type="workspace",
                    name=workspace_name,
                    attributes={
                        "cloud": workspace.get("cloud"),
                        "region": workspace.get("region"),
                        "tier": workspace.get("tier"),
                    },
                )
            )
            resources.extend(self._build_identity_resources(project, workspace_name, workspace))
            for catalog in workspace.get("catalogs", []):
                catalog_definition = self._normalize_catalog_definition(catalog)
                catalog_name = catalog_definition["name"]
                catalog_attributes = {"workspace": workspace_name}
                if catalog_definition.get("managed_location") is not None:
                    catalog_attributes["managed_location"] = catalog_definition["managed_location"]
                if catalog_definition.get("use_default_storage"):
                    catalog_attributes["_use_default_storage"] = True
                resources.append(
                    ResourceDescriptor(
                        resource_type="catalog",
                        name=catalog_name,
                        attributes=catalog_attributes,
                    )
                )
                for schema in catalog_definition.get("schemas", []):
                    schema_definition = self._normalize_schema_definition(schema)
                    schema_attributes = {"workspace": workspace_name, "catalog": catalog_name}
                    if schema_definition.get("managed_location") is not None:
                        schema_attributes["managed_location"] = schema_definition["managed_location"]
                    resources.append(
                        ResourceDescriptor(
                            resource_type="schema",
                            name=f"{catalog_name}.{schema_definition['name']}",
                            attributes=schema_attributes,
                        )
                    )
        return resources

    def apply_resource(self, resource: ResourceDescriptor) -> dict:
        self.execution_policy.guard_mutation(resource)
        if self.auth.allows_live_mutation():
            if resource.resource_type in {"workspace", "taxonomy", "classification", "rbac_role", "column_mask"}:
                return {"applied": resource.address, "provider": "databricks", "mode": "local-only"}
            if resource.resource_type == "catalog":
                if resource.attributes.get("_use_default_storage"):
                    self.client.create_catalog_with_default_storage(resource.name)
                else:
                    self.client.create_catalog(
                        resource.name,
                        managed_location=resource.attributes.get("managed_location"),
                    )
                return {"applied": resource.address, "provider": "databricks", "mode": "live-apply"}
            if resource.resource_type == "schema":
                catalog_name, _, schema_name = resource.name.partition(".")
                if not catalog_name or not schema_name:
                    raise ProviderError(
                        description="Schema resource name must use the '<catalog>.<schema>' format.",
                        context={"resource": resource.address},
                    )
                self.client.create_schema(
                    catalog_name,
                    schema_name,
                    managed_location=resource.attributes.get("managed_location"),
                )
                return {"applied": resource.address, "provider": "databricks", "mode": "live-apply"}
            if resource.resource_type == "permission_binding":
                for grant in self._permission_binding_grants(resource):
                    self.client.grant_privilege(
                        privilege=grant["privilege"],
                        securable_type=grant["securable_type"],
                        securable_name=grant["securable_name"],
                        principal=grant["principal"],
                    )
                return {"applied": resource.address, "provider": "databricks", "mode": "live-apply"}
            if resource.resource_type in {"user", "group", "service_principal", "group_membership"}:
                self._apply_identity_resource(resource)
                return {"applied": resource.address, "provider": "databricks", "mode": "live-apply"}
        return {"applied": resource.address, "provider": "databricks"}

    def destroy_resource(self, resource: ResourceDescriptor) -> bool:
        self.execution_policy.guard_mutation(resource)
        if self.auth.allows_live_mutation():
            if resource.resource_type in {"workspace", "taxonomy", "classification", "rbac_role", "column_mask"}:
                return True
            if resource.resource_type == "catalog":
                self.client.delete_catalog(resource.name)
                return True
            if resource.resource_type == "schema":
                self.client.delete_schema(resource.name)
                return True
            if resource.resource_type == "permission_binding":
                for grant in self._permission_binding_grants(resource):
                    self.client.revoke_privilege(
                        privilege=grant["privilege"],
                        securable_type=grant["securable_type"],
                        securable_name=grant["securable_name"],
                        principal=grant["principal"],
                    )
                return True
            if resource.resource_type in {"user", "group", "service_principal", "group_membership"}:
                self._destroy_identity_resource(resource)
                return True
        return True

    def get_resource_types(self) -> list[str]:
        return [
            "workspace",
            "catalog",
            "schema",
            "user",
            "group",
            "service_principal",
            "group_membership",
            "permission_binding",
        ]

    @staticmethod
    def _is_valid_url(value: str) -> bool:
        parsed = urlparse(value)
        return bool(parsed.scheme and parsed.netloc)

    @staticmethod
    def _normalize_catalog_definition(catalog: object) -> dict:
        if isinstance(catalog, dict):
            if catalog.get("use_default_storage") and catalog.get("managed_location"):
                raise ProviderError(
                    description="Catalog definitions cannot set both use_default_storage and managed_location.",
                    context={"catalog": catalog},
                    suggestion="Choose either use_default_storage: true or managed_location, but not both.",
                )
            return catalog
        raise ProviderError(
            description="Catalog definitions must be mappings with at least a 'name' field.",
            context={"catalog": catalog},
        )

    @staticmethod
    def _normalize_schema_definition(schema: object) -> dict:
        if isinstance(schema, str):
            return {"name": schema}
        if isinstance(schema, dict):
            return schema
        raise ProviderError(
            description="Schema definitions must be strings or mappings with a 'name' field.",
            context={"schema": schema},
        )

    @classmethod
    def _uses_default_storage_catalogs(cls, project) -> bool:
        for workspace_config in project.workspaces:
            catalogs = workspace_config.raw.get("workspace", {}).get("catalogs", [])
            for catalog in catalogs:
                if isinstance(catalog, dict) and catalog.get("use_default_storage"):
                    return True
        return False

    @staticmethod
    def _uses_permission_bindings(project) -> bool:
        return any(
            resource.resource_type == "permission_binding"
            for resource in compile_rbac_resources(project.governance)
        )

    @classmethod
    def _desired_resource_index(cls, project) -> tuple[set[str], set[str], dict[str, set[str]]]:
        groups: set[str] = set()
        catalogs: set[str] = set()
        schemas: dict[str, set[str]] = {}
        for workspace_config in project.workspaces:
            workspace = workspace_config.raw.get("workspace", {})
            for group in workspace.get("principals", {}).get("groups", []):
                if isinstance(group, dict) and group.get("lifecycle", "existing") == "managed":
                    groups.add(group["name"])
            for catalog in workspace.get("catalogs", []):
                catalog_definition = cls._normalize_catalog_definition(catalog)
                catalog_name = catalog_definition["name"]
                catalogs.add(catalog_name)
                schemas.setdefault(catalog_name, set())
                for schema in catalog_definition.get("schemas", []):
                    schema_definition = cls._normalize_schema_definition(schema)
                    schemas[catalog_name].add(schema_definition["name"])
        return groups, catalogs, schemas

    @staticmethod
    def _desired_permission_bindings(project) -> list[ResourceDescriptor]:
        return [
            resource
            for resource in compile_rbac_resources(project.governance)
            if resource.resource_type == "permission_binding"
        ]

    @classmethod
    def _managed_identity_resources(cls, project) -> list[ResourceDescriptor]:
        resources: list[ResourceDescriptor] = []
        for workspace_config in project.workspaces:
            workspace = workspace_config.raw.get("workspace", {})
            resources.extend(cls._build_identity_resources(project, workspace.get("name", "workspace"), workspace))
        return resources

    @staticmethod
    def _build_identity_resources(project, workspace_name: str, workspace: dict) -> list[ResourceDescriptor]:
        principals = workspace.get("principals") or {}
        resources: list[ResourceDescriptor] = []
        managed_enabled = (
            project.root.project.edition == "enterprise"
            and project.root.features.identity_management
        )
        has_managed_declarations = any(
            isinstance(item, dict) and item.get("lifecycle", "existing") == "managed"
            for collection_name in ("users", "groups", "service_principals")
            for item in principals.get(collection_name, [])
        )
        if has_managed_declarations and not managed_enabled:
            raise ProviderError(
                description="Managed identity declarations require DataMuru Enterprise identity management.",
                context={
                    "workspace": workspace_name,
                    "edition": project.root.project.edition,
                    "identity_management": project.root.features.identity_management,
                },
                suggestion="Use project.edition: enterprise and set features.identity_management: true.",
            )

        managed_users: set[str] = set()
        managed_service_principals: set[str] = set()
        for user in principals.get("users", []):
            if not isinstance(user, dict) or user.get("lifecycle", "existing") != "managed":
                continue
            if not managed_enabled:
                continue
            email = user["email"]
            managed_users.add(email)
            resources.append(
                ResourceDescriptor(
                    resource_type="user",
                    name=email,
                    attributes={
                        "workspace": workspace_name,
                        "email": email,
                        "display_name": user.get("display_name"),
                        "lifecycle": "managed",
                        "allow_delete": bool(user.get("allow_delete", False)),
                        "_identity_management_enabled": True,
                    },
                )
            )

        for principal in principals.get("service_principals", []):
            if not isinstance(principal, dict) or principal.get("lifecycle", "existing") != "managed":
                continue
            if not managed_enabled:
                continue
            name = principal["name"]
            managed_service_principals.add(name)
            resources.append(
                ResourceDescriptor(
                    resource_type="service_principal",
                    name=name,
                    attributes={
                        "workspace": workspace_name,
                        "display_name": name,
                        "application_id": principal.get("application_id"),
                        "lifecycle": "managed",
                        "allow_delete": bool(principal.get("allow_delete", False)),
                        "_identity_management_enabled": True,
                    },
                )
            )

        for group in principals.get("groups", []):
            if not isinstance(group, dict) or group.get("lifecycle", "existing") != "managed":
                continue
            if not managed_enabled:
                continue
            group_name = group["name"]
            resources.append(
                ResourceDescriptor(
                    resource_type="group",
                    name=group_name,
                    attributes={
                        "workspace": workspace_name,
                        "display_name": group_name,
                        "lifecycle": "managed",
                        "allow_delete": bool(group.get("allow_delete", False)),
                        "_identity_management_enabled": True,
                    },
                )
            )
            members = group.get("members") or {}
            for member_type, collection_name in (
                ("user", "users"),
                ("group", "groups"),
                ("service_principal", "service_principals"),
            ):
                for member_name in members.get(collection_name, []):
                    resources.append(
                        ResourceDescriptor(
                            resource_type="group_membership",
                            name=f"{group_name}:{member_type}:{member_name}",
                            attributes={
                                "workspace": workspace_name,
                                "group": group_name,
                                "member_type": member_type,
                                "member_name": member_name,
                                "member_is_managed": (
                                    member_name in managed_users
                                    if member_type == "user"
                                    else member_name in managed_service_principals
                                    if member_type == "service_principal"
                                    else False
                                ),
                                "_identity_management_enabled": True,
                            },
                        )
                    )
        return resources

    def _observe_managed_identities(self, project) -> dict[str, StateResourceRecord]:
        desired = self._managed_identity_resources(project)
        if not desired:
            return {}
        capability = self.client.probe_identity_management()
        if not capability.supported:
            return {}
        try:
            users = self.client.list_account_users()
            groups = self.client.list_account_groups()
            service_principals = self.client.list_account_service_principals()
        except ProviderError:
            return {}

        user_index = {
            str(user.get("userName", "")).casefold(): user
            for user in users
            if user.get("userName")
        }
        group_index = {
            str(group.get("displayName", "")).casefold(): group
            for group in groups
            if group.get("displayName")
        }
        service_principal_index = {
            str(principal.get("displayName", "")).casefold(): principal
            for principal in service_principals
            if principal.get("displayName")
        }
        observed: dict[str, StateResourceRecord] = {}

        for resource in desired:
            exists = False
            if resource.resource_type == "user":
                exists = resource.name.casefold() in user_index
            elif resource.resource_type == "group":
                exists = resource.name.casefold() in group_index
            elif resource.resource_type == "service_principal":
                exists = resource.name.casefold() in service_principal_index
            elif resource.resource_type == "group_membership":
                group = group_index.get(str(resource.attributes["group"]).casefold())
                member = self._identity_from_indexes(
                    resource.attributes["member_type"],
                    resource.attributes["member_name"],
                    user_index,
                    group_index,
                    service_principal_index,
                )
                member_id = str((member or {}).get("id", ""))
                exists = bool(
                    group
                    and member_id
                    and any(str(item.get("value", "")) == member_id for item in group.get("members", []))
                )
            if exists:
                observed[resource.address] = StateResourceRecord(
                    fingerprint=fingerprint(resource),
                    attributes=resource.attributes,
                )
        return observed

    def _apply_identity_resource(self, resource: ResourceDescriptor) -> None:
        self._require_identity_management(resource)
        if resource.resource_type == "user":
            if not self.client.find_account_user(resource.name):
                self.client.create_account_user(
                    email=resource.name,
                    display_name=resource.attributes.get("display_name"),
                )
            return
        if resource.resource_type == "group":
            if resource.name.lower() in self.SYSTEM_GROUP_NAMES:
                raise ProviderError(
                    description="System-managed Databricks groups cannot be managed by DataMuru.",
                    context={"resource": resource.address},
                )
            if not self.client.find_account_group(resource.name):
                self.client.create_account_group(name=resource.name)
            return
        if resource.resource_type == "service_principal":
            if not self.client.find_account_service_principal(resource.name):
                self.client.create_account_service_principal(
                    name=resource.name,
                    application_id=resource.attributes.get("application_id"),
                )
            return
        if resource.resource_type == "group_membership":
            group = self.client.find_account_group(resource.attributes["group"])
            member = self._find_identity(
                resource.attributes["member_type"],
                resource.attributes["member_name"],
            )
            if not group or not member:
                raise ProviderError(
                    description="Group membership could not resolve both the target group and member.",
                    context={
                        "resource": resource.address,
                        "group_found": bool(group),
                        "member_found": bool(member),
                    },
                    suggestion="Declare managed identities first or ensure referenced existing identities already exist.",
                )
            member_id = str(member["id"])
            if not any(str(item.get("value", "")) == member_id for item in group.get("members", [])):
                self.client.add_group_member(group_id=str(group["id"]), member_id=member_id)

    def _destroy_identity_resource(self, resource: ResourceDescriptor) -> None:
        self._require_identity_management(resource)
        if resource.resource_type == "group_membership":
            group = self.client.find_account_group(resource.attributes["group"])
            member = self._find_identity(
                resource.attributes["member_type"],
                resource.attributes["member_name"],
            )
            if group and member:
                self.client.remove_group_member(group_id=str(group["id"]), member_id=str(member["id"]))
            return
        if not resource.attributes.get("allow_delete", False):
            raise ProviderError(
                description="Managed identity deletion is disabled for this resource.",
                context={"resource": resource.address, "allow_delete": False},
                suggestion="Set allow_delete: true explicitly only after reviewing the identity impact.",
            )
        if resource.resource_type == "group":
            if resource.name.lower() in self.SYSTEM_GROUP_NAMES:
                raise ProviderError(
                    description="System-managed Databricks groups cannot be deleted.",
                    context={"resource": resource.address},
                )
            identity = self.client.find_account_group(resource.name)
            scim_type = "Groups"
        elif resource.resource_type == "user":
            identity = self.client.find_account_user(resource.name)
            scim_type = "Users"
        else:
            identity = self.client.find_account_service_principal(resource.name)
            scim_type = "ServicePrincipals"
        if identity:
            self.client.delete_account_identity(resource_type=scim_type, resource_id=str(identity["id"]))

    def _require_identity_management(self, resource: ResourceDescriptor) -> None:
        if not resource.attributes.get("_identity_management_enabled"):
            raise ProviderError(
                description="Managed identity operations require DataMuru Enterprise identity management.",
                context={"resource": resource.address},
                suggestion=(
                    "Use project.edition: enterprise, enable features.identity_management, and declare the "
                    "identity with lifecycle: managed."
                ),
            )
        capability = self.client.probe_identity_management()
        if capability.supported:
            return
        raise ProviderError(
            description=capability.message,
            context={
                "resource": resource.address,
                "status_code": capability.status_code,
                **capability.details,
            },
            suggestion=(
                "Use an Enterprise DataMuru project connected to a full Databricks account with account SCIM "
                "support and an authorized admin principal. Free Edition can still use existing principals for ACLs."
            ),
        )

    def _find_identity(self, member_type: str, member_name: str) -> dict | None:
        if member_type == "user":
            return self.client.find_account_user(member_name)
        if member_type == "group":
            return self.client.find_account_group(member_name)
        if member_type == "service_principal":
            return self.client.find_account_service_principal(member_name)
        raise ProviderError(
            description="Unsupported group member type.",
            context={"member_type": member_type, "member_name": member_name},
        )

    @staticmethod
    def _identity_from_indexes(
        member_type: str,
        member_name: str,
        users: dict[str, dict],
        groups: dict[str, dict],
        service_principals: dict[str, dict],
    ) -> dict | None:
        key = member_name.casefold()
        if member_type == "user":
            return users.get(key)
        if member_type == "group":
            return groups.get(key)
        if member_type == "service_principal":
            return service_principals.get(key)
        return None

    @staticmethod
    def _permission_binding_grants(resource: ResourceDescriptor) -> list[dict[str, str]]:
        principal = resource.attributes.get("principal")
        domains = resource.attributes.get("domains", [])
        permissions = resource.attributes.get("permissions", [])
        if not principal or not permissions:
            raise ProviderError(
                description="Permission binding resources require principal and permissions data.",
                context={"resource": resource.address, "attributes": resource.attributes},
                suggestion="Compile permission bindings from governance RBAC before applying them live.",
            )

        grants: list[dict[str, str]] = []
        for permission in permissions:
            resource_type = str(permission.get("resource_type", "")).lower()
            privilege = str(permission.get("privilege", "")).upper()
            resource_pattern = str(permission.get("resource_pattern", ""))
            if resource_type not in {"catalog", "schema"}:
                raise ProviderError(
                    description="Live ACL support currently handles only catalog and schema grants.",
                    context={"resource": resource.address, "permission": permission},
                    suggestion="Limit RBAC permissions to catalog and schema grants for the current alpha slice.",
                )
            if not privilege:
                raise ProviderError(
                    description="Permission entries require a privilege value.",
                    context={"resource": resource.address, "permission": permission},
                )
            if resource_type == "catalog":
                target_catalogs = DatabricksProvider._expand_catalog_targets(domains, resource_pattern)
                for catalog_name in target_catalogs:
                    grants.append(
                        {
                            "principal": principal,
                            "privilege": privilege,
                            "securable_type": "catalog",
                            "securable_name": catalog_name,
                        }
                    )
                continue

            target_schemas = DatabricksProvider._expand_schema_targets(domains, resource_pattern)
            for schema_name in target_schemas:
                grants.append(
                    {
                        "principal": principal,
                        "privilege": privilege,
                        "securable_type": "schema",
                        "securable_name": schema_name,
                    }
                )
        return grants

    def _live_grant_index(self, bindings: list[ResourceDescriptor]) -> set[tuple[str, str, str, str]]:
        grant_index: set[tuple[str, str, str, str]] = set()
        queried_objects: set[tuple[str, str]] = set()
        for binding in bindings:
            for desired_grant in self._permission_binding_grants(binding):
                securable_key = (desired_grant["securable_type"], desired_grant["securable_name"])
                if securable_key in queried_objects:
                    continue
                queried_objects.add(securable_key)
                try:
                    live_grants = self.client.show_grants(
                        securable_type=desired_grant["securable_type"],
                        securable_name=desired_grant["securable_name"],
                    )
                except ProviderError:
                    continue
                for live_grant in live_grants:
                    grant_index.add(
                        (
                            str(live_grant.get("principal", "")).lower(),
                            str(live_grant.get("privilege", "")).upper(),
                            str(live_grant.get("securable_type", "")).lower(),
                            str(live_grant.get("securable_name", "")).lower(),
                        )
                    )
        return grant_index

    def _observed_permission_binding(
        self,
        binding: ResourceDescriptor,
        live_grants: set[tuple[str, str, str, str]],
    ) -> ResourceDescriptor:
        matching_permissions: list[dict] = []
        for permission in binding.attributes.get("permissions", []):
            grant_records = self._permission_binding_grants(
                ResourceDescriptor(
                    resource_type="permission_binding",
                    name=binding.name,
                    attributes={
                        "principal": binding.attributes.get("principal"),
                        "domains": binding.attributes.get("domains", []),
                        "permissions": [permission],
                    },
                )
            )
            if all(
                (
                    grant["principal"].lower(),
                    grant["privilege"].upper(),
                    grant["securable_type"].lower(),
                    grant["securable_name"].lower(),
                )
                in live_grants
                for grant in grant_records
            ):
                matching_permissions.append(permission)

        observed_attributes = dict(binding.attributes)
        observed_attributes["permissions"] = matching_permissions
        return ResourceDescriptor(
            resource_type=binding.resource_type,
            name=binding.name,
            attributes=observed_attributes,
        )

    @staticmethod
    def _expand_catalog_targets(domains: list[str], resource_pattern: str) -> list[str]:
        if resource_pattern in {"", "*"}:
            return list(domains)
        if "." in resource_pattern:
            raise ProviderError(
                description="Catalog permission patterns must not include schema segments.",
                context={"resource_pattern": resource_pattern, "domains": domains},
            )
        return [resource_pattern]

    @staticmethod
    def _expand_schema_targets(domains: list[str], resource_pattern: str) -> list[str]:
        if not domains and "." not in resource_pattern:
            raise ProviderError(
                description="Schema permission patterns without an explicit catalog require at least one domain.",
                context={"resource_pattern": resource_pattern, "domains": domains},
            )
        if resource_pattern.startswith("*."):
            suffix = resource_pattern[2:]
            return [f"{domain}.{suffix}" for domain in domains]
        if "." in resource_pattern:
            return [resource_pattern]
        return [f"{domain}.{resource_pattern}" for domain in domains]

    def _safe_list_groups(self, *, include_system: bool) -> list[str]:
        try:
            groups = self.client.list_groups()
        except ProviderError:
            return []
        if include_system:
            return groups
        return [group for group in groups if group.lower() not in self.SYSTEM_GROUP_NAMES]

    def _safe_list_catalogs(self, *, include_system: bool) -> list[str]:
        try:
            catalogs = self.client.list_catalogs()
        except ProviderError:
            return []
        if include_system:
            return catalogs
        return [catalog for catalog in catalogs if catalog.lower() not in self.SYSTEM_CATALOG_NAMES]

    def _safe_list_schemas(self, catalog_name: str, *, include_system: bool) -> list[str]:
        try:
            schemas = self.client.list_schemas(catalog_name)
        except ProviderError:
            return []
        if include_system:
            return schemas
        return [schema for schema in schemas if schema.lower() not in self.SYSTEM_SCHEMA_NAMES]

    def _safe_discover_identities(
        self,
        *,
        include_system: bool,
        enabled: bool,
    ) -> tuple[list[ImportUserResource], list[ImportGroupResource], list[ImportServicePrincipalResource]]:
        if not enabled:
            return [], [], []
        capability = self.client.probe_identity_management()
        if not capability.supported:
            return [], [], []
        try:
            raw_users = self.client.list_account_users()
            raw_groups = self.client.list_account_groups()
            raw_service_principals = self.client.list_account_service_principals()
        except ProviderError:
            return [], [], []

        users_by_id: dict[str, str] = {}
        groups_by_id: dict[str, str] = {}
        service_principals_by_id: dict[str, str] = {}

        users: list[ImportUserResource] = []
        for user in raw_users:
            email = user.get("userName")
            if not email:
                continue
            users_by_id[str(user.get("id", ""))] = str(email)
            users.append(
                ImportUserResource(
                    email=str(email),
                    display_name=user.get("displayName"),
                )
            )

        service_principals: list[ImportServicePrincipalResource] = []
        for principal in raw_service_principals:
            name = principal.get("displayName") or principal.get("applicationId")
            if not name:
                continue
            service_principals_by_id[str(principal.get("id", ""))] = str(name)
            service_principals.append(
                ImportServicePrincipalResource(
                    name=str(name),
                    application_id=principal.get("applicationId"),
                )
            )

        for group in raw_groups:
            name = group.get("displayName")
            if name:
                groups_by_id[str(group.get("id", ""))] = str(name)

        group_details: list[ImportGroupResource] = []
        for group in raw_groups:
            name = group.get("displayName")
            if not name:
                continue
            if not include_system and str(name).lower() in self.SYSTEM_GROUP_NAMES:
                continue
            members: dict[str, list[str]] = {"users": [], "groups": [], "service_principals": []}
            for member in group.get("members", []) or []:
                member_id = str(member.get("value", ""))
                if member_id in users_by_id:
                    members["users"].append(users_by_id[member_id])
                elif member_id in groups_by_id:
                    members["groups"].append(groups_by_id[member_id])
                elif member_id in service_principals_by_id:
                    members["service_principals"].append(service_principals_by_id[member_id])
            group_details.append(
                ImportGroupResource(
                    name=str(name),
                    members={key: sorted(values) for key, values in members.items() if values},
                )
            )

        return users, group_details, service_principals

    def _safe_show_grants(self, securable_type: str, securable_name: str) -> list[ImportGrantResource]:
        if not self.auth.resolve_sql_warehouse_id():
            return []
        try:
            grants = self.client.show_grants(securable_type=securable_type, securable_name=securable_name)
        except ProviderError:
            return []
        return [
            ImportGrantResource(
                principal=str(grant["principal"]),
                privilege=str(grant["privilege"]).upper(),
                securable_type=str(grant["securable_type"]).lower(),
                securable_name=str(grant["securable_name"]),
            )
            for grant in grants
            if grant.get("principal") and grant.get("privilege")
        ]
