# Snowflake Programmatic Access Token Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit, redacted Snowflake Programmatic Access Token authentication for live-readonly DataMuru discovery using the configured host, token, and username environment variables.

**Architecture:** Extend the focused Snowflake auth model with host normalization, account derivation, and PAT token resolution. Keep connector keyword construction in `SnowflakeSqlClient`, expose readiness through existing doctor checks, and preserve browser SSO and password behavior without generic connector passthrough.

**Tech Stack:** Python 3.11+, Pydantic/DataMuruModel, Snowflake Connector for Python 3.18, pytest, Ruff, MkDocs Material, GitHub Actions.

---

## File Map

- Create `tests/unit/test_snowflake_pat_auth.py`: host normalization, account precedence, PAT connector arguments, redaction, and doctor checks.
- Modify `datamuru/providers/snowflake/auth.py`: host/token fields and redacted resolution helpers.
- Modify `datamuru/providers/snowflake/client.py`: reviewed PAT connector arguments and local missing-credential errors.
- Modify `datamuru/providers/snowflake/provider.py`: PAT-aware authenticate and doctor readiness checks.
- Modify `datamuru/bootstrap.py`: generated Snowflake PAT opt-in guidance without secret values.
- Modify `tests/unit/test_cli.py`: generated PAT guidance assertions.
- Modify `docs/reference/snowflake-provider.md`: exact PAT configuration and network-policy boundary.
- Modify `docs/guides/authentication.md`: supported Snowflake authentication modes.
- Modify `docs/operations/milestone-0-4-test-runbook.md`: PAT identity, discovery, redaction, policy, and revocation tests.
- Modify `docs/reference/capabilities.md`: bounded Snowflake PAT capability statement.
- Modify `CHANGELOG.md`: unreleased PAT support entry.
- Modify `docs/superpowers/specs/2026-06-28-snowflake-pat-authentication-design.md`: implementation status.

### Task 1: Host, Account, And Token Resolution

**Files:**
- Create: `tests/unit/test_snowflake_pat_auth.py`
- Modify: `datamuru/providers/snowflake/auth.py`

- [ ] **Step 1: Write failing auth-resolution tests**

Add tests with wished-for configuration:

```python
def test_pat_auth_resolves_host_account_user_and_token(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_HOST", "https://acme-analytics.snowflakecomputing.com/")
    monkeypatch.setenv("SNOWFLAKE_USERNAME", "operator")
    monkeypatch.setenv("SNOWFLAKE_TOKEN", "pat-secret")
    auth = SnowflakeAuthConfig.model_validate(
        {
            "host_env": "SNOWFLAKE_HOST",
            "user_env": "SNOWFLAKE_USERNAME",
            "token_env": "SNOWFLAKE_TOKEN",
            "auth_type": "programmatic_access_token",
            "execution_mode": "live-readonly",
        }
    )

    assert auth.resolve_host() == "acme-analytics.snowflakecomputing.com"
    assert auth.resolve_account() == "acme-analytics"
    assert auth.resolve_user() == "operator"
    assert auth.resolve_token() == "pat-secret"
```

Add separate tests for hostname input without a scheme, explicit `account`
precedence, `account_env` precedence, and rejection of a non-Snowflake hostname.

- [ ] **Step 2: Run tests and verify RED**

Run:

```powershell
python -m pytest tests\unit\test_snowflake_pat_auth.py -q --basetemp .datamuru\pytest-pat-auth-red -p no:cacheprovider
```

Expected: failures report missing `host_env`, `token_env`, `resolve_host`, and
`resolve_token` behavior.

- [ ] **Step 3: Implement minimal resolution helpers**

Add fields and helpers with this public shape:

