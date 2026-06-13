from __future__ import annotations

from dataclasses import dataclass

from datamuru.types import ValidationIssue


@dataclass(frozen=True, slots=True)
class EditionDefinition:
    name: str
    allowed_features: set[str]


class EditionCatalog:
    BASE_FEATURES = {
        "governance",
        "data_mesh",
        "ingestion",
        "modeling",
        "observability",
    }
    ENTERPRISE_ONLY_FEATURES = {
        "compliance_reporting",
        "multi_workspace",
        "hosted_control_plane",
        "identity_management",
    }

    DEFINITIONS = {
        "open-source": EditionDefinition(
            name="open-source",
            allowed_features=BASE_FEATURES,
        ),
        "enterprise": EditionDefinition(
            name="enterprise",
            allowed_features=BASE_FEATURES | ENTERPRISE_ONLY_FEATURES,
        ),
    }

    @classmethod
    def validate_features(cls, edition: str, features: dict[str, object]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        definition = cls.DEFINITIONS.get(edition)
        if definition is None:
            issues.append(
                ValidationIssue(
                    level="error",
                    path="project.edition",
                    message=f"Unsupported edition '{edition}'.",
                )
            )
            return issues

        for feature_name, enabled in features.items():
            if feature_name not in definition.allowed_features:
                if enabled is False:
                    continue
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"features.{feature_name}",
                        message=f"Feature '{feature_name}' is not available in edition '{edition}'.",
                    )
                )
                continue
            if not isinstance(enabled, bool):
                issues.append(
                    ValidationIssue(
                        level="error",
                        path=f"features.{feature_name}",
                        message="Feature flags must be boolean values.",
                    )
                )
        return issues
