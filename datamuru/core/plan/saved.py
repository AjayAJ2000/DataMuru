from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from datamuru.core.config.models import LoadedProject
from datamuru.errors import SavedPlanError
from datamuru.modeling import DataMuruModel

from .models import Plan

SAVED_PLAN_SCHEMA_VERSION = "datamuru.saved_plan.v1"


class SavedPlanMetadata(DataMuruModel):
    schema_version: str
    created_at: str
    project_name: str
    project_version: str
    environment: str
    provider: str
    provider_cloud: str
    config_fingerprint: str
    target: str | None = None


class SavedPlanDocument(DataMuruModel):
    metadata: SavedPlanMetadata
    plan: Plan

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.model_dump(mode="python"),
            "plan": self.plan.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SavedPlanDocument":
        try:
            document = cls.model_validate(data)
        except PydanticValidationError as exc:
            raise SavedPlanError(
                description="Saved plan file does not match the expected DataMuru plan contract.",
                context={"validation_error": str(exc)},
            ) from exc
        if document.metadata.schema_version != SAVED_PLAN_SCHEMA_VERSION:
            raise SavedPlanError(
                description="Saved plan schema version is not supported.",
                context={
                    "expected_schema_version": SAVED_PLAN_SCHEMA_VERSION,
                    "actual_schema_version": document.metadata.schema_version,
                },
            )
        return document


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def config_fingerprint(project: LoadedProject, environment: str) -> str:
    payload = {
        "root": project.root.model_dump(mode="python"),
        "environment": environment,
        "environment_data": project.environment_data,
        "provider_data": project.provider_data,
        "workspaces": [
            {
                "path": str(workspace.path.relative_to(project.root_path)),
                "raw": workspace.raw,
            }
            for workspace in sorted(project.workspaces, key=lambda item: str(item.path))
        ],
        "governance": project.governance.model_dump(mode="python"),
    }
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def build_saved_plan_document(
    *,
    project: LoadedProject,
    environment: str,
    plan: Plan,
    target: str | None,
) -> SavedPlanDocument:
    return SavedPlanDocument(
        metadata=SavedPlanMetadata(
            schema_version=SAVED_PLAN_SCHEMA_VERSION,
            created_at=datetime.now(UTC).isoformat(),
            project_name=project.root.project.name,
            project_version=project.root.project.version,
            environment=environment,
            provider=project.root.provider.name,
            provider_cloud=project.root.provider.cloud,
            config_fingerprint=config_fingerprint(project, environment),
            target=target,
        ),
        plan=plan,
    )


def load_saved_plan_document(data: dict[str, Any]) -> SavedPlanDocument:
    return SavedPlanDocument.from_dict(data)


def validate_saved_plan_document(
    document: SavedPlanDocument,
    *,
    project: LoadedProject,
    environment: str,
) -> None:
    expected_fingerprint = config_fingerprint(project, environment)
    metadata = document.metadata
    if metadata.environment != environment:
        raise SavedPlanError(
            description="Saved plan environment does not match the selected environment.",
            context={"plan_environment": metadata.environment, "current_environment": environment},
        )
    if metadata.project_name != project.root.project.name:
        raise SavedPlanError(
            description="Saved plan project does not match the current configuration.",
            context={"plan_project": metadata.project_name, "current_project": project.root.project.name},
        )
    if metadata.provider != project.root.provider.name or metadata.provider_cloud != project.root.provider.cloud:
        raise SavedPlanError(
            description="Saved plan provider does not match the current configuration.",
            context={
                "plan_provider": metadata.provider,
                "current_provider": project.root.provider.name,
                "plan_cloud": metadata.provider_cloud,
                "current_cloud": project.root.provider.cloud,
            },
        )
    if metadata.config_fingerprint != expected_fingerprint:
        raise SavedPlanError(
            description="Saved plan is stale because the project configuration changed after the plan was created.",
            context={
                "plan_config_fingerprint": metadata.config_fingerprint,
                "current_config_fingerprint": expected_fingerprint,
            },
            suggestion="Run plan again and apply the newly generated saved-plan artifact.",
        )
