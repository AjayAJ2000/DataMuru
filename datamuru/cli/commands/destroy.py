from __future__ import annotations

import click

from datamuru.api import DataMuru

from ..guard import with_cli_errors
from ..output import console


@click.command("destroy")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--target", default=None)
@click.option("--confirm-destroy", is_flag=True, default=False)
@with_cli_errors
def destroy_command(config_path: str, target: str | None, confirm_destroy: bool) -> None:
    if not confirm_destroy:
        raise click.ClickException("Destroy requires --confirm-destroy.")
    dm = DataMuru(config_path=config_path)
    result = dm.destroy(target=target)
    if not result.success:
        raise SystemExit(1)
    console.print(f"[success]Destroyed[/success] {len(result.applied)} resources.")
