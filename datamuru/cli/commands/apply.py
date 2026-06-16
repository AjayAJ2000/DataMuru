from __future__ import annotations

import json
from pathlib import Path

import click

from datamuru.api import DataMuru
from datamuru.core.plan import load_saved_plan_document
from datamuru.errors import SavedPlanError
from datamuru.types import Plan

from ..guard import with_cli_errors
from ..output import console


@click.command("apply")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--target", default=None)
@click.option("--plan", "plan_path", default=None)
@click.option("--auto-approve", is_flag=True, default=False)
@with_cli_errors
def apply_command(config_path: str, target: str | None, plan_path: str | None, auto_approve: bool) -> None:
    if not auto_approve:
        raise click.ClickException("Alpha bootstrap requires --auto-approve for non-interactive apply.")
    dm = DataMuru(config_path=config_path)
    preview_plan: Plan | None = None
    if plan_path:
        try:
            saved_plan_payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SavedPlanError(
                description="Saved plan file is not valid JSON.",
                context={"plan_path": plan_path, "json_error": str(exc)},
            ) from exc
        preview_plan = load_saved_plan_document(saved_plan_payload).plan
        result = dm.apply_saved_plan(plan_path)
    else:
        preview_plan = dm.plan(target=target)
        if target and not preview_plan.changes:
            console.print(f"[warning]Target '{target}' matched nothing; apply skipped.[/warning]")
            return
        result = dm.apply(target=target)
    if not result.success:
        for failure in result.failures:
            console.print(f"[error]FAILED[/error] {failure.resource}: {failure.reason}")
        raise SystemExit(1)
    noop_count = 0
    if preview_plan is not None:
        noop_count = sum(1 for change in preview_plan.changes if change.action == "noop")
    message = f"[success]Applied[/success] {len(result.applied)} changes."
    if noop_count:
        message += f" [muted]{noop_count} resources already matched.[/muted]"
    console.print(message)
