# Tenant Entitlement Record Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a redacted, deterministic, offline tenant entitlement record that can be exported through CLI and Python APIs and included in the Enterprise activation handoff package.

**Architecture:** A focused `datamuru.enterprise.registry` module reuses the existing activation report for readiness and redacted source data, derives an immutable record identifier from canonical stable fields, and owns JSON serialization. Existing engine, public API, CLI, and handoff-package layers remain thin adapters around that module.

**Tech Stack:** Python 3.11+, Pydantic/DataMuruModel, Click, pytest, Ruff, MkDocs Material.

---

## File Map

- Create `datamuru/enterprise/registry.py`: record model, canonical fingerprint, builder, and writer.
- Create `tests/unit/test_tenant_entitlement_record.py`: builder, fingerprint, redaction, CLI, and public API coverage.
- Modify `datamuru/enterprise/__init__.py`: public enterprise exports.
- Modify `datamuru/core/engine.py`: engine builder and writer methods.
- Modify `datamuru/api.py`: public Python API methods.
- Modify `datamuru/cli/commands/enterprise.py`: `enterprise control-plane tenant-record` command.
- Modify `datamuru/enterprise/handoff.py`: sixth handoff artifact and JSON file.
- Modify `tests/unit/test_enterprise_activation.py`: six-artifact package assertions.
- Modify `docs/reference/cli.md`, `docs/reference/python-api.md`, and `docs/reference/capabilities.md`: exact public behavior and limits.
- Modify `docs/guides/enterprise-activation.md`: onboarding workflow guidance.
- Modify `docs/operations/milestone-0-5-test-runbook.md`: feature-by-feature validation steps.
- Modify `docs/product/roadmap.md`, `docs/product/github-project-board.md`, `CHANGELOG.md`, and the approved design spec: milestone status.

### Task 1: Record Contract, Stable Identity, And Redaction

**Files:**
- Create: `tests/unit/test_tenant_entitlement_record.py`
- Create: `datamuru/enterprise/registry.py`
- Modify: `datamuru/enterprise/__init__.py`

- [x] **Step 1: Write the failing builder tests**

Create a fixture helper that enables Enterprise activation in a copied sample project, then add tests with fixed UTC timestamps. The assertions must include:

```python
record = build_tenant_entitlement_record(
    project,
    environ={"DATAMURU_LICENSE_KEY": "secret-value"},
    generated_at=datetime(2026, 6, 27, 10, 0, tzinfo=UTC),
)
assert record.schema_version == "datamuru.tenant_entitlement_record.v1"
assert record.status == "ready"
assert record.ready is True
assert record.record_id.startswith("ter_")
assert len(record.record_id) == 24
assert record.tenant["tenant_id"] == "acme-prod"
assert record.entitlement["enabled_features"] == [
    "compliance_reporting",
    "hosted_control_plane",
    "identity_management",
    "multi_workspace",
]
assert record.security["secret_values_included"] is False
assert "secret-value" not in json.dumps(record.to_dict())
assert str(sample_project.resolve()) not in json.dumps(record.to_dict())
```

Add separate tests proving blocked OSS checks, timestamp stability, license-availability stability, tenant-change identity, and entitlement-change identity.

- [x] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -m pytest tests\unit\test_tenant_entitlement_record.py -q --basetemp .datamuru\pytest-tenant-red -p no:cacheprovider
```

Expected: collection fails because `datamuru.enterprise.registry` does not exist.

- [x] **Step 3: Implement the model, builder, and writer**

Implement this public shape in `datamuru/enterprise/registry.py`:

```python
class TenantEntitlementRecord(DataMuruModel):
    schema_version: str
    generated_at: str
    status: str
    ready: bool
    record_id: str
    project: dict[str, Any]
    tenant: dict[str, Any]
    entitlement: dict[str, Any]
    source: dict[str, Any]
    checks: list[ActivationCheck]
    security: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.model_dump(mode="python", exclude={"checks"}),
            "checks": [check.to_dict() for check in self.checks],
        }


