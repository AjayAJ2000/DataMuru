from __future__ import annotations

from typing import Any

from datamuru.edition import EditionCatalog
from datamuru.types import ValidationIssue


class SchemaValidator:
    ROOT_REQUIRED = {"project", "environments", "default_environment", "features", "state", "provider"}
    EDITIONS = {"open-source", "enterprise"}
    BACKENDS = {"local", "s3", "azure_blob", "gcs"}
    CLOUDS = {"azure", "aws", "gcp"}

    def validate_root(self, raw: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for key in sorted(self.ROOT_REQUIRED - raw.keys()):
            issues.append(ValidationIssue("error", key, f"Missing required root key '{key}'."))
        if issues:
            return issues

        project = raw.get("project", {})
        if project.get("edition") not in self.EDITIONS:
            issues.append(ValidationIssue("error", "project.edition", "Edition must be open-source or enterprise."))
        if not project.get("name"):
            issues.append(ValidationIssue("error", "project.name", "Project name is required."))

        environments = raw.get("environments", [])
        names = [item.get("name") for item in environments if isinstance(item, dict)]
        if raw.get("default_environment") not in names:
            issues.append(
                ValidationIssue(
                    "error",
                    "default_environment",
                    "Default environment must match one of environments[].name.",
                )
            )

        state = raw.get("state", {})
        if state.get("backend") not in self.BACKENDS:
            issues.append(ValidationIssue("error", "state.backend", "Unsupported state backend."))
        if not state.get("path"):
            issues.append(ValidationIssue("error", "state.path", "State path is required."))

        provider = raw.get("provider", {})
        if provider.get("cloud") not in self.CLOUDS:
            issues.append(ValidationIssue("error", "provider.cloud", "Provider cloud must be azure, aws, or gcp."))
        if not provider.get("config"):
            issues.append(ValidationIssue("error", "provider.config", "Provider config path is required."))

        issues.extend(EditionCatalog.validate_features(project.get("edition", ""), raw.get("features", {})))

        return issues

    def validate_workspace(self, raw: dict[str, Any], path: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        workspace = raw.get("workspace")
        if not isinstance(workspace, dict):
            return [ValidationIssue("error", path, "Workspace file must contain a workspace mapping.")]
        for key in ("name", "cloud", "region"):
            if not workspace.get(key):
                issues.append(ValidationIssue("error", f"{path}.workspace.{key}", f"Workspace {key} is required."))
        return issues

    def validate_taxonomy(self, raw: dict[str, Any], path: str) -> list[ValidationIssue]:
        taxonomy = raw.get("taxonomy") or {}
        categories = taxonomy.get("categories") or []
        issues: list[ValidationIssue] = []
        if not taxonomy.get("name"):
            issues.append(ValidationIssue("error", f"{path}.taxonomy.name", "Taxonomy name is required."))
        seen: set[str] = set()
        for category in categories:
            category_id = category.get("id")
            if not category_id:
                issues.append(ValidationIssue("error", f"{path}.taxonomy.categories", "Every category needs an id."))
                continue
            if category_id in seen:
                issues.append(ValidationIssue("error", f"{path}.taxonomy.categories.{category_id}", "Category ids must be unique."))
            seen.add(category_id)
        return issues

    def validate_rbac(self, raw: dict[str, Any], path: str) -> list[ValidationIssue]:
        rbac = raw.get("rbac") or {}
        issues: list[ValidationIssue] = []
        roles = rbac.get("roles") or []
        assignments = rbac.get("assignments") or []
        if not roles:
            issues.append(ValidationIssue("error", f"{path}.rbac.roles", "At least one RBAC role is required."))
        if not assignments:
            issues.append(ValidationIssue("warning", f"{path}.rbac.assignments", "No RBAC assignments defined yet."))
        return issues
