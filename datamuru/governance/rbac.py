from __future__ import annotations

from datamuru.types import ResourceDescriptor


def compile_rbac_resources(governance) -> list[ResourceDescriptor]:
    if not governance.rbac:
        return []
    rbac = governance.rbac.get("rbac", {})
    resources: list[ResourceDescriptor] = []
    role_map = {role["id"]: role for role in rbac.get("roles", [])}
    for role in rbac.get("roles", []):
        resources.append(
            ResourceDescriptor(
                resource_type="rbac_role",
                name=role["id"],
                attributes={"permissions": role.get("permissions", [])},
            )
        )
    for assignment in rbac.get("assignments", []):
        for role_id in assignment.get("roles", []):
            effective_permissions = _resolve_effective_permissions(role_map, role_id)
            resources.append(
                ResourceDescriptor(
                    resource_type="permission_binding",
                    name=f"{assignment['principal']}:{role_id}",
                    attributes={
                        "principal": assignment["principal"],
                        "principal_type": assignment.get("type", "group"),
                        "role": role_id,
                        "domains": assignment.get("domains", []),
                        "inherits": role_map.get(role_id, {}).get("inherits", []),
                        "permissions": effective_permissions,
                    },
                )
            )
    return resources


def _resolve_effective_permissions(role_map: dict[str, dict], role_id: str, seen: set[str] | None = None) -> list[dict]:
    if seen is None:
        seen = set()
    if role_id in seen:
        return []
    seen.add(role_id)
    role = role_map.get(role_id, {})
    inherited_permissions: list[dict] = []
    for inherited_role in role.get("inherits", []):
        inherited_permissions.extend(_resolve_effective_permissions(role_map, inherited_role, seen=seen.copy()))
    return inherited_permissions + list(role.get("permissions", []))