def build_tenant_entitlement_record(
    project: LoadedProject,
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: datetime | None = None,
) -> TenantEntitlementRecord:
    report = build_activation_report(project, environ=environ)
    activation = report.payload["activation"]
    features = report.payload["features"]
    project_payload = {
        "name": report.payload["project"]["name"],
        "provider": report.payload["project"]["provider"],
        "default_environment": report.payload["project"]["default_environment"],
    }
    tenant = {
        "organization": activation.get("organization"),
        "tenant_id": activation.get("tenant_id"),
        "deployment_region": activation.get("deployment_region"),
        "control_plane_url": activation.get("control_plane_url"),
    }
    entitlement = {
        "support_plan": activation.get("support_plan"),
        "purchase_reference": activation.get("purchase_reference"),
        "enabled_features": sorted(name for name, enabled in features.items() if enabled),
        "license_key_env": activation.get("license_key_env"),
        "license_key_present": activation.get("license_key_present", False),
    }
```

Build the fingerprint payload only from `project`, `tenant`, activation schema version, and `entitlement` without `license_key_present`. Serialize it with `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`, hash with SHA-256, and format `ter_{digest[:20]}`. Add the exact security booleans from the approved design. The writer resolves the destination, creates its parent, writes indented JSON plus a trailing newline, and returns the resolved `Path`.

- [x] **Step 4: Export the new symbols**

Export `TenantEntitlementRecord`, `build_tenant_entitlement_record`, and `write_tenant_entitlement_record` from `datamuru/enterprise/__init__.py` and include them in `__all__`.

- [x] **Step 5: Run the focused tests and verify GREEN**

Run the same focused pytest command. Expected: all builder, identity, and redaction tests pass.

### Task 2: Python API And CLI

**Files:**
- Modify: `tests/unit/test_tenant_entitlement_record.py`
- Modify: `datamuru/core/engine.py`
- Modify: `datamuru/api.py`
- Modify: `datamuru/cli/commands/enterprise.py`

- [x] **Step 1: Write failing API and CLI tests**

Add tests that call:

```python
dm = DataMuru(config_path)
record = dm.enterprise_tenant_entitlement_record()
written = dm.write_enterprise_tenant_entitlement_record(output_path)
assert record.ready is True
assert written == output_path.resolve()
```

Use `CliRunner` to verify a ready JSON export, default blocked behavior with no file, and `--allow-blocked` diagnostic output. The ready invocation is:

```python
result = CliRunner().invoke(cli, [
    "--no-banner", "enterprise", "control-plane", "tenant-record",
    "--config", str(config_path), "--out", str(output_path), "--output", "json",
])
```

- [x] **Step 2: Run the API and CLI tests and verify RED**

Run the focused test file. Expected: failures report missing DataMuru methods and unknown `tenant-record` command.

- [x] **Step 3: Add thin engine and public API methods**

Add these methods to both adapter layers:

```python
def enterprise_tenant_entitlement_record(self):
    project, _, _, _ = self._load()
    from datamuru.enterprise import build_tenant_entitlement_record
    return build_tenant_entitlement_record(project, environ=os.environ)

def write_enterprise_tenant_entitlement_record(self, output_path: str | Path):
    from datamuru.enterprise import write_tenant_entitlement_record
    record = self.enterprise_tenant_entitlement_record()
    return write_tenant_entitlement_record(record, output_path)
