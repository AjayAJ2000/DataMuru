from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import click

from datamuru.core.config import load_project, resolve_environment_name, validate_project
from datamuru.governance.masking import compile_masking_resources
from datamuru.governance.rbac import compile_rbac_resources
from datamuru.governance.taxonomy import compile_taxonomy_resources
from datamuru.providers.factory import load_provider

from ..guard import with_cli_errors
from ..output import console


@click.command("ui")
@click.option("--config", "config_path", default="datamuru.yml", show_default=True)
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, show_default=True, type=int)
@with_cli_errors
def ui_command(config_path: str, host: str, port: int) -> None:
    """Serve a local DataMuru project dashboard without live provider scans."""

    server = _DataMuruUiServer((host, port), _DataMuruUiHandler, config_path=Path(config_path).resolve())
    url = f"http://{host}:{port}/"
    console.print(f"[primary]DataMuru local UI[/primary] running at [code]{url}[/code]")
    console.print("[muted]Press Ctrl+C to stop. The dashboard uses local config only; it does not scan Databricks.[/muted]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[warning]Stopping DataMuru local UI.[/warning]")
    finally:
        server.server_close()


class _DataMuruUiServer(ThreadingHTTPServer):
    def __init__(self, server_address, request_handler_class, *, config_path: Path) -> None:
        super().__init__(server_address, request_handler_class)
        self.config_path = config_path


class _DataMuruUiHandler(BaseHTTPRequestHandler):
    server: _DataMuruUiServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/summary":
            self._send_json(_build_summary(self.server.config_path))
            return
        if parsed.path in {"/", "/index.html"}:
            self._send_html(_render_page())
            return
        self.send_error(404, "Not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _build_summary(config_path: Path) -> dict:
    issues = validate_project(config_path)
    project = load_project(config_path)
    environment = resolve_environment_name(project, None)
    provider = load_provider(project)
    resources = provider.build_desired_resources(project)
    resources.extend(compile_taxonomy_resources(project.governance))
    resources.extend(compile_rbac_resources(project.governance))
    resources.extend(compile_masking_resources(project.governance))
    resource_counts: dict[str, int] = {}
    for resource in resources:
        resource_counts[resource.resource_type] = resource_counts.get(resource.resource_type, 0) + 1
    return {
        "project": project.root.project.name,
        "edition": project.root.project.edition,
        "environment": environment,
        "provider": project.root.provider.name,
        "validation": {
            "ok": not any(issue.level == "error" for issue in issues),
            "issues": [issue.model_dump(mode="python") for issue in issues],
        },
        "resource_counts": dict(sorted(resource_counts.items())),
        "resource_total": len(resources),
        "workspaces": len(project.workspaces),
        "config_path": str(config_path),
    }


def _render_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DataMuru Local UI</title>
  <style>
    :root { --ink: #111827; --muted: #64748b; --teal: #0D7377; --blue: #14539A; --gold: #C8962A; --paper: #f8fafc; }
    body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; color: var(--ink); background: var(--paper); }
    header { padding: 32px; color: white; background: linear-gradient(135deg, var(--teal), var(--blue)); }
    main { max-width: 1120px; margin: -28px auto 48px; padding: 0 24px; }
    .hero { display: flex; align-items: end; justify-content: space-between; gap: 24px; }
    .eyebrow { color: #d9f99d; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; font-size: 12px; }
    h1 { margin: 8px 0 4px; font-size: clamp(32px, 6vw, 64px); line-height: .95; }
    .tagline { margin: 0; color: #dbeafe; font-size: 18px; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 20px; box-shadow: 0 20px 45px rgba(15, 23, 42, .08); padding: 22px; }
    .metric { font-size: 34px; font-weight: 800; color: var(--teal); }
    .label { color: var(--muted); font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
    .wide { grid-column: span 2; }
    pre { overflow: auto; padding: 16px; border-radius: 14px; background: #0f172a; color: #dbeafe; }
    .ok { color: #047857; font-weight: 800; }
    .bad { color: #b91c1c; font-weight: 800; }
    @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } .wide { grid-column: span 1; } .hero { display: block; } }
  </style>
</head>
<body>
  <header>
    <div class="hero">
      <div>
        <div class="eyebrow">DataMuru Local Console</div>
        <h1 id="project">Loading...</h1>
        <p class="tagline">Local-first project visibility without live warehouse scans.</p>
      </div>
      <div id="status" class="tagline">Checking project...</div>
    </div>
  </header>
  <main>
    <section class="grid">
      <article class="card"><div class="label">Edition</div><div id="edition" class="metric">-</div></article>
      <article class="card"><div class="label">Provider</div><div id="provider" class="metric">-</div></article>
      <article class="card"><div class="label">Resources</div><div id="resources" class="metric">-</div></article>
      <article class="card"><div class="label">Workspaces</div><div id="workspaces" class="metric">-</div></article>
      <article class="card wide"><div class="label">Resource Inventory</div><pre id="counts">{}</pre></article>
      <article class="card wide"><div class="label">Validation</div><pre id="issues">[]</pre></article>
    </section>
  </main>
  <script>
    fetch('/api/summary').then(r => r.json()).then(data => {
      document.getElementById('project').textContent = data.project;
      document.getElementById('edition').textContent = data.edition;
      document.getElementById('provider').textContent = data.provider;
      document.getElementById('resources').textContent = data.resource_total;
      document.getElementById('workspaces').textContent = data.workspaces;
      document.getElementById('counts').textContent = JSON.stringify(data.resource_counts, null, 2);
      document.getElementById('issues').textContent = JSON.stringify(data.validation.issues, null, 2);
      const status = document.getElementById('status');
      status.textContent = data.validation.ok ? 'Configuration valid' : 'Validation needs attention';
      status.className = data.validation.ok ? 'ok' : 'bad';
    }).catch(error => {
      document.getElementById('project').textContent = 'DataMuru';
      document.getElementById('status').textContent = 'Failed to load summary: ' + error;
    });
  </script>
</body>
</html>"""
