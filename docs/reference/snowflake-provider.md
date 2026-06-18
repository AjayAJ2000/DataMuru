# Snowflake Provider

The Snowflake provider is available as a state-only scaffold in the current
alpha. It lets teams validate provider-neutral configuration, plan databases
and schemas as DataMuru catalog/schema resources, and prepare for live provider
parity.

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
