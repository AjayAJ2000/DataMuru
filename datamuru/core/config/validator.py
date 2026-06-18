from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from datamuru.edition import EditionCatalog
from datamuru.types import ValidationIssue
from datamuru.providers.databricks.auth import DatabricksAuthConfig

from .parser import load_yaml


class SchemaValidator:
    ROOT_REQUIRED = {"project", "environments", "default_environment", "features", "state", "provider"}
    EDITIONS = {"open-source", "enterprise"}
    BACKENDS = {"local", "s3", "azure_blob", "gcs"}
    CLOUDS = {"azure", "aws", "gcp", "snowflake"}

    def validate_root(self, raw: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for key in sorted(self.ROOT_REQUIRED - raw.keys()):
            issues.append(ValidationIssue(level="error", path=key, message=f"Missing required root key '{key}'."))
        if issues:
            return issues

        project = raw.get("project", {})
        if project.get("provider") and raw.get("provider", {}).get("name"):
            if project["provider"] != raw["provider"]["name"]:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path="provider.name",
                        message="Root provider.name must match project.provider.",
                    )
                )
        if project.get("edition") not in self.EDITIONS:
            issues.append(
                ValidationIssue(
                    level="error",
                    path="project.edition",
                    message="Edition must be open-source or enterprise.",
                )
            )
        if not project.get("name"):
            issues.append(ValidationIssue(level="error", path="project.name", message="Project name is required."))

        environments = raw.get("environments", [])
        names = [item.get("name") for item in environments if isinstance(item, dict)]
        seen_environment_names: set[str] = set()
        seen_environment_configs: set[str] = set()
        for index, environment in enumerate(environments):
            if not isinstance(environment, dict):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"environments.{index}",
                        message="Environment entries must be mappings with name and config.",
                    )
                )
                continue
            name = environment.get("name")
            config = environment.get("config")
            if not name:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"environments.{index}.name",
                        message="Environment name is required.",
                    )
                )
            elif name in seen_environment_names:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"environments.{index}.name",
                        message=f"Environment name '{name}' is declared more than once.",
                    )
                )
            seen_environment_names.add(name)
            if not config:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"environments.{index}.config",
                        message="Environment config path is required.",
                    )
                )
            elif config in seen_environment_configs:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"environments.{index}.config",
                        message=f"Environment config path '{config}' is reused.",
                    )
                )
            seen_environment_configs.add(config)
        if raw.get("default_environment") not in names:
            issues.append(
                ValidationIssue(
                    level="error",
                    path="default_environment",
                    message="Default environment must match one of environments[].name.",
                )
            )

        state = raw.get("state", {})
        if state.get("backend") not in self.BACKENDS:
            issues.append(ValidationIssue(level="error", path="state.backend", message="Unsupported state backend."))
        if not state.get("path"):
            issues.append(ValidationIssue(level="error", path="state.path", message="State path is required."))

        provider = raw.get("provider", {})
        if provider.get("cloud") not in self.CLOUDS:
            issues.append(
                ValidationIssue(
                    level="error",
                    path="provider.cloud",
                    message="Provider cloud must be azure, aws, or gcp.",
                )
            )
        if not provider.get("config"):
            issues.append(
                ValidationIssue(
                    level="error",
                    path="provider.config",
                    message="Provider config path is required.",
                )
            )

        issues.extend(EditionCatalog.validate_features(project.get("edition", ""), raw.get("features", {})))
        return issues

    def validate_workspace(self, raw: dict[str, Any], path: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if "principals" in raw:
            issues.append(
                ValidationIssue(
                    level="error",
                    path=f"{path}.principals",
                    message="Workspace principals must be nested under the workspace mapping.",
                )
            )
        workspace = raw.get("workspace")
        if not isinstance(workspace, dict):
            issues.append(
                ValidationIssue(
                    level="error",
                    path=path,
                    message="Workspace file must contain a workspace mapping.",
                )
            )
            return issues
        for key in ("name", "cloud", "region"):
            if not workspace.get(key):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.{key}",
                        message=f"Workspace {key} is required.",
                    )
                )
        principals = workspace.get("principals") or {}
        if not isinstance(principals, dict):
            issues.append(
                ValidationIssue(
                    level="error",
                    path=f"{path}.workspace.principals",
                    message="Workspace principals must be a mapping.",
                )
            )
            return issues
        issues.extend(self._validate_principals(principals, path))
        issues.extend(self._validate_catalogs(workspace, path))
        return issues

    def validate_workspace_against_root(
        self,
        raw: dict[str, Any],
        *,
        root_cloud: str,
        path: str,
    ) -> list[ValidationIssue]:
        workspace = raw.get("workspace") or {}
        if not isinstance(workspace, dict):
            return []
        cloud = workspace.get("cloud")
        if cloud and root_cloud and cloud != root_cloud:
            return [
                ValidationIssue(
                    level="error",
                    path=f"{path}.workspace.cloud",
                    message=f"Workspace cloud '{cloud}' must match root provider.cloud '{root_cloud}'.",
                )
            ]
        return []

    def _validate_catalogs(self, workspace: dict[str, Any], path: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        seen_catalogs: set[str] = set()
        for catalog_index, catalog in enumerate(workspace.get("catalogs") or []):
            if not isinstance(catalog, dict) or not catalog.get("name"):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.catalogs.{catalog_index}",
                        message="Catalog entries require a name.",
                    )
                )
                continue
            catalog_name = str(catalog["name"])
            if catalog_name in seen_catalogs:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.catalogs.{catalog_index}.name",
                        message=f"Catalog '{catalog_name}' is declared more than once in this workspace.",
                    )
                )
            seen_catalogs.add(catalog_name)
            seen_schemas: set[str] = set()
            for schema_index, schema in enumerate(catalog.get("schemas") or []):
                schema_name = self._schema_name(schema)
                if not schema_name:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.workspace.catalogs.{catalog_index}.schemas.{schema_index}",
                            message="Schema entries must be a name string or a mapping with name.",
                        )
                    )
                    continue
                if schema_name == "information_schema":
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.workspace.catalogs.{catalog_index}.schemas.{schema_index}",
                            message="information_schema is system-owned and cannot be declared as a managed schema.",
                        )
                    )
                if schema_name in seen_schemas:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.workspace.catalogs.{catalog_index}.schemas.{schema_index}",
                            message=f"Schema '{schema_name}' is declared more than once in catalog '{catalog_name}'.",
                        )
                    )
                seen_schemas.add(schema_name)
        return issues

    @staticmethod
    def _schema_name(schema: Any) -> str | None:
        if isinstance(schema, str):
            return schema
        if isinstance(schema, dict):
            value = schema.get("name")
            return str(value) if value else None
        return None

    def _validate_principals(self, principals: dict[str, Any], path: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        managed_identity_count = 0
        for index, user in enumerate(principals.get("users", [])):
            if isinstance(user, str):
                continue
            if not isinstance(user, dict) or not user.get("email"):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.principals.users.{index}",
                        message="Managed user entries require an email.",
                    )
                )
                continue
            issues.extend(self._validate_identity_lifecycle(user, f"{path}.workspace.principals.users.{index}"))
            is_managed = user.get("lifecycle", "existing") == "managed"
            managed_identity_count += is_managed
            email = str(user["email"]).strip().lower()
            domain = email.rpartition("@")[2]
            if is_managed and domain in {"example.com", "example.net", "example.org"}:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.principals.users.{index}.email",
                        message=(
                            "Managed users require a real account email; replace the reserved example-domain address."
                        ),
                    )
                )

        for index, group in enumerate(principals.get("groups", [])):
            if isinstance(group, str):
                continue
            if not isinstance(group, dict) or not group.get("name"):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.principals.groups.{index}",
                        message="Managed group entries require a name.",
                    )
                )
                continue
            group_path = f"{path}.workspace.principals.groups.{index}"
            issues.extend(self._validate_identity_lifecycle(group, group_path))
            managed_identity_count += group.get("lifecycle", "existing") == "managed"
            members = group.get("members", {})
            if members is not None and not isinstance(members, dict):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{group_path}.members",
                        message="Group members must be a mapping of users, groups, and service_principals.",
                    )
                )

        for index, principal in enumerate(principals.get("service_principals", [])):
            if isinstance(principal, str):
                continue
            if not isinstance(principal, dict) or not principal.get("name"):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.workspace.principals.service_principals.{index}",
                        message="Managed service principal entries require a name.",
                    )
                )
                continue
            issues.extend(
                self._validate_identity_lifecycle(
                    principal,
                    f"{path}.workspace.principals.service_principals.{index}",
                )
            )
            managed_identity_count += principal.get("lifecycle", "existing") == "managed"

        if managed_identity_count:
            issues.append(
                ValidationIssue(
                    level="info",
                    path=f"{path}.workspace.principals",
                    message=(
                        "Managed identity declarations detected. DataMuru will verify Databricks account SCIM "
                        "capability during doctor, plan, and apply."
                    ),
                )
            )
        return issues

    @staticmethod
    def _validate_identity_lifecycle(identity: dict[str, Any], path: str) -> list[ValidationIssue]:
        lifecycle = identity.get("lifecycle", "existing")
        if lifecycle not in {"existing", "managed", "external"}:
            return [
                ValidationIssue(
                    level="error",
                    path=f"{path}.lifecycle",
                    message="Identity lifecycle must be existing, managed, or external.",
                )
            ]
        return []

    def validate_taxonomy(self, raw: dict[str, Any], path: str) -> list[ValidationIssue]:
        taxonomy = raw.get("taxonomy") or {}
        categories = taxonomy.get("categories") or []
        issues: list[ValidationIssue] = []
        if not taxonomy.get("name"):
            issues.append(
                ValidationIssue(level="error", path=f"{path}.taxonomy.name", message="Taxonomy name is required.")
            )
        seen: set[str] = set()
        for category in categories:
            category_id = category.get("id")
            if not category_id:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.taxonomy.categories",
                        message="Every category needs an id.",
                    )
                )
                continue
            if category_id in seen:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.taxonomy.categories.{category_id}",
                        message="Category ids must be unique.",
                    )
                )
            seen.add(category_id)
        return issues

    def validate_rbac(self, raw: dict[str, Any], path: str) -> list[ValidationIssue]:
        rbac = raw.get("rbac") or {}
        issues: list[ValidationIssue] = []
        if not (rbac.get("roles") or []):
            issues.append(
                ValidationIssue(
                    level="error",
                    path=f"{path}.rbac.roles",
                    message="At least one RBAC role is required.",
                )
            )
        roles = rbac.get("roles") or []
        role_ids: set[str] = set()
        for index, role in enumerate(roles):
            if not isinstance(role, dict) or not role.get("id"):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.rbac.roles.{index}",
                        message="Every RBAC role requires an id.",
                    )
                )
                continue
            role_id = str(role["id"])
            if role_id in role_ids:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.rbac.roles.{index}.id",
                        message=f"RBAC role '{role_id}' is declared more than once.",
                    )
                )
            role_ids.add(role_id)
            for inherited_role in role.get("inherits") or []:
                if inherited_role == role_id:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.rbac.roles.{index}.inherits",
                            message=f"RBAC role '{role_id}' cannot inherit from itself.",
                        )
                    )
                elif inherited_role not in role_ids and not any(
                    isinstance(candidate, dict) and candidate.get("id") == inherited_role for candidate in roles
                ):
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.rbac.roles.{index}.inherits",
                            message=f"RBAC role '{role_id}' inherits unknown role '{inherited_role}'.",
                        )
                    )
            for permission_index, permission in enumerate(role.get("permissions") or []):
                if not isinstance(permission, dict):
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.rbac.roles.{index}.permissions.{permission_index}",
                            message="RBAC permissions must be mappings.",
                        )
                    )
                    continue
                for key in ("resource_type", "resource_pattern", "privilege"):
                    if not permission.get(key):
                        issues.append(
                            ValidationIssue(
                                level="error",
                                path=f"{path}.rbac.roles.{index}.permissions.{permission_index}.{key}",
                                message=f"RBAC permission {key} is required.",
                            )
                        )
        if not (rbac.get("assignments") or []):
            issues.append(
                ValidationIssue(
                    level="warning",
                    path=f"{path}.rbac.assignments",
                    message="No RBAC assignments defined yet.",
                )
            )
        for assignment_index, assignment in enumerate(rbac.get("assignments") or []):
            if not isinstance(assignment, dict):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{path}.rbac.assignments.{assignment_index}",
                        message="RBAC assignments must be mappings.",
                    )
                )
                continue
            for key in ("principal", "roles"):
                if not assignment.get(key):
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.rbac.assignments.{assignment_index}.{key}",
                            message=f"RBAC assignment {key} is required.",
                        )
                    )
            for role_id in assignment.get("roles") or []:
                if role_id not in role_ids:
                    issues.append(
                        ValidationIssue(
                            level="error",
                            path=f"{path}.rbac.assignments.{assignment_index}.roles",
                            message=f"RBAC assignment references unknown role '{role_id}'.",
                        )
                    )
        return issues

    def validate_provider(self, raw: dict[str, Any], *, provider_name: str, path: str) -> list[ValidationIssue]:
        if provider_name != "databricks":
            return []
        try:
            DatabricksAuthConfig.from_provider_data(raw)
        except PydanticValidationError as exc:
            issues: list[ValidationIssue] = []
            for error in exc.errors():
                location = ".".join(str(item) for item in error.get("loc", ()))
                field_path = f"{path}.provider.{location}" if location else f"{path}.provider"
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=field_path,
                        message=error.get("msg", "Invalid provider configuration."),
                    )
                )
            return issues
        return []


