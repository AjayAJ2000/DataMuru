from __future__ import annotations

import hashlib
import json
from typing import Iterable

from datamuru.types import Plan, PlanChange, ResourceDescriptor


def fingerprint(resource: ResourceDescriptor) -> str:
    payload = json.dumps(resource.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _matches_target(address: str, target: str | None) -> bool:
    if target is None:
        return True
    if address == target:
        return True
    _, _, suffix = target.partition(":")
    return bool(suffix) and suffix in address


def build_plan(
    environment: str,
    desired_resources: Iterable[ResourceDescriptor],
    current_state: dict[str, dict],
    target: str | None = None,
) -> Plan:
    desired = {resource.address: resource for resource in desired_resources if _matches_target(resource.address, target)}
    existing = {address: value for address, value in current_state.items() if _matches_target(address, target)}
    changes: list[PlanChange] = []

    for address, resource in sorted(desired.items()):
        desired_fingerprint = fingerprint(resource)
        if address not in existing:
            changes.append(PlanChange("create", resource, after={"fingerprint": desired_fingerprint}, reason="resource not in state"))
            continue
        before = existing[address]
        if before.get("fingerprint") != desired_fingerprint:
            changes.append(
                PlanChange(
                    "update",
                    resource,
                    before=before,
                    after={"fingerprint": desired_fingerprint},
                    reason="resource definition changed",
                )
            )
        else:
            changes.append(PlanChange("noop", resource, before=before, after=before, reason="resource already matches"))

    for address, before in sorted(existing.items()):
        if address in desired:
            continue
        resource_type, _, name = address.partition(":")
        changes.append(
            PlanChange(
                "destroy",
                ResourceDescriptor(resource_type=resource_type, name=name, attributes=before.get("attributes", {})),
                before=before,
                reason="resource no longer declared",
            )
        )

    return Plan(environment=environment, changes=changes)
