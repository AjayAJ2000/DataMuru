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
    workspace_names = [
        workspace.raw.get("workspace", {}).get("name", workspace.path.stem) for workspace in project.workspaces
    ]
    risk_count = len([issue for issue in issues if issue.level == "error"])
    warning_count = len([issue for issue in issues if issue.level == "warning"])
    readiness = "Ready for review"
    if risk_count:
        readiness = "Action required"
    elif warning_count:
        readiness = "Review warnings"
    return {
        "project": project.root.project.name,
        "edition": project.root.project.edition,
        "environment": environment,
        "provider": project.root.provider.name,
        "provider_cloud": project.root.provider.cloud,
        "validation": {
            "ok": not any(issue.level == "error" for issue in issues),
            "issues": [issue.model_dump(mode="python") for issue in issues],
            "error_count": risk_count,
            "warning_count": warning_count,
            "readiness": readiness,
        },
        "resource_counts": dict(sorted(resource_counts.items())),
        "resource_total": len(resources),
        "workspaces": len(project.workspaces),
        "workspace_names": workspace_names,
        "features": project.root.features.model_dump(mode="python"),
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
    :root {
      --ink: #142033; --muted: #64748b; --line: #dbe5ea; --teal: #087c80;
      --teal-2: #0f8b8d; --blue: #14539a; --gold: #c8962a; --cream: #fbf8f0;
      --paper: #f5f8fa; --navy: #101a2b; --green: #0f766e; --red: #b42318;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Aptos", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 12%, rgba(8, 124, 128, .14), transparent 28rem),
        linear-gradient(180deg, #fffdf8 0%, var(--paper) 44%, #eef5f6 100%);
    }
    header {
      padding: 28px 36px 96px;
      color: white;
      background:
        linear-gradient(120deg, rgba(16, 26, 43, .96), rgba(8, 124, 128, .92)),
        radial-gradient(circle at 82% 8%, rgba(200, 150, 42, .42), transparent 22rem);
    }
    nav { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 54px; }
    .brand { display: flex; align-items: center; gap: 14px; font-weight: 800; letter-spacing: -.02em; }
    .mark {
      width: 42px; height: 42px; border-radius: 14px;
      display: grid; place-items: center;
      background: rgba(255, 255, 255, .09); border: 1px solid rgba(255, 255, 255, .2);
    }
    .mark svg { width: 26px; height: 26px; }
    .pill {
      border: 1px solid rgba(255,255,255,.22); border-radius: 999px;
      padding: 9px 13px; color: #dbeafe; font-size: 13px; background: rgba(255,255,255,.08);
    }
    main { max-width: 1180px; margin: -62px auto 56px; padding: 0 24px; }
    .hero { max-width: 860px; }
    .eyebrow { color: #f1d58a; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; font-size: 12px; }
    h1 { margin: 10px 0 14px; font-size: clamp(40px, 7vw, 76px); line-height: .92; letter-spacing: -.055em; }
    .tagline { margin: 0; color: #dbeafe; font-size: clamp(17px, 2vw, 21px); line-height: 1.55; max-width: 760px; }
    .shell { display: grid; grid-template-columns: 1.25fr .75fr; gap: 18px; align-items: start; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
    .card {
      background: rgba(255, 255, 255, .92);
      border: 1px solid rgba(190, 207, 214, .86);
      border-radius: 24px;
      box-shadow: 0 24px 70px rgba(16, 26, 43, .10);
      padding: 22px;
      backdrop-filter: blur(16px);
    }
    .metric { font-size: 34px; font-weight: 850; letter-spacing: -.04em; color: var(--teal); margin-top: 6px; }
    .label { color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }
    .section-title { margin: 0 0 14px; font-size: 20px; letter-spacing: -.03em; }
    .wide { grid-column: span 3; }
    .panel-list { display: grid; gap: 10px; }
    .row { display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }
    .row:last-child { border-bottom: 0; }
    .row strong { font-size: 14px; }
    .row span { color: var(--muted); text-align: right; }
    pre { overflow: auto; padding: 16px; border-radius: 16px; background: var(--navy); color: #dbeafe; line-height: 1.5; }
    .status { display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; padding: 10px 14px; font-weight: 800; }
    .ok { color: var(--green); background: #dff7ef; }
    .bad { color: var(--red); background: #ffe5df; }
    .warn { color: #8a5a00; background: #fff2c7; }
    .timeline { display: grid; gap: 12px; }
    .step { display: grid; grid-template-columns: 30px 1fr; gap: 12px; align-items: start; }
    .num {
      width: 30px; height: 30px; border-radius: 50%;
      background: #e6f4f1; color: var(--teal); display: grid; place-items: center; font-weight: 900;
    }
    .step p { margin: 2px 0 0; color: var(--muted); line-height: 1.45; }
    .workspace-chip {
      display: inline-flex; margin: 4px 6px 4px 0; padding: 7px 10px;
      border-radius: 999px; background: #edf7f7; color: var(--teal); font-weight: 700; font-size: 13px;
    }
    .mono { font-family: "Cascadia Code", "SFMono-Regular", Consolas, monospace; font-size: 12px; }
    @media (max-width: 980px) { .shell, .grid { grid-template-columns: 1fr; } .wide { grid-column: span 1; } header { padding-inline: 24px; } }
  </style>
</head>
<body>
  <header>
    <nav>
      <div class="brand">
        <div class="mark" aria-hidden="true">
          <svg viewBox="0 0 64 64" fill="none">
            <path d="M32 5C18 17 10 29 12 42c2 12 11 17 20 17s18-5 20-17C54 29 46 17 32 5Z" stroke="#f7fbfb" stroke-width="6"/>
            <path d="M32 17c-8 8-12 16-10 24 1 7 5 11 10 13 5-2 9-6 10-13 2-8-2-16-10-24Z" fill="#14539a"/>
            <path d="M32 34v25M22 58l10-24 10 24" stroke="#f7fbfb" stroke-width="5" stroke-linecap="round"/>
            <circle cx="32" cy="31" r="6" fill="#c8962a"/>
          </svg>
        </div>
        <span>DataMuru</span>
      </div>
      <div class="pill">Local enterprise console</div>
    </nav>
    <div class="hero">
      <div class="eyebrow">Governed data infrastructure</div>
      <h1 id="project">Loading project...</h1>
      <p class="tagline">Review workspace posture, provider readiness, governance coverage, and adoption next steps before running any live platform scan.</p>
    </div>
  </header>
  <main>
    <section class="shell">
      <div class="grid">
        <article class="card"><div class="label">Edition</div><div id="edition" class="metric">-</div></article>
        <article class="card"><div class="label">Provider</div><div id="provider" class="metric">-</div></article>
        <article class="card"><div class="label">Managed resources</div><div id="resources" class="metric">-</div></article>
        <article class="card wide">
          <h2 class="section-title">Project posture</h2>
          <div class="panel-list">
            <div class="row"><strong>Readiness</strong><span id="status" class="status">Checking...</span></div>
            <div class="row"><strong>Environment</strong><span id="environment">-</span></div>
            <div class="row"><strong>Config source</strong><span id="config" class="mono">-</span></div>
            <div class="row"><strong>Workspaces</strong><span id="workspace-list">-</span></div>
          </div>
        </article>
        <article class="card wide">
          <h2 class="section-title">Declared inventory</h2>
          <pre id="counts">{}</pre>
        </article>
      </div>
      <aside class="card">
        <h2 class="section-title">Enterprise rollout path</h2>
        <div class="timeline">
          <div class="step"><div class="num">1</div><div><strong>Discover narrowly</strong><p>Start with catalog inventory. Add grants only for selected scopes.</p></div></div>
          <div class="step"><div class="num">2</div><div><strong>Generate review suite</strong><p>Write workspace, RBAC, taxonomy, and migration files using stable names.</p></div></div>
          <div class="step"><div class="num">3</div><div><strong>Promote intentionally</strong><p>Move from read-only to plan, saved plan review, and controlled apply.</p></div></div>
          <div class="step"><div class="num">4</div><div><strong>Track delivery</strong><p>Use GitHub Projects for roadmap, ownership, release, and evidence.</p></div></div>
        </div>
      </aside>
      <article class="card">
        <h2 class="section-title">Feature posture</h2>
        <pre id="features">{}</pre>
      </article>
      <article class="card">
        <h2 class="section-title">Validation detail</h2>
        <pre id="issues">[]</pre>
      </article>
    </section>
  </main>
  <script>
    fetch('/api/summary').then(r => r.json()).then(data => {
      document.getElementById('project').textContent = data.project;
      document.getElementById('edition').textContent = data.edition;
      document.getElementById('provider').textContent = data.provider + ' / ' + data.provider_cloud;
      document.getElementById('resources').textContent = data.resource_total;
      document.getElementById('environment').textContent = data.environment;
      document.getElementById('config').textContent = data.config_path;
      document.getElementById('workspace-list').innerHTML = data.workspace_names.length
        ? data.workspace_names.map(name => '<span class="workspace-chip">' + name + '</span>').join('')
        : 'No workspace files';
      document.getElementById('features').textContent = JSON.stringify(data.features, null, 2);
      document.getElementById('counts').textContent = JSON.stringify(data.resource_counts, null, 2);
      document.getElementById('issues').textContent = JSON.stringify(data.validation.issues, null, 2);
      const status = document.getElementById('status');
      status.textContent = data.validation.readiness;
      status.className = 'status ' + (data.validation.error_count ? 'bad' : data.validation.warning_count ? 'warn' : 'ok');
    }).catch(error => {
      document.getElementById('project').textContent = 'DataMuru';
      document.getElementById('status').textContent = 'Failed to load summary: ' + error;
    });
  </script>
</body>
</html>"""
