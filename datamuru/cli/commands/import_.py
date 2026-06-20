from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import click
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.group("import")
def import_group() -> None:
    """Discover and generate starter YAML from an existing live workspace."""


@import_group.command("discover")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--catalog", "catalogs", multiple=True, help="Catalog name to include. Repeat to select multiple.")
@click.option("--include-system", is_flag=True, default=False, help="Include system catalogs, schemas, and groups.")
@click.option("--include-identities", is_flag=True, default=False, help="Include users, groups, memberships, and service principals when account SCIM is available.")
@click.option("--include-grants", is_flag=True, default=False, help="Include Unity Catalog grants when a SQL warehouse is configured.")
@click.option(
    "--grant-scope",
    default="catalog",
    show_default=True,
    type=click.Choice(["catalog", "schema", "all"]),
    help="Grant object level to scan when --include-grants is set.",
)
@click.option(
    "--max-grant-objects",
    default=500,
    show_default=True,
    type=int,
    help="Stop before grant discovery if more grant objects are in scope. Use 0 for no cap.",
)
@click.option(
    "--max-catalog-grant-objects",
    default=None,
    type=int,
    help="Stop before grant discovery if catalog objects in scope exceed this cap. Use 0 for no cap.",
)
@click.option(
    "--max-schema-grant-objects",
    default=None,
    type=int,
    help="Stop before grant discovery if schema objects in scope exceed this cap. Use 0 for no cap.",
)
@click.option(
    "--progress-checkpoint",
    default=None,
    help="Write the latest import progress event to this JSON file.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def import_discover_command(
    config_path: str,
    catalogs: tuple[str, ...],
    include_system: bool,
    include_identities: bool,
    include_grants: bool,
    grant_scope: str,
    max_grant_objects: int,
    max_catalog_grant_objects: int | None,
    max_schema_grant_objects: int | None,
    progress_checkpoint: str | None,
    output_format: str,
) -> None:
    dm = DataMuru(config_path=config_path)
    grant_cap = None if max_grant_objects == 0 else max_grant_objects
    grant_object_budgets = _grant_object_budgets(
        catalog=max_catalog_grant_objects,
        schema=max_schema_grant_objects,
    )
    if output_format == "json":
        report = dm.import_discover(
            include_system=include_system,
            include_identities=include_identities,
            include_grants=include_grants,
            catalogs=list(catalogs) or None,
            grant_scope=grant_scope,
            max_grant_objects=grant_cap,
            grant_object_budgets=grant_object_budgets,
            progress=_checkpoint_progress(progress_checkpoint).update if progress_checkpoint else None,
        )
    else:
        with _import_progress("Import discovery", checkpoint_path=progress_checkpoint) as progress_callback:
            report = dm.import_discover(
                include_system=include_system,
                include_identities=include_identities,
                include_grants=include_grants,
                catalogs=list(catalogs) or None,
                grant_scope=grant_scope,
                max_grant_objects=grant_cap,
                grant_object_budgets=grant_object_budgets,
                progress=progress_callback,
            )
    if output_format == "json":
        console.print_json(json.dumps(report.to_dict(), indent=2))
        return

    console.print(f"[primary]Import Discovery[/primary] - provider: [code]{report.provider}[/code]")
    console.print(f"[primary]Environment[/primary]: [code]{report.environment}[/code]")
    console.print(f"[primary]Workspace[/primary]: [code]{report.workspace.name}[/code]")
    console.print(f"[primary]Cloud[/primary]: [code]{report.workspace.cloud}[/code]")
    console.print(f"[primary]Region[/primary]: [code]{report.workspace.region}[/code]")
    if report.workspace.groups:
        console.print("[primary]Groups[/primary]:")
        for group_name in report.workspace.groups:
            console.print(f"  - [code]{group_name}[/code]")
    if report.workspace.users:
        console.print("[primary]Users[/primary]:")
        for user in report.workspace.users:
            console.print(f"  - [code]{user.email}[/code]")
    if report.workspace.service_principals:
        console.print("[primary]Service principals[/primary]:")
        for principal in report.workspace.service_principals:
            console.print(f"  - [code]{principal.name}[/code]")
    if report.workspace.grants:
        console.print(f"[primary]Grants[/primary]: [code]{len(report.workspace.grants)}[/code] discovered")
    if report.workspace.catalogs:
        console.print("[primary]Catalogs[/primary]:")
        for catalog in report.workspace.catalogs:
            console.print(f"  - [code]{catalog.name}[/code]")
            for schema in catalog.schemas:
                console.print(f"    - schema [code]{schema.name}[/code]")


