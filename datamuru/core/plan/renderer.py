from __future__ import annotations

import hashlib
import json

from .models import Plan, ResourceDescriptor


def fingerprint(resource: ResourceDescriptor) -> str:
    payload = json.dumps(resource.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def summarize_changes(plan: Plan) -> list[str]:
    return [f"{change.action}:{change.resource.address}" for change in plan.changes]
