from __future__ import annotations

import click

from .commands import COMMANDS


@click.group()
def cli() -> None:
    """DataMuru alpha CLI."""


for command in COMMANDS:
    cli.add_command(command)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