@import_group.command("generate")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--catalog", "catalogs", multiple=True, help="Catalog name to include. Repeat to select multiple.")
@click.option("--include-groups", is_flag=True, default=False, help="Include discovered groups in principals.")
@click.option("--include-identities", is_flag=True, default=False, help="Include discovered users, group memberships, and service principals in principals.")
@click.option("--include-grants", is_flag=True, default=False, help="Generate starter RBAC assignments from live Unity Catalog grants.")
@click.option(
    "--grant-scope",
    default="catalog",
    show_default=True,
    type=click.Choice(["catalog", "schema", "all"]),
    help="Grant object level to scan when --include-grants or --suite-out is set.",
)
@click.option(
    "--max-grant-objects",
    default=500,
    show_default=True,
    type=int,
    help="Stop before grant discovery if more grant objects are in scope. Use 0 for no cap.",
)
@click.option(
    "--max-catalog-grant-objects",
    default=None,
    type=int,
    help="Stop before grant discovery if catalog objects in scope exceed this cap. Use 0 for no cap.",
)
@click.option(
    "--max-schema-grant-objects",
    default=None,
    type=int,
    help="Stop before grant discovery if schema objects in scope exceed this cap. Use 0 for no cap.",
)
@click.option(
    "--progress-checkpoint",
    default=None,
    help="Write the latest import progress event to this JSON file.",
)
@click.option("--include-system", is_flag=True, default=False, help="Include system catalogs, schemas, and groups.")
@click.option("--out", "out_path", default=None, help="Write generated workspace YAML to a file.")
@click.option("--suite-out", "suite_out", default=None, help="Write workspace, RBAC, taxonomy, and masking review files under this directory.")
@click.option(
    "--suite-layout",
    default="standard",
    show_default=True,
    type=click.Choice(["standard", "enterprise"]),
    help="File naming layout for --suite-out.",
)
@click.option(
    "--suite-prefix",
    default=None,
    help="Override the generated enterprise suite filename prefix.",
)
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def import_generate_command(
    config_path: str,
    catalogs: tuple[str, ...],
    include_groups: bool,
    include_identities: bool,
    include_grants: bool,
    grant_scope: str,
    max_grant_objects: int,
    max_catalog_grant_objects: int | None,
    max_schema_grant_objects: int | None,
    progress_checkpoint: str | None,
    include_system: bool,
    out_path: str | None,
    suite_out: str | None,
    suite_layout: str,
    suite_prefix: str | None,
    output_format: str,
) -> None:
    dm = DataMuru(config_path=config_path)
    grant_cap = None if max_grant_objects == 0 else max_grant_objects
    grant_object_budgets = _grant_object_budgets(
        catalog=max_catalog_grant_objects,
        schema=max_schema_grant_objects,
    )
    progress_callback = None
    progress_context = None
    if output_format == "json" and progress_checkpoint:
        progress_callback = _checkpoint_progress(progress_checkpoint).update
    elif output_format != "json":
        progress_context = _import_progress("Import generation", checkpoint_path=progress_checkpoint)
        progress_callback = progress_context.__enter__()
    try:
        if suite_out:
            result = dm.import_suite(
                output_dir=suite_out,
                catalogs=list(catalogs) or None,
                include_system=include_system,
                grant_scope=grant_scope,
                max_grant_objects=grant_cap,
                grant_object_budgets=grant_object_budgets,
                suite_layout=suite_layout,
                suite_prefix=suite_prefix,
                progress=progress_callback,
            )
        else:
            result = dm.import_generate(
                catalogs=list(catalogs) or None,
                include_groups=include_groups,
                include_identities=include_identities,
                include_grants=include_grants,
                include_system=include_system,
                grant_scope=grant_scope,
                max_grant_objects=grant_cap,
                grant_object_budgets=grant_object_budgets,
                progress=progress_callback,
            )
    finally:
        if progress_context is not None:
            progress_context.__exit__(None, None, None)
    if out_path:
        resolved = Path(out_path).resolve()
        resolved.write_text(result.workspace_file_text, encoding="utf-8")
    if output_format == "json":
        payload = result.to_dict()
        if out_path:
            payload["written_to"] = str(Path(out_path).resolve())
        if suite_out:
            payload["suite_out"] = str(Path(suite_out).resolve())
            payload["suite_layout"] = suite_layout
        console.print_json(json.dumps(payload, indent=2))
        return

    console.print(f"[primary]Import Generate[/primary] - environment: [code]{result.environment}[/code]")
    if suite_out:
        console.print(
            f"[success]Wrote[/success] [code]{suite_layout}[/code] import review suite under [code]{Path(suite_out).resolve()}[/code]"
        )
        for label, path in result.suite_files.items():
            console.print(f"  - {label}: [code]{path}[/code]")
        return
    if out_path:
        console.print(f"[success]Wrote[/success] starter workspace YAML to [code]{Path(out_path).resolve()}[/code]")
    console.print(result.workspace_file_text)
    if result.rbac_file_text:
        console.print("[primary]Generated RBAC preview[/primary]:")
        console.print(result.rbac_file_text)


