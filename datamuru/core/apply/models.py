from __future__ import annotations

from typing import Any

from pydantic import Field

from datamuru.modeling import DataMuruModel


class ApplyFailure(DataMuruModel):
    resource: str
    reason: str
    code: str | None = None
    title: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    suggestion: str | None = None


class ApplyResult(DataMuruModel):
    success: bool
    applied: list[str] = Field(default_factory=list)
    failures: list[ApplyFailure] = Field(default_factory=list)
