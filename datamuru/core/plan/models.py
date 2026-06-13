from __future__ import annotations

from typing import Any

from pydantic import Field

from datamuru.modeling import DataMuruModel


class ResourceDescriptor(DataMuruModel):
    resource_type: str
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)

    @property
    def address(self) -> str:
        return f"{self.resource_type}:{self.name}"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceDescriptor":
        return cls.model_validate(data)


class PlanChange(DataMuruModel):
    action: str
    resource: ResourceDescriptor
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "resource": self.resource.to_dict(),
            "before": self.before,
            "after": self.after,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlanChange":
        return cls.model_validate(data)


class Plan(DataMuruModel):
    environment: str
    changes: list[PlanChange] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "changes": [change.to_dict() for change in self.changes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Plan":
        return cls.model_validate(data)
