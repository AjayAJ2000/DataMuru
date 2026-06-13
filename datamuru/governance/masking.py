from __future__ import annotations

from datamuru.types import ResourceDescriptor


def compile_masking_resources(governance) -> list[ResourceDescriptor]:
    if not governance.masking:
        return []
    masking = governance.masking.get("masking", {})
    resources: list[ResourceDescriptor] = []
    for builtin in masking.get("builtins", []):
        resources.append(
            ResourceDescriptor(
                resource_type="column_mask",
                name=builtin["id"],
                attributes={"strategy": builtin.get("strategy"), "description": builtin.get("description")},
            )
        )
    return resources
