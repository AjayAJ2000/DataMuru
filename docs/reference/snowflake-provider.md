# Snowflake Provider

The Snowflake provider is available for provider-neutral planning and
live-readonly database/schema discovery in the current alpha. It lets teams
validate Snowflake target configuration, inspect existing databases and schemas,
and prepare for broader provider parity.

Use it today to prove the configuration and inventory model. Do not use it yet
for live Snowflake mutations.

Install the Snowflake extra before live discovery:

```powershell
pip install "datamuru[snowflake]"
```

Generate a provider-correct starter project:

```powershell
datamuru init `
  --name snowflake-smoke `
  --provider snowflake `
  --execution-mode live-readonly `
  --output-dir .\snowflake-smoke
```

## Provider config

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

Supported auth fields:

| Field | Purpose |
| --- | --- |
| `account` / `account_env` | Snowflake account identifier. |
| `host` / `host_env` | Snowflake hostname or full HTTPS URL. PAT mode normalizes this in memory. |
| `user` / `user_env` | User name when not resolved by SSO. |
| `auth_type` | Reviewed authentication mode: `externalbrowser`, `snowflake`, or `programmatic_access_token`. |
| `password_env` | Optional environment variable for password auth when `auth_type: snowflake` is approved for a sandbox. |
| `token_env` | Environment variable containing a Snowflake PAT when `auth_type: programmatic_access_token`. |
| `warehouse` | Default Snowflake warehouse for discovery sessions. |
| `role` | Role for discovery sessions. |

Use the organization-account form for `SNOWFLAKE_ACCOUNT`, such as
`acme-analytics`. Do not include `https://` or `.snowflakecomputing.com`.
`warehouse` and `role` are non-secret provider values and currently remain in
the provider file rather than separate environment variables.

Browser SSO is the default and does not require a password in project files. A
disposable trial user can use password authentication for non-interactive test
automation:

```yaml
provider:
  cloud: snowflake
  account_env: SNOWFLAKE_ACCOUNT
  user_env: SNOWFLAKE_USER
  auth_type: snowflake
  password_env: SNOWFLAKE_PASSWORD
  warehouse: COMPUTE_WH
  role: DATAMURU_READONLY
  execution_mode: live-readonly
```

Keep `SNOWFLAKE_PASSWORD` in the current shell or an approved secret store.
Never write it into YAML or `.env.example`.

## Programmatic Access Token authentication

PAT authentication is supported for non-interactive `live-readonly` discovery:

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

`SNOWFLAKE_HOST` may be either a hostname or full HTTPS URL. DataMuru removes
the scheme, path, port, query, fragment, and trailing slash in memory. It
rejects hosts outside `snowflakecomputing.com`.

Account resolution uses literal `account`, then `account_env`, then the first
DNS label of the normalized host. Set an explicit account when your Snowflake
deployment requires an account identifier that differs from that label.

Set the values only in your shell or approved secret store:

```powershell
$env:SNOWFLAKE_HOST="https://your-account.snowflakecomputing.com"
$env:SNOWFLAKE_USERNAME="your-user"
$env:SNOWFLAKE_TOKEN="<token-from-secret-store>"
```

Snowflake requires a PAT user to be subject to a network policy. DataMuru does
not create or change that policy. Without one, the expected provider response
is `Network policy is required`. Snowflake also supports a token-specific
`MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT` setting for at most 1440 minutes;
use that only for an approved temporary trial because it does not bypass an
existing policy.

Create, rotate, and revoke PATs from an independently authenticated Snowflake
administrative session. To revoke the test token:

```sql
ALTER USER IF EXISTS <username> REMOVE PAT terminal_token;
```

A PAT-authenticated session cannot revoke the PAT it is using. See Snowflake's
[PAT removal reference](https://docs.snowflake.com/en/sql-reference/sql/alter-user-remove-programmatic-access-token).

## Current support

| Capability | Status |
| --- | --- |
| Validation | Available |
| State-only plan/apply/destroy | Available |
| Database and schema desired resources | Available |
| Live database/schema discovery | Available in `live-readonly` |
| PAT authentication | Available in `live-readonly`; Snowflake network policy required |
| Live SQL apply/destroy | Planned |
| Grant import | Planned |

The provider intentionally blocks live mutations until Snowflake SQL execution,
credential handling, and safety checks are tested.

## Free trial validation

Snowflake trials are useful for validating naming, environment layout, and
provider-neutral planning.

1. Create a Snowflake trial account.
2. Capture the organization-account identifier, warehouse, read-only role, and user.
3. Configure the Snowflake provider in `live-readonly` mode.
4. Run `validate`, `doctor`, and bounded import discovery.
5. Declare target databases and schemas using DataMuru catalog/schema resources.
6. Run `plan`.

```powershell
$env:SNOWFLAKE_ACCOUNT="your-account"
$env:SNOWFLAKE_USER="your-user"

datamuru validate --config datamuru.yml --strict
datamuru doctor --config datamuru.yml
datamuru import discover --config datamuru.yml --catalog FINANCE
datamuru plan --config datamuru.yml
```

`doctor` checks configuration shape and connector availability. The bounded
`import discover` command is the first live SQL connection test.

Snowflake discovery maps Snowflake databases to DataMuru catalogs and Snowflake
schemas to DataMuru schemas. It filters common Snowflake system databases and
`INFORMATION_SCHEMA` unless `--include-system` is provided.

## Databricks to Snowflake

For cross-provider adoption, use the Databricks provider to discover bounded
source inventory and the Snowflake provider to model target state.

See [Databricks to Snowflake adoption path](../guides/databricks-to-snowflake.md)
for the recommended staged workflow.

## Live provider readiness checklist

Before Snowflake live apply/destroy and RBAC import are enabled, DataMuru needs:

- idempotent database and schema create/update behavior;
- grant discovery and grant apply with privilege normalization;
- destructive-change protection for databases and schemas;
- integration tests against a Snowflake trial or sandbox account;
- deeper docs for SSO, key-pair, OAuth, and password-based authentication;
- parity tests against provider-neutral resource contracts.
