# Snowflake Provider

The Snowflake provider is available as a state-only scaffold in the current
alpha. It lets teams validate provider-neutral configuration, plan databases
and schemas as DataMuru catalog/schema resources, and prepare for live provider
parity.

Use it today to prove the configuration and governance model. Do not use it
yet for live Snowflake mutations.

## Provider config

```yaml
provider:
  cloud: snowflake
  account_env: SNOWFLAKE_ACCOUNT
  user_env: SNOWFLAKE_USER
  auth_type: externalbrowser
  execution_mode: state-only
```

Supported auth fields:

| Field | Purpose |
| --- | --- |
| `account` / `account_env` | Snowflake account identifier. |
| `user` / `user_env` | User name when not resolved by SSO. |
| `auth_type` | Planned values include `externalbrowser`, `oauth`, `keypair`, and `password`. |
| `warehouse` | Default Snowflake warehouse for future live SQL execution. |
| `role` | Role for future live SQL execution. |

## Current support

| Capability | Status |
| --- | --- |
| Validation | Available |
| State-only plan/apply/destroy | Available |
| Database and schema desired resources | Available |
| Live discovery | Planned |
| Live SQL apply/destroy | Planned |
| Grant import | Planned |

The scaffold intentionally blocks live mutations until Snowflake SQL execution,
credential handling, and safety checks are tested.

## Free trial validation

Snowflake trials are useful for validating naming, environment layout, and
provider-neutral planning.

1. Create a Snowflake trial account.
2. Capture the account identifier, warehouse, role, and user.
3. Configure the Snowflake provider in `state-only` mode.
4. Declare target databases and schemas using DataMuru catalog/schema resources.
5. Run `validate` and `plan`.

```powershell
$env:SNOWFLAKE_ACCOUNT="your-account"
$env:SNOWFLAKE_USER="your-user"

datamuru validate --config datamuru.yml --strict
datamuru plan --config datamuru.yml
```

## Databricks to Snowflake

For cross-provider adoption, use the Databricks provider to discover bounded
source inventory and the Snowflake provider to model target state.

See [Databricks to Snowflake adoption path](../guides/databricks-to-snowflake.md)
for the recommended staged workflow.

## Live provider readiness checklist

Before Snowflake live execution is enabled, DataMuru needs:

- SQL API/session execution with explicit warehouse and role selection;
- idempotent database and schema create/update behavior;
- grant discovery and grant apply with privilege normalization;
- destructive-change protection for databases and schemas;
- integration tests against a Snowflake trial or sandbox account;
- docs for SSO, key-pair, OAuth, and password-based authentication;
- parity tests against provider-neutral resource contracts.