@import_group.command("adopt")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option(
    "--target",
    "targets",
    multiple=True,
    required=True,
    help="Declared resource address to adopt. Repeat for multiple targets.",
)
@click.option("--auto-approve", is_flag=True, default=False, help="Commit matching live resources to state.")
@click.option("--output", "output_format", default="text", type=click.Choice(["text", "json"]))
@with_cli_errors
def import_adopt_command(
    config_path: str,
    targets: tuple[str, ...],
    auto_approve: bool,
    output_format: str,
) -> None:
    dm = DataMuru(config_path=config_path)
    preview = dm.import_adopt(targets=list(targets), commit=False)
    if output_format == "json" and not auto_approve:
        console.print_json(json.dumps(preview.to_dict(), indent=2))
        return

    console.print(f"[primary]Import Adoption Preview[/primary] - environment: [code]{preview.environment}[/code]")
    for address in preview.candidates:
        console.print(f"  [create]+[/create] [code]{address}[/code] ready to adopt")
    for address in preview.already_managed:
        console.print(f"  [nochange]=[/nochange] [code]{address}[/code] already managed")
    for address in preview.missing:
        console.print(f"  [error]![/error] [code]{address}[/code] was not observed live")
    for conflict in preview.conflicts:
        console.print(f"  [error]![/error] [code]{conflict.address}[/code] {conflict.reason}")

    if not auto_approve:
        console.print("[warning]Preview only. Re-run with --auto-approve to write matching resources to state.[/warning]")
        return
    if not preview.ready:
        raise click.ClickException("Import adoption has blockers; state was not changed.")

    result = dm.import_adopt(targets=list(targets), commit=True)
    if output_format == "json":
        console.print_json(json.dumps(result.to_dict(), indent=2))
        return
    console.print(f"[success]Adopted[/success] {len(result.adopted)} resources into state.")


class _import_progress:
    def __init__(self, label: str, *, checkpoint_path: str | None = None) -> None:
        self.label = label
        self.checkpoint = _checkpoint_progress(checkpoint_path) if checkpoint_path else None
        self.progress = Progress(
            SpinnerColumn(style="primary"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        )
        self.task_id = None

    def __enter__(self):
        self.progress.__enter__()
        self.task_id = self.progress.add_task(f"{self.label}: starting", total=6)
        return self.update

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.task_id is not None and exc_type is None:
            task = self.progress.tasks[self.task_id]
            total = task.total or 1
            self.progress.update(self.task_id, completed=total, description=f"{self.label}: complete")
        self.progress.__exit__(exc_type, exc, tb)

    def update(self, event: dict) -> None:
        if self.task_id is None:
            return
        update_args = {}
        message = event.get("message")
        stage = event.get("stage")
        if message:
            prefix = f"{self.label}: {stage}: " if stage else f"{self.label}: "
            update_args["description"] = f"{prefix}{message}"
        if event.get("total") is not None:
            update_args["total"] = max(int(event["total"]), 1)
        if event.get("completed") is not None:
            update_args["completed"] = max(int(event["completed"]), 0)
        if event.get("advance") is not None:
            update_args["advance"] = int(event["advance"])
        self.progress.update(self.task_id, **update_args)
        if self.checkpoint:
            self.checkpoint.update(event)


def _grant_object_budgets(*, catalog: int | None, schema: int | None) -> dict[str, int] | None:
    budgets: dict[str, int] = {}
    if catalog is not None and catalog > 0:
        budgets["catalog"] = catalog
    if schema is not None and schema > 0:
        budgets["schema"] = schema
    return budgets or None


class _checkpoint_progress:
    def __init__(self, checkpoint_path: str | None) -> None:
        self.path = Path(checkpoint_path).resolve() if checkpoint_path else None

    def update(self, event: dict) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(UTC).isoformat(),
            "event": event,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
