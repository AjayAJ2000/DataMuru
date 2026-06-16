from __future__ import annotations

from datamuru.core.plan import fingerprint
from datamuru.errors import DataMuruError
from datamuru.types import ApplyFailure, ApplyResult, Plan


def apply_plan(plan: Plan, provider, state_backend) -> ApplyResult:
    state = state_backend.load()
    resources = state.setdefault("resources", {})
    applied: list[str] = []
    failures: list[ApplyFailure] = []

    for change in plan.changes:
        try:
            if change.action == "noop":
                continue
            if change.action == "destroy":
                provider.destroy_resource(change.resource)
                resources.pop(change.resource.address, None)
            else:
                provider.apply_resource(change.resource)
                resources[change.resource.address] = {
                    "fingerprint": fingerprint(change.resource),
                    "attributes": change.resource.attributes,
                }
            applied.append(change.resource.address)
        except Exception as exc:  # pragma: no cover
            if isinstance(exc, DataMuruError):
                failures.append(
                    ApplyFailure(
                        resource=change.resource.address,
                        reason=exc.description,
                        code=exc.code,
                        title=exc.title,
                        context=exc.context,
                        suggestion=exc.suggestion,
                    )
                )
            else:
                failures.append(ApplyFailure(resource=change.resource.address, reason=str(exc)))

    state_backend.save(state)
    return ApplyResult(success=not failures, applied=applied, failures=failures)
