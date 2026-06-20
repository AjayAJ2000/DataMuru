from __future__ import annotations

import sys

import click

from .commands import COMMANDS
from .output import render_cli_banner


class DataMuruGroup(click.Group):
    """Keep the original argv so the shell banner can respect output mode."""

    def main(self, args: list[str] | None = None, **kwargs) -> object:
        self.datamuru_raw_args = list(sys.argv[1:] if args is None else args)
        return super().main(args=args, **kwargs)


def _json_output_requested(args: list[str]) -> bool:
    for index, arg in enumerate(args):
        if arg == "--output" and index + 1 < len(args) and args[index + 1] == "json":
            return True
        if arg == "--output=json":
            return True
    return False


@click.group(cls=DataMuruGroup, invoke_without_command=True)
@click.option("--no-banner", is_flag=True, help="Suppress the branded CLI header for scripts and automation.")
@click.pass_context
def cli(ctx: click.Context, no_banner: bool) -> None:
    """DataMuru alpha CLI."""

    raw_args = getattr(ctx.command, "datamuru_raw_args", sys.argv[1:])
    suppress_banner = no_banner or _json_output_requested(raw_args)
    if ctx.resilient_parsing:
        return
    if ctx.invoked_subcommand is None:
        if not suppress_banner:
            render_cli_banner()
        click.echo(ctx.get_help())
        return
    if not suppress_banner:
        render_cli_banner(ctx.invoked_subcommand)


for command in COMMANDS:
    cli.add_command(command)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