def validate_project(config_path: Path) -> list[ValidationIssue]:
    validator = SchemaValidator()
    root_raw = load_yaml(config_path)
    issues = validator.validate_root(root_raw)
    if issues:
        return issues

    project_root = config_path.parent
    for environment in root_raw.get("environments", []):
        env_path = project_root / environment["config"]
        if not env_path.exists():
            issues.append(
                ValidationIssue(
                    level="error",
                    path=f"environments.{environment['name']}",
                    message=f"Missing environment file: {env_path}",
                )
            )

    provider_name = root_raw["provider"].get("name", "")
    provider_path = project_root / root_raw["provider"]["config"]
    if not provider_path.exists():
        issues.append(
            ValidationIssue(
                level="error",
                path="provider.config",
                message=f"Missing provider config file: {provider_path}",
            )
        )
    else:
        issues.extend(
            validator.validate_provider(
                load_yaml(provider_path),
                provider_name=provider_name,
                path=provider_path.name,
            )
        )

    for workspace_path in sorted((project_root / "workspaces").glob("*.yml")):
        workspace_raw = load_yaml(workspace_path)
        issues.extend(validator.validate_workspace(workspace_raw, workspace_path.name))
        issues.extend(
            validator.validate_workspace_against_root(
                workspace_raw,
                root_cloud=root_raw["provider"].get("cloud", ""),
                path=workspace_path.name,
            )
        )
        principals = (workspace_raw.get("workspace") or {}).get("principals") or {}
        managed_identities = any(
            isinstance(item, dict) and item.get("lifecycle", "existing") == "managed"
            for collection in ("users", "groups", "service_principals")
            for item in principals.get(collection, [])
        )
        if managed_identities:
            edition = root_raw.get("project", {}).get("edition")
            identity_enabled = root_raw.get("features", {}).get("identity_management", False)
            if edition != "enterprise":
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"{workspace_path.name}.workspace.principals",
                        message="Managed identity lifecycle requires project.edition: enterprise.",
                    )
                )
            if not identity_enabled:
                issues.append(
                    ValidationIssue(
                        level="error",
                        path="features.identity_management",
                        message="Managed identity lifecycle requires features.identity_management: true.",
                    )
                )

    taxonomy_path = project_root / "governance" / "taxonomy.yml"
    if taxonomy_path.exists():
        issues.extend(validator.validate_taxonomy(load_yaml(taxonomy_path), taxonomy_path.name))

    rbac_path = project_root / "governance" / "rbac.yml"
    if rbac_path.exists():
        issues.extend(validator.validate_rbac(load_yaml(rbac_path), rbac_path.name))

    return issues
