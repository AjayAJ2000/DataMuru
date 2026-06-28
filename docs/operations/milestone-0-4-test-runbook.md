# Milestone 0.4 test runbook

Use this runbook to test the 0.4.0a0 milestone features end to end. Run each
feature independently and capture the command, output, generated files, and any
provider error details when reporting bugs.

## Scope

This runbook covers:

- Databricks grant scan budgets by object type;
- import progress checkpoints;
- resumable enterprise import jobs;
- enterprise import suite naming;
- Snowflake live-readonly discovery;
- Databricks-to-Snowflake mapping drafts;
- GitHub issue draft export for agile planning.

## Before you start

Use a sandbox project and non-production provider accounts.

```powershell
python -m pip install -e ".[dev,docs,databricks,snowflake]"
python -m datamuru.cli.main --no-banner validate --config datamuru.yml --strict
python -m datamuru.cli.main --no-banner doctor --config datamuru.yml
```

Capture:

- DataMuru version or commit SHA;
- Python version;
- provider config with secrets redacted;
- execution mode;
- exact command and full output.

Do not paste PATs, OAuth tokens, private keys, workspace secrets, customer data,
or generated state files that contain sensitive identifiers.

## 1. Import progress checkpoint

Run a bounded Databricks discovery with JSON output:

```powershell
python -m datamuru.cli.main --no-banner import discover `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --output json `
  --progress-checkpoint .\.datamuru\imports\progress.json
```

Expected result:

- command exits successfully;
- `.datamuru/imports/progress.json` exists;
- checkpoint contains `updated_at` and an `event` object;
- stdout remains valid JSON when `--output json` is used.

Bug evidence to capture:

- command output;
- redacted `progress.json`;
- whether the command was interrupted or completed.

## 2. Grant scan budgets

Start with a safe low budget:

```powershell
python -m datamuru.cli.main --no-banner import discover `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --include-grants `
  --grant-scope all `
  --max-catalog-grant-objects 1 `
  --max-schema-grant-objects 1
```

Expected result:

- small catalogs may pass;
- larger catalogs should stop before launching expensive grant scans;
- error context should show object type, objects in scope, and configured cap.

Then raise the schema cap for a selected catalog:

```powershell
python -m datamuru.cli.main --no-banner import discover `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --include-grants `
  --grant-scope all `
  --max-grant-objects 100 `
  --max-schema-grant-objects 100
```

Expected result:

- scoped grant discovery completes or fails with a provider-specific error;
- DataMuru should not silently scan more objects than the configured cap.

## 3. Resumable import job checkpoint

Run discovery with both checkpoint types:

```powershell
python -m datamuru.cli.main --no-banner import discover `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --include-grants `
  --grant-scope all `
  --job-checkpoint .\.datamuru\imports\<catalog_name>.job.json `
  --progress-checkpoint .\.datamuru\imports\<catalog_name>.progress.json
```

Expected result:

- job checkpoint contains `completed_grant_targets`;
- job checkpoint contains discovered `grants` when grants are available;
- progress checkpoint shows the latest event.

Resume with the same scope:

```powershell
python -m datamuru.cli.main --no-banner import discover `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --include-grants `
  --grant-scope all `
  --resume-from .\.datamuru\imports\<catalog_name>.job.json `
  --job-checkpoint .\.datamuru\imports\<catalog_name>.job.json
```

Expected result:

- completed grant targets are skipped;
- catalog/schema inventory is refreshed;
- output still reflects the requested catalog scope.

## 4. Enterprise import suite naming

Generate a bounded import review suite:

```powershell
python -m datamuru.cli.main --no-banner import generate `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --include-identities `
  --include-grants `
  --grant-scope catalog `
  --suite-layout enterprise `
  --suite-out .\imports
```

Expected files:

- `imports/workspaces/databricks.<env>.<workspace>.<catalog>.workspace.yml`;
- `imports/governance/databricks.<env>.<workspace>.<catalog>.rbac.yml`;
- taxonomy and masking review files when generated.

Review:

- no secrets in generated files;
- imported identities are lifecycle `existing`;
- RBAC assignments are starter review material, not blindly approved changes.

## 5. Snowflake live-readonly discovery

Configure Snowflake credentials without secrets in YAML:

```powershell
$env:SNOWFLAKE_ACCOUNT="<organization-account>"
$env:SNOWFLAKE_USER="<user>"
```

Do not use the full Snowflake browser hostname for `SNOWFLAKE_ACCOUNT`.

Provider example:

```yaml
provider:
  cloud: snowflake
  account_env: SNOWFLAKE_ACCOUNT
  user_env: SNOWFLAKE_USER
  auth_type: externalbrowser
  warehouse: COMPUTE_WH
  role: SYSADMIN
  execution_mode: live-readonly
