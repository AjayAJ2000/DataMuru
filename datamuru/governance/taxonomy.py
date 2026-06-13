from __future__ import annotations

from datamuru.types import ResourceDescriptor


def compile_taxonomy_resources(governance) -> list[ResourceDescriptor]:
    if not governance.taxonomy:
        return []
    taxonomy = governance.taxonomy.get("taxonomy", {})
    resources = [
        ResourceDescriptor(
            resource_type="taxonomy",
            name=taxonomy.get("name", "unnamed-taxonomy"),
            attributes={"version": taxonomy.get("version", "0")},
        )
    ]
    for category in taxonomy.get("categories", []):
        resources.append(
            ResourceDescriptor(
                resource_type="classification",
                name=category["id"],
                attributes={
                    "label": category.get("label"),
                    "parent": category.get("parent"),
                    "masking": category.get("handling", {}).get("masking"),
                },
            )
        )
    return resources
