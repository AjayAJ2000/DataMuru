from __future__ import annotations

from datamuru.core.plan.models import Plan

from .executor import PlanExecutor
from .models import ApplyResult


def apply_plan(plan: Plan, provider, state_backend) -> ApplyResult:
    return PlanExecutor().execute(plan=plan, provider=provider, state_backend=state_backend)
