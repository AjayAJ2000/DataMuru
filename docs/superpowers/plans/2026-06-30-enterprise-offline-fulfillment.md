# Enterprise Offline Fulfillment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a secure offline operator-decision workflow that validates a redacted Enterprise purchase request and writes traceable fulfillment evidence without claiming payment, license signing, or tenant provisioning.

**Architecture:** A new `datamuru.enterprise.fulfillment` module owns request loading, validation, canonical fingerprints, decision/receipt models, and conflict-safe writes. The CLI and Python API are thin adapters around that module, and post-decision artifacts remain separate from the existing pre-fulfillment activation package.

**Tech Stack:** Python 3.11-3.13, Pydantic-backed `DataMuruModel`, Click, JSON, SHA-256 from `hashlib`, pytest, Ruff, MkDocs Material.

---

## File Structure

- Create `datamuru/enterprise/fulfillment.py`: fulfillment models, safe loader, validation, fingerprints, builders, and writer.
- Create `tests/unit/test_enterprise_fulfillment.py`: focused domain, CLI, API, tamper, idempotency, and redaction tests.
- Modify `datamuru/errors.py`: add a stable fulfillment error family.
- Modify `datamuru/enterprise/__init__.py`: export the public fulfillment contracts.
- Modify `datamuru/api.py`: expose config-independent fulfillment methods.
- Modify `datamuru/cli/commands/enterprise.py`: add `activation fulfill`.
- Modify `docs/guides/enterprise-activation.md`, `docs/reference/cli.md`, `docs/reference/python-api.md`, and `docs/reference/capabilities.md`: document exact supported scope and boundaries.
- Modify `docs/operations/milestone-0-5-test-runbook.md`: add complete approval, rejection, tamper, rerun, and redaction tests.
- Modify `docs/product/roadmap.md`, `docs/product/github-project-board.md`, `PROJECT_STATUS.md`, and `CHANGELOG.md`: close the scoped milestone outcome without claiming hosted fulfillment.

### Task 1: Domain validation and canonical request fingerprint

**Files:**
- Create: `datamuru/enterprise/fulfillment.py`
- Modify: `datamuru/errors.py`
- Test: `tests/unit/test_enterprise_fulfillment.py`

- [ ] **Step 1: Write failing loader and validation tests**

Add tests that build a ready `datamuru.enterprise_purchase_request.v1` fixture and assert:

```python
request = load_purchase_request(path)
assert request["schema_version"] == "datamuru.enterprise_purchase_request.v1"
assert purchase_request_fingerprint(request).startswith("sha256:")
```

