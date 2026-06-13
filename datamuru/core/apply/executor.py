from __future__ import annotations

from datamuru.core.plan.models import Plan
from datamuru.core.plan.renderer import fingerprint
from datamuru.core.state.models import StateResourceRecord
from datamuru.errors import DataMuruError

from .models import ApplyFailure, ApplyResult


class PlanExecutor:
    def execute(self, plan: Plan, provider, state_backend) -> ApplyResult:
        state = state_backend.load()
        applied: list[str] = []
        failures: list[ApplyFailure] = []
        failed_catalogs: set[str] = set()

        for change in sorted(plan.changes, key=self._execution_order):
            try:
                if change.action == "noop":
                    continue
                if change.resource.resource_type == "schema" and change.action != "destroy":
                    catalog_name = change.resource.attributes.get("catalog") or change.resource.name.partition(".")[0]
                    if catalog_name in failed_catalogs:
                        failures.append(
                            ApplyFailure(
                                resource=change.resource.address,
                                reason=f"Skipped because parent catalog '{catalog_name}' failed earlier in this apply.",
                            )
                        )
                        continue
                if change.action == "destroy":
                    provider.destroy_resource(change.resource)
                    state.resources.pop(change.resource.address, None)
                else:
                    provider.apply_resource(change.resource)
                    state.resources[change.resource.address] = StateResourceRecord(
                        fingerprint=fingerprint(change.resource),
                        attributes=change.resource.attributes,
                    )
                applied.append(change.resource.address)
            except Exception as exc:  # pragma: no cover
                failures.append(
                    ApplyFailure(
                        resource=change.resource.address,
                        reason=self._render_failure_reason(exc),
                    )
                )
                if change.resource.resource_type == "catalog":
                    failed_catalogs.add(change.resource.name)

        state_backend.save(state)
        return ApplyResult(success=not failures, applied=applied, failures=failures)

    @staticmethod
    def _execution_order(change) -> tuple[int, str]:
        create_priority = {
            "user": 10,
            "service_principal": 10,
            "group": 20,
            "group_membership": 30,
            "catalog": 40,
            "schema": 50,
            "permission_binding": 60,
        }
        destroy_priority = {
            "permission_binding": 10,
            "group_membership": 20,
            "schema": 30,
            "catalog": 40,
            "group": 50,
            "service_principal": 60,
            "user": 60,
        }
        priorities = destroy_priority if change.action == "destroy" else create_priority
        return priorities.get(change.resource.resource_type, 100), change.resource.address

    @staticmethod
    def _render_failure_reason(exc: Exception) -> str:
        if isinstance(exc, DataMuruError):
            details = [exc.description]
            if exc.context:
                detail_parts = [f"{key}={value}" for key, value in exc.context.items()]
                details.append(f"Details: {'; '.join(detail_parts)}")
            if exc.suggestion:
                details.append(f"Suggestion: {exc.suggestion}")
            return " ".join(details)
        return str(exc)