```python
class SnowflakeAuthConfig(DataMuruModel):
    host: str | None = None
    host_env: str | None = None
    token_env: str | None = None

    def resolve_host(self) -> str | None:
        value = self.host or (os.getenv(self.host_env) if self.host_env else None)
        return normalize_snowflake_host(value)

    def resolve_account(self) -> str | None:
        if self.account:
            return self.account
        if self.account_env:
            return os.getenv(self.account_env)
        host = self.resolve_host()
        return host.split(".", 1)[0] if host else None

    def resolve_token(self) -> str | None:
        return os.getenv(self.token_env) if self.token_env else None

    def uses_programmatic_access_token(self) -> bool:
        return self.auth_type.casefold() == "programmatic_access_token"
```

`normalize_snowflake_host()` uses `urllib.parse.urlparse`, strips URL-only
components, lowercases the hostname, and returns `None` unless it ends with
`.snowflakecomputing.com`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Task 1 pytest command. Expected: all resolution tests pass.

### Task 2: Reviewed PAT Connector Arguments

**Files:**
- Modify: `tests/unit/test_snowflake_pat_auth.py`
- Modify: `datamuru/providers/snowflake/client.py`

- [ ] **Step 1: Write failing connector tests**

Require this connector payload without serializing it:

```python
kwargs = SnowflakeSqlClient(auth)._connection_kwargs()
assert kwargs == {
    "account": "acme-analytics",
    "host": "acme-analytics.snowflakecomputing.com",
    "user": "operator",
    "authenticator": "PROGRAMMATIC_ACCESS_TOKEN",
    "token": "pat-secret",
    "warehouse": "COMPUTE_WH",
    "role": "SYSADMIN",
}
```

Add a missing-token test that expects `ProviderError`, includes only the
configured `token_env` name in context, and proves `pat-secret` is absent from
the exception. Add preservation tests for external-browser and password paths.

- [ ] **Step 2: Run connector tests and verify RED**

Run the focused test file. Expected: PAT kwargs lack host/token and use the
lowercase authenticator.

- [ ] **Step 3: Implement PAT-specific kwargs**

Build kwargs from resolved values. For PAT mode:

```python
if self.auth.uses_programmatic_access_token():
    token = self.auth.resolve_token()
    if not token:
        raise ProviderError(
            description="Snowflake Programmatic Access Token is required for PAT authentication.",
            context={"token_env": self.auth.token_env},
            suggestion="Set the configured token environment variable before live discovery.",
        )
    kwargs["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
    kwargs["token"] = token
```

Pass normalized `host` when available. Keep password handling restricted to
non-PAT modes.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the focused test file. Expected: PAT, external-browser, password, and
missing-token tests pass.

### Task 3: PAT-Aware Doctor Checks

**Files:**
- Modify: `tests/unit/test_snowflake_pat_auth.py`
- Modify: `datamuru/providers/snowflake/provider.py`

- [ ] **Step 1: Write failing doctor tests**

Construct `SnowflakeProvider` with PAT environment-variable names and assert:

```python
checks = {check.code: check for check in provider.doctor(None, "dev").checks}
assert checks["provider.account"].level == "ok"
assert checks["provider.user"].level == "ok"
assert checks["provider.pat"].level == "ok"
assert "pat-secret" not in json.dumps([check.model_dump() for check in checks.values()])
```

Add a missing-token case where `provider.pat` is `error` and mentions only
`SNOWFLAKE_TOKEN`.

- [ ] **Step 2: Run doctor tests and verify RED**

Run the focused test file. Expected: no `provider.pat` check exists.

- [ ] **Step 3: Add doctor readiness checks**

Treat either a resolved explicit account or a valid host-derived account as
configured. Add `provider.pat` only for PAT mode, with `ok` when the configured
token variable is present and `error` when absent. Update `authenticate()` to
require both account posture and token posture for PAT mode.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the focused test file. Expected: PAT doctor tests pass without disclosure.

### Task 4: Starter Guidance And Documentation

