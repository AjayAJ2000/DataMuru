from __future__ import annotations

from typing import Any


class DataMuruError(Exception):
    """Base exception with product-grade metadata for user-facing failures."""

    default_code = "DMR-0000"
    default_title = "DataMuru Error"
    default_suggestion = "Review the error context and retry."

    def __init__(
        self,
        description: str,
        *,
        code: str | None = None,
        title: str | None = None,
        context: dict[str, Any] | None = None,
        suggestion: str | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(description)
        self.code = code or self.default_code
        self.title = title or self.default_title
        self.description = description
        self.context = context or {}
        self.suggestion = suggestion or self.default_suggestion
        self.exit_code = exit_code

    def render(self) -> str:
        return f"{self.code} {self.title}: {self.description}"


class ConfigLoadError(DataMuruError):
    default_code = "DMR-CFG-1001"
    default_title = "Configuration Load Failed"
    default_suggestion = "Check the file path, YAML syntax, and interpolation values."


class ValidationError(DataMuruError):
    default_code = "DMR-CFG-1002"
    default_title = "Configuration Validation Failed"
    default_suggestion = "Fix the reported configuration issues and run validate again."

    def __init__(
        self,
        description: str | None = None,
        *,
        issues: list[Any] | None = None,
        context: dict[str, Any] | None = None,
        suggestion: str | None = None,
        exit_code: int = 1,
    ) -> None:
        self.issues = issues or []
        if description is None and self.issues:
            description = "; ".join(
                f"{issue.path}: {issue.message}" for issue in self.issues if hasattr(issue, "path")
            )
        super().__init__(
            description or "Configuration validation failed.",
            context=context or {"issue_count": len(self.issues)},
            suggestion=suggestion,
            exit_code=exit_code,
        )


class ProviderError(DataMuruError):
    default_code = "DMR-PROV-1001"
    default_title = "Provider Operation Failed"
    default_suggestion = "Verify provider credentials and workspace settings."


class SavedPlanError(DataMuruError):
    default_code = "DMR-PLAN-1001"
    default_title = "Saved Plan Error"
    default_suggestion = "Regenerate the plan file and retry."


class StateBackendError(DataMuruError):
    default_code = "DMR-STATE-1001"
    default_title = "State Backend Error"
    default_suggestion = "Check the configured backend and state file permissions."


class ImportAdoptionError(DataMuruError):
    default_code = "DMR-IMPORT-1001"
    default_title = "Import Adoption Blocked"
    default_suggestion = "Resolve every reported conflict or missing live resource, then preview adoption again."


class EnterpriseFulfillmentError(DataMuruError):
    default_code = "DMR-ENT-1001"
    default_title = "Enterprise Fulfillment Error"
    default_suggestion = "Fix the purchase request and retry the offline fulfillment workflow."


class UnsupportedOperationError(DataMuruError):
    default_code = "DMR-CORE-1001"
    default_title = "Unsupported Operation"
    default_suggestion = "Use a supported alpha workflow or implement the missing capability."


ConfigError = ConfigLoadError
