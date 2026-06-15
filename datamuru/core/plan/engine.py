from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from datamuru.core.state.models import StateSnapshot

from .models import Plan, PlanChange, ResourceDescriptor
from .renderer import fingerprint


def matches_target(address: str, target: str | None) -> bool:
    if target is None:
        return True
    if address == target:
        return True
    target_type, separator, target_name = target.partition(":")
    if not separator or not target_name:
        return False
    if target_type == "catalog":
        return address.startswith(f"schema:{target_name}.")
    if target_type == "group":
        return address.startswith(f"group_membership:{target_name}:")
    return False


def _normalize_existing(current_state: StateSnapshot | dict[str, Any]) -> dict[str, dict[str, Any]]:
    if isinstance(current_state, StateSnapshot):
        return {
            address: record.model_dump(mode="python") for address, record in current_state.resources.items()
        }
    return current_state


class PlanEngine:
    def build(
        self,
        *,
        environment: str,
        desired_resources: Iterable[ResourceDescriptor],
        current_state: StateSnapshot | dict[str, Any],
        target: str | None = None,
    ) -> Plan:
        desired = {
            resource.address: resource
            for resource in desired_resources
            if matches_target(resource.address, target)
        }
        existing = {
            address: value
            for address, value in _normalize_existing(current_state).items()
            if matches_target(address, target)
        }
        changes: list[PlanChange] = []

        for address, resource in sorted(desired.items()):
            desired_fingerprint = fingerprint(resource)
            if address not in existing:
                changes.append(
                    PlanChange(
                        action="create",
                        resource=resource,
                        after={"fingerprint": desired_fingerprint},
                        reason="resource not in state",
                    )
                )
                continue

            before = existing[address]
            if before.get("fingerprint") != desired_fingerprint:
                changes.append(
                    PlanChange(
                        action="update",
                        resource=resource,
                        before=before,
                        after={"fingerprint": desired_fingerprint},
                        reason="resource definition changed",
                    )
                )
            else:
                changes.append(
                    PlanChange(
                        action="noop",
                        resource=resource,
                        before=before,
                        after=before,
                        reason="resource already matches",
                    )
                )

        for address, before in sorted(existing.items()):
            if address in desired:
                continue
            resource_type, _, name = address.partition(":")
            changes.append(
                PlanChange(
                    action="destroy",
                    resource=ResourceDescriptor(
                        resource_type=resource_type,
                        name=name,
                        attributes=before.get("attributes", {}),
                    ),
                    before=before,
                    reason="resource no longer declared",
                )
            )

        return Plan(environment=environment, changes=changes)


def build_plan(
    environment: str,
    desired_resources: Iterable[ResourceDescriptor],
    current_state: StateSnapshot | dict[str, Any],
    target: str | None = None,
) -> Plan:
    return PlanEngine().build(
        environment=environment,
        desired_resources=desired_resources,
        current_state=current_state,
        target=target,
    )