**Files:**
- Modify: `datamuru/bootstrap.py`
- Modify: `tests/unit/test_cli.py`
- Modify: `docs/reference/snowflake-provider.md`
- Modify: `docs/guides/authentication.md`
- Modify: `docs/operations/milestone-0-4-test-runbook.md`
- Modify: `docs/reference/capabilities.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/specs/2026-06-28-snowflake-pat-authentication-design.md`

- [ ] **Step 1: Write the failing starter assertion**

Extend the Snowflake init test to require generated `.env.example` and README
guidance containing `SNOWFLAKE_TOKEN`, `host_env`, `token_env`, and
`programmatic_access_token`, while proving no literal token value is generated.

- [ ] **Step 2: Run the init test and verify RED**

Run:

```powershell
python -m pytest tests\unit\test_cli.py::test_init_command_creates_provider_specific_snowflake_project -q --basetemp .datamuru\pytest-pat-init-red -p no:cacheprovider
```

Expected: generated guidance does not yet mention PAT opt-in.

- [ ] **Step 3: Add generated PAT opt-in guidance**

Keep browser SSO as the generated provider default. Add commented PAT
environment guidance to `.env.example` and an exact provider snippet to the
generated README. Never generate a token value.

- [ ] **Step 4: Update public docs and runbook**

Document:

- the exact PAT provider fields;
- full URL and hostname normalization;
- explicit account precedence;
- Snowflake's network-policy prerequisite;
- the expected `Network policy is required` failure;
- identity and bounded discovery commands;
- redaction checks;
- `ALTER USER ... REMOVE PROGRAMMATIC ACCESS TOKEN` revocation guidance;
- live mutation remaining unavailable.

Mark the design status `implemented, pending milestone release` only after all
local gates pass.

- [ ] **Step 5: Run documentation checks**

```powershell
python -m pytest tests\unit\test_documentation.py -q --basetemp .datamuru\pytest-pat-docs -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
```

Expected: documentation tests and strict MkDocs build exit zero.

### Task 5: Live-Readonly Snowflake Validation

**Files:**
- Generate ignored test artifacts under `.datamuru/snowflake-pat-live/`.

- [ ] **Step 1: Generate an ignored Snowflake project**

```powershell
python -m datamuru.cli.main --no-banner init `
  --name snowflake-pat-live `
  --provider snowflake `
  --execution-mode live-readonly `
  --output-dir .datamuru\snowflake-pat-live
```

Use the approved PAT provider fields and the existing User-scope environment
variables. Do not write resolved values to disk.

- [ ] **Step 2: Run DataMuru doctor**

Run doctor with JSON parsed in memory and print only check codes and levels.
Expected: account, user, PAT, connector, and execution-mode checks are ready or
informational without credential values.

- [ ] **Step 3: Run bounded discovery through the Python API**

Call `DataMuru(...).import_discover()` and print only provider, success state,
database count, and aggregate schema count. Expected: live discovery completes
without printing inventory names and without mutation.

- [ ] **Step 4: Verify secret absence**

Search tracked files and generated artifacts for the resolved PAT value in
memory without printing it. Expected: zero matches.

### Task 6: Full Verification And Deployment

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run the complete local gate**

```powershell
python -m ruff check datamuru tests
python -m pytest -q --basetemp .datamuru\pytest-pat-final -p no:cacheprovider
$env:NO_MKDOCS_2_WARNING='1'
python -m mkdocs build --strict
git diff --check
```

Expected: every command exits zero.

- [ ] **Step 2: Review the diff against the spec**

Confirm every acceptance criterion has a test or runbook step, PAT values never
enter serialized objects, existing auth modes remain compatible, and no live
mutation is enabled.

- [ ] **Step 3: Commit and push**

```powershell
git add CHANGELOG.md datamuru docs tests
git commit -m "Add Snowflake PAT authentication"
git push origin main
```

- [ ] **Step 4: Verify required pipelines**

Wait for CI, Documentation, and Documentation Links for the pushed SHA. Require
all three conclusions to be `success` before starting another implementation.
