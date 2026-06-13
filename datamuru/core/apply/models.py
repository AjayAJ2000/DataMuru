from __future__ import annotations

from pydantic import Field

from datamuru.modeling import DataMuruModel


class ApplyFailure(DataMuruModel):
    resource: str
    reason: str


class ApplyResult(DataMuruModel):
    success: bool
    applied: list[str] = Field(default_factory=list)
    failures: list[ApplyFailure] = Field(default_factory=list)
