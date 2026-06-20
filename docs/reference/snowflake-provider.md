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
| `user` / `user_env` | User name when not resolved by SSO. |
| `auth_type` | Snowflake connector authenticator, such as `externalbrowser`, `oauth`, `snowflake`, or key-pair-compatible modes. |
| `password_env` | Optional environment variable for password auth when `auth_type: snowflake` is approved for a sandbox. |
| `warehouse` | Default Snowflake warehouse for discovery sessions. |
| `role` | Role for discovery sessions. |

## Current support

| Capability | Status |
| --- | --- |
| Validation | Available |
| State-only plan/apply/destroy | Available |
| Database and schema desired resources | Available |
| Live database/schema discovery | Available in `live-readonly` |
| Live SQL apply/destroy | Planned |
| Grant import | Planned |

The provider intentionally blocks live mutations until Snowflake SQL execution,
credential handling, and safety checks are tested.

## Free trial validation

Snowflake trials are useful for validating naming, environment layout, and
provider-neutral planning.

1. Create a Snowflake trial account.
2. Capture the account identifier, warehouse, role, and user.
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