Add parameterized failures for malformed JSON, an unsupported schema, missing `commercial`, missing tenant identity, `license.secret_values_included: true`, `fulfillment.provisions_tenant: true`, and `fulfillment.calls_license_server: true`. Assert `EnterpriseFulfillmentError.code == "DMR-ENT-1001"` and that exception text excludes a planted `secret-value`.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m pytest tests\unit\test_enterprise_fulfillment.py -q --basetemp .datamuru\pytest-fulfillment-red -p no:cacheprovider
```

Expected: collection fails because `datamuru.enterprise.fulfillment` does not exist.

- [ ] **Step 3: Implement the loader and validation boundary**

Add `EnterpriseFulfillmentError` in `datamuru/errors.py`. In the new module, define constants for supported schemas and functions with these signatures:

```python
def load_purchase_request(path: str | Path) -> dict[str, Any]: ...
def validate_purchase_request(request: Mapping[str, Any], *, for_approval: bool) -> None: ...
def canonical_json(payload: Mapping[str, Any]) -> str: ...
def purchase_request_fingerprint(request: Mapping[str, Any]) -> str: ...
```

Use `json.loads`, exact type checks, `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`, and `hashlib.sha256`. Emit fixed validation messages and field paths; never interpolate arbitrary input values into errors.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Task 1 test selection and expect all loader/fingerprint tests to pass.

- [ ] **Step 5: Commit the domain boundary**

```powershell
git add datamuru/errors.py datamuru/enterprise/fulfillment.py tests/unit/test_enterprise_fulfillment.py
git commit -m "Add enterprise fulfillment request validation"
```

### Task 2: Decision and activation receipt models

**Files:**
- Modify: `datamuru/enterprise/fulfillment.py`
- Modify: `datamuru/enterprise/__init__.py`
- Test: `tests/unit/test_enterprise_fulfillment.py`

- [ ] **Step 1: Write failing builder tests**

Cover approved and rejected decisions with fixed UTC timestamps. Assert required schemas, operator evidence, source fingerprint, deterministic IDs, approved entitlements, and security declarations. Assert blocked requests cannot be approved but can be rejected.

```python
decision, receipt = build_fulfillment(
    request,
    decision="approve",
    operator="licensing@datamuru.com",
    decision_reference="CRM-1234",
    generated_at=fixed_time,
)
assert decision.schema_version == "datamuru.enterprise_fulfillment_decision.v1"
assert receipt.schema_version == "datamuru.enterprise_activation_receipt.v1"
assert receipt.security["cryptographically_signed"] is False
assert receipt.security["provisions_tenant"] is False
```

- [ ] **Step 2: Run builder tests and verify RED**

Expected: import or attribute failure for missing models/builders.

- [ ] **Step 3: Implement models and builders**

Define `FulfillmentDecision`, `ActivationReceipt`, and `FulfillmentResult` as `DataMuruModel` classes with explicit `to_dict()` methods. Implement:

```python
def build_fulfillment(
    request: Mapping[str, Any],
    *,
    decision: Literal["approve", "reject"],
    operator: str,
    decision_reference: str,
    notes: str | None = None,
    generated_at: datetime | None = None,
) -> tuple[FulfillmentDecision, ActivationReceipt | None]: ...
```

Require nonblank operator/reference values, derive `decision_id` and `receipt_id` from canonical stable fields, omit notes from identifiers, and include explicit `offline`, `payment_processed: false`, `cryptographically_signed: false`, `calls_license_server: false`, and `provisions_tenant: false` flags.

- [ ] **Step 4: Run builder tests and verify GREEN**

Run the focused module and expect approval/rejection/determinism tests to pass.

- [ ] **Step 5: Commit builders**

```powershell
git add datamuru/enterprise/fulfillment.py datamuru/enterprise/__init__.py tests/unit/test_enterprise_fulfillment.py
git commit -m "Add offline fulfillment decision contracts"
```

### Task 3: Conflict-safe writer and Python API

**Files:**
- Modify: `datamuru/enterprise/fulfillment.py`
- Modify: `datamuru/api.py`
- Test: `tests/unit/test_enterprise_fulfillment.py`

- [ ] **Step 1: Write failing writer/API tests**

Assert approval writes `fulfillment-decision.json` and `activation-receipt.json`; rejection writes only the decision. Assert an identical rerun succeeds, a conflicting existing file blocks before either file changes, and planted license/provider secrets never appear.

- [ ] **Step 2: Run writer/API tests and verify RED**

Expected: missing writer and API method failures.

- [ ] **Step 3: Implement pre-serialized conflict-safe writes**

Implement:

```python
def write_fulfillment(
    request_path: str | Path,
    output_dir: str | Path,
    *,
    decision: Literal["approve", "reject"],
    operator: str,
    decision_reference: str,
    notes: str | None = None,
) -> FulfillmentResult: ...
```

Serialize all output first, inspect every destination, reject any differing existing content, then create the directory and write UTF-8 JSON with a final newline. Add `DataMuru.fulfill_enterprise_activation(...)` as a config-independent static method or thin method that delegates directly to the writer without loading provider configuration.

- [ ] **Step 4: Run writer/API tests and verify GREEN**

- [ ] **Step 5: Commit writer/API**

```powershell
git add datamuru/enterprise/fulfillment.py datamuru/api.py tests/unit/test_enterprise_fulfillment.py
git commit -m "Add conflict-safe fulfillment artifact writer"
```

### Task 4: CLI command and safe output contracts

**Files:**
- Modify: `datamuru/cli/commands/enterprise.py`
- Test: `tests/unit/test_enterprise_fulfillment.py`

- [ ] **Step 1: Write failing CLI tests**

Exercise `enterprise activation fulfill` for approve/reject, JSON/text, missing required options, blocked approval, malformed input, and secret-bearing input. JSON output must include decision, IDs, fingerprints, and written paths but not the complete request.

- [ ] **Step 2: Run CLI tests and verify RED**

Expected: Click reports no such command `fulfill`.

- [ ] **Step 3: Add the thin Click adapter**

Add required `--request`, `--decision`, `--operator`, `--decision-reference`, and `--out`; optional `--notes`; and `--output text|json`. Delegate to `write_fulfillment`, render concise artifact evidence, and rely on `@with_cli_errors` for structured failures.

- [ ] **Step 4: Run CLI tests and verify GREEN**

- [ ] **Step 5: Commit CLI behavior**

```powershell
git add datamuru/cli/commands/enterprise.py tests/unit/test_enterprise_fulfillment.py
git commit -m "Add enterprise activation fulfillment command"
```

### Task 5: Documentation and complete milestone runbook

**Files:**
- Modify: `docs/guides/enterprise-activation.md`
- Modify: `docs/reference/cli.md`
- Modify: `docs/reference/python-api.md`
- Modify: `docs/reference/capabilities.md`
- Modify: `docs/operations/milestone-0-5-test-runbook.md`
- Modify: `tests/unit/test_documentation.py`

- [ ] **Step 1: Add failing documentation contract assertions**

Assert the CLI reference and runbook contain `enterprise activation fulfill`, both schema versions, required operator evidence, tamper test guidance, and the statement that receipts are not signed licenses or provisioning proof.

- [ ] **Step 2: Run documentation tests and verify RED**

```powershell
python -m pytest tests\unit\test_documentation.py -q --basetemp .datamuru\pytest-fulfillment-docs-red -p no:cacheprovider
```

- [ ] **Step 3: Document supported behavior and boundaries**

Add exact approve/reject PowerShell commands, expected JSON fields, output file lists, safe rerun behavior, malformed/tampered request tests, blocked approval, conflict protection, and recursive secret scanning. Keep the capability page canonical and label hosted issuance/provisioning as Roadmap/Enterprise rather than Supported.

- [ ] **Step 4: Run docs tests and strict MkDocs**

```powershell
python -m pytest tests\unit\test_documentation.py -q --basetemp .datamuru\pytest-fulfillment-docs-green -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
```

- [ ] **Step 5: Commit docs and runbook**

```powershell
git add docs tests/unit/test_documentation.py
git commit -m "Document enterprise fulfillment testing"
```

### Task 6: Milestone closeout and exhaustive local verification

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `PROJECT_STATUS.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/product/github-project-board.md`

- [ ] **Step 1: Update milestone evidence honestly**

Mark the offline OSS fulfillment contract complete, retain explicit future-hosted boundaries, link the runbook, and avoid changing the already published `0.5.0a0` artifact claim. Record this as post-release main evidence unless a later release is intentionally prepared.

- [ ] **Step 2: Run focused security and behavior tests**

```powershell
python -m pytest tests\unit\test_enterprise_fulfillment.py tests\unit\test_enterprise_activation.py tests\unit\test_documentation.py -q --basetemp .datamuru\pytest-fulfillment-focused -p no:cacheprovider
```

Expected: zero failures.

- [ ] **Step 3: Run complete repository gates**

```powershell
python -m ruff check datamuru tests
python -m pytest -q --basetemp .datamuru\pytest-fulfillment-full -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
python -m build --outdir .datamuru\dist-fulfillment
python -m twine check .datamuru\dist-fulfillment\*
git diff --check
```

Expected: Ruff clean, all tests pass, strict docs pass, wheel/sdist build, Twine passes both artifacts, and no whitespace errors.

- [ ] **Step 4: Perform artifact-level redaction smoke test**

Generate a fresh purchase request with fake sentinel secrets, fulfill it, recursively scan stdout and output files for each sentinel, verify stable IDs across a rerun, and verify a modified existing receipt blocks without changing either file.

- [ ] **Step 5: Commit milestone closeout**

```powershell
git add CHANGELOG.md PROJECT_STATUS.md docs/product/roadmap.md docs/product/github-project-board.md
git commit -m "Complete offline enterprise fulfillment milestone"
```

### Task 7: GitHub delivery and pipeline verification

**Files:**
- No additional source files expected.

- [ ] **Step 1: Recheck repository state and commit range**

```powershell
git status --short --branch
git log --oneline origin/main..main
```

- [ ] **Step 2: Push main**

```powershell
git push origin main
```

- [ ] **Step 3: Update the private GitHub Project item**

Set `Enterprise purchase and license activation flow` to Done and add the implementation commit, runbook, and successful workflow URLs as evidence. The item description must retain the hosted-backend limitations.

- [ ] **Step 4: Verify every triggered GitHub workflow**

Use `gh run list` and `gh run watch` for CI, Documentation, and Documentation Links. Inspect logs for any failure; do not report deployment complete until all required runs conclude successfully.

- [ ] **Step 5: Prepare the next-milestone handoff prompt**

Include the canonical D-drive repo, current release/tag, fulfillment completion, Snowflake live validation state, runbook path, clean git state, next-roadmap inspection instructions, and the requested real DataMuru ASCII wordmark/banner discussion.
