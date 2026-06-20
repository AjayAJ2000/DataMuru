"""Shared rich console and formatting helpers for the DataMuru CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install

from datamuru.errors import DataMuruError

DATAMURU_THEME = Theme(
    {
        "primary": "bold #0D7377",
        "secondary": "bold #14539A",
        "accent": "#C8962A",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "create": "bold green",
        "update": "bold yellow",
        "destroy": "bold red",
        "nochange": "dim",
        "code": "#9CDCFE",
        "muted": "dim white",
    }
)

console = Console(theme=DATAMURU_THEME)
install(show_locals=False)


def render_cli_banner(command: str | None = None) -> None:
    """Render the branded CLI shell header for interactive command usage."""

    title = Text("DataMuru", style="primary")
    subtitle = Text("Provider-agnostic data infrastructure, governed by design.", style="secondary")
    tagline = Text("Declare. Review. Apply. Evidence.", style="accent")
    mark = Text()
    mark.append("   /\\\n", style="primary")
    mark.append("  /DM\\\n", style="accent")
    mark.append("  \\__/\n", style="primary")
    if command:
        tagline.append(f"  command: {command}", style="muted")

    body = Text()
    body.append_text(mark)
    body.append_text(title)
    body.append("\n")
    body.append_text(subtitle)
    body.append("\n")
    body.append_text(tagline)
    console.print(Panel.fit(body, border_style="primary", title="DataMuru CLI"))


def render_plan_symbol(action: str) -> str:
    """Return the rich-styled symbol for a plan action."""

    mapping = {
        "create": "[create]+[/create]",
        "update": "[update]~[/update]",
        "destroy": "[destroy]-[/destroy]",
        "noop": "[nochange]=[/nochange]",
    }
    return mapping[action]


def render_error(error: DataMuruError) -> None:
    lines = [f"[error]{error.code}[/error] [primary]{error.title}[/primary]", error.description]
    for key, value in error.context.items():
        lines.append(f"[muted]{key}[/muted]: {value}")
    if error.suggestion:
        lines.append(f"[accent]Suggestion[/accent]: {error.suggestion}")
    console.print(Panel.fit("\n".join(lines), border_style="error", title="DataMuru"))