```

Run:

```powershell
python -m datamuru.cli.main --no-banner validate --config datamuru.yml --strict
python -m datamuru.cli.main --no-banner doctor --config datamuru.yml
python -m datamuru.cli.main --no-banner import discover --config datamuru.yml --catalog <database_name>
```

Expected result:

- doctor reports Snowflake account and connector readiness;
- bounded discovery completes the first live Snowflake SQL connection;
- discovery returns Snowflake databases as DataMuru catalogs;
- schemas are listed under each selected database;
- apply and destroy remain blocked for live Snowflake mutation.

### Snowflake PAT authentication

Use this path for a non-interactive Snowflake trial or sandbox. Keep the token
out of files, command history, screenshots, and bug reports.

```yaml
provider:
  cloud: snowflake
  host_env: SNOWFLAKE_HOST
  user_env: SNOWFLAKE_USERNAME
  token_env: SNOWFLAKE_TOKEN
  auth_type: programmatic_access_token
  warehouse: COMPUTE_WH
  role: SYSADMIN
  execution_mode: live-readonly
```

Set the three variables in the same PowerShell process that runs DataMuru:

```powershell
$env:SNOWFLAKE_HOST="https://<account>.snowflakecomputing.com"
$env:SNOWFLAKE_USERNAME="<user>"
$env:SNOWFLAKE_TOKEN="<token-from-secret-store>"
```

Run the redacted readiness checks:

```powershell
python -m datamuru.cli.main --no-banner validate --config datamuru.yml --strict
python -m datamuru.cli.main --no-banner doctor --config datamuru.yml --output json
```

Expected result:

- `provider.account`, `provider.user`, and `provider.pat` are `ok`;
- `provider.connector` is `ok` when `datamuru[snowflake]` is installed;
- output contains environment-variable names but no credential values.

Run bounded discovery against one database:

```powershell
python -m datamuru.cli.main --no-banner import discover `
  --config datamuru.yml `
  --catalog <database_name>
```

Expected result:

- the identity handshake and database/schema reads complete;
- output is limited to the requested database;
- no Snowflake mutation is attempted;
- live apply and destroy remain unavailable.

If Snowflake returns `Network policy is required`, stop and ask the Snowflake
operator to attach an approved network policy to the PAT user. DataMuru does
not create that policy. Snowflake's token-specific temporary bypass is limited
to 1440 minutes and is suitable only for an explicitly approved trial.

After testing, revoke the PAT from a separate browser SSO or administrative
session, not from the session authenticated by that PAT:

```sql
ALTER USER IF EXISTS <username> REMOVE PAT terminal_token;
```

Then clear the local process value:

```powershell
Remove-Item Env:SNOWFLAKE_TOKEN
```

Record only pass/fail state, check codes, and aggregate database/schema counts.
Never attach the PAT, username, host, inventory names, or raw connector output
to a bug report.

## 6. Databricks-to-Snowflake mapping draft

Run from a Databricks-configured project:

```powershell
python -m datamuru.cli.main --no-banner import map-snowflake `
  --config datamuru.yml `
  --catalog <catalog_name> `
  --target-account <snowflake_account_label> `
  --target-workspace <snowflake_workspace_label> `
  --database-prefix DM `
  --out .\migrations\databricks-to-snowflake\<catalog_name>.mapping.yml
```

Expected result:

- mapping YAML contains `migration.source.provider: databricks`;
- mapping YAML contains `migration.target.provider: snowflake`;
- Databricks catalogs map to Snowflake databases;
- Databricks schemas map to Snowflake schemas;
- file includes review notes and does not apply any Snowflake changes.

Review before implementation:

- database naming;
- schema case;
- reserved words;
- whether one Databricks catalog should become one Snowflake database;
- RBAC and role-model differences.

## 7. GitHub issue draft export

Export the roadmap backlog locally:

```powershell
python -m datamuru.cli.main --no-banner agile export `
  --format github-issues `
  --release-target 0.4.0a0 `
  --out .\github-issue-drafts\0.4.0a0
```

Expected result:

- one Markdown issue draft per roadmap row in the release target;
- `manifest.json` lists every draft;
- labels include area, risk, release, edition, and provider where relevant;
- no GitHub network access or credentials are required.

Review generated issues before creating public GitHub issues. Keep Enterprise,
customer, and security-sensitive items private.

## 8. Local quality gate

Run this before reporting the milestone as tested:

```powershell
python -m ruff check datamuru tests
python -m pytest tests\unit -q
python -m mkdocs build --strict
```

Expected result:

- lint passes;
- unit tests pass;
- documentation builds strictly.

## Bug report template

When a test fails, capture:

- feature under test;
- exact command;
- full output;
- expected result from this runbook;
- actual result;
- generated files with secrets removed;
- provider account type, for example Databricks Free Edition, Databricks Enterprise, or Snowflake trial;
- whether the failure is reproducible on a second run.

Do not include provider tokens, private keys, customer data, or raw state files.
