from __future__ import annotations

from typing import Any

from pydantic import Field

from datamuru.modeling import DataMuruModel


class StateResourceRecord(DataMuruModel):
    fingerprint: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class StateSnapshot(DataMuruModel):
    resources: dict[str, StateResourceRecord] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resources": {
                address: record.model_dump(mode="python") for address, record in self.resources.items()
            }
        }

    def merged_with(self, other: "StateSnapshot") -> "StateSnapshot":
        merged = dict(self.resources)
        merged.update(other.resources)
        return StateSnapshot(resources=merged)