```

The `DataMuru` methods delegate directly to the engine methods.

- [x] **Step 4: Add the guarded CLI command**

Register `tenant-record` under `control-plane` with required `--out`, optional `--config`, `--allow-blocked`, and `--output text|json`. Build once, refuse to write when blocked unless explicitly allowed, write with the shared writer, print the complete record in JSON mode, and exit zero for an explicitly allowed diagnostic record.

- [x] **Step 5: Run focused tests and verify GREEN**

Run the focused test file. Expected: builder, API, and CLI tests all pass.

### Task 3: Activation Handoff Package Integration

**Files:**
- Modify: `tests/unit/test_enterprise_activation.py`
- Modify: `datamuru/enterprise/handoff.py`

- [x] **Step 1: Change package assertions first**

Require `tenant_entitlement_record` in the manifest artifact names, require `tenant-entitlement-record.json` on disk, and change the Python API manifest count from five to six.

- [x] **Step 2: Run package tests and verify RED**

Run:

```powershell
python -m pytest tests\unit\test_enterprise_activation.py -q --basetemp .datamuru\pytest-package-red -p no:cacheprovider
```

Expected: package assertions fail because the sixth artifact is absent.

- [x] **Step 3: Build and write the sixth artifact**

In both package builder and writer paths, call `build_tenant_entitlement_record(project, environ=environ, generated_at=timestamp)`. Add:

```python
_artifact(
    "tenant_entitlement_record",
    "tenant-entitlement-record.json",
    tenant_record.to_dict(),
    tenant_record.status,
)
```

Write the same payload before `manifest.json`. Include `tenant_record.ready` in `package_ready` so the manifest cannot report ready when its tenant record is blocked.

- [x] **Step 4: Run package and focused tests and verify GREEN**

Run both enterprise activation and tenant entitlement test files. Expected: all tests pass.

### Task 4: Documentation And Milestone Runbook

**Files:**
- Modify: `docs/reference/cli.md`
- Modify: `docs/reference/python-api.md`
- Modify: `docs/reference/capabilities.md`
- Modify: `docs/guides/enterprise-activation.md`
- Modify: `docs/operations/milestone-0-5-test-runbook.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/product/github-project-board.md`
- Modify: `docs/superpowers/specs/2026-06-27-tenant-entitlement-record-design.md`
- Modify: `CHANGELOG.md`

- [x] **Step 1: Document the exact contract and safety boundary**

Add the CLI signature, both Python methods, schema name, deterministic ID rule, six-file package listing, and the offline/non-provisioning boundary. Mark the immutable record export as Experimental and hosted registry/provisioning as Roadmap.

- [x] **Step 2: Update planning status without claiming hosted infrastructure**

Add the tenant entitlement record slice to the v0.5 roadmap and project-board backlog, note it in Unreleased, and change the design status to implemented after verification. Keep hosted mutable registry, tenant provisioning, license issuance, and remote API synchronization explicitly unimplemented.

- [x] **Step 3: Add a complete runbook section**

Include PowerShell commands for ready export, schema/field inspection, two-run ID comparison, license-presence stability, secret and absolute-path redaction, blocked default behavior, `--allow-blocked`, package integration, expected results, and bug evidence. Renumber the quality-gate section after inserting the feature section.

- [x] **Step 4: Run documentation checks**

Run:

```powershell
python -m pytest tests\unit\test_documentation.py -q --basetemp .datamuru\pytest-docs -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
```

Expected: documentation tests and strict MkDocs build exit zero.

### Task 5: Full Verification And Delivery

**Files:**
- Verify all modified files.

- [x] **Step 1: Run the complete local gate**

```powershell
python -m ruff check datamuru tests
python -m pytest -q --basetemp .datamuru\pytest-final -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
git diff --check
```

Expected: every command exits zero with no lint, test, build, or whitespace errors.

- [x] **Step 2: Review the diff against the approved spec**

Confirm each acceptance criterion has a code assertion or runbook step, no secret values or absolute local paths enter artifacts, no hosted behavior is claimed, and only the intentional package artifact-count change affects existing behavior.

- [ ] **Step 3: Commit and push**

```powershell
git add CHANGELOG.md datamuru docs tests
git commit -m "Add offline tenant entitlement record export"
git push origin main
```

- [ ] **Step 4: Verify remote checks**

Inspect the pushed commit and GitHub Actions. Require CI, Documentation, and Documentation Links to complete successfully before reporting delivery.
