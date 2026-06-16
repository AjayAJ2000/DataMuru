# Databricks provider

`providers/databricks.yml` contains a top-level `provider` mapping.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `cloud` | string | required | `azure`, `aws`, or `gcp` |
| `host` | URL | none | Workspace origin |
| `host_env` | string | none | Environment variable containing the workspace origin |
| `auth_type` | string | `pat` | `pat`, `databricks-cli`, `oauth`, or `azure-managed-identity` |
| `token_env` | string | none | Environment variable containing a PAT |
| `execution_mode` | string | `state-only` | `state-only`, `live-readonly`, or `live-apply` |
| `connect_timeout_seconds` | integer | `10` | HTTP connection timeout |
| `account_id` | string | none | Databricks account identifier for account-level operations |
| `sql_warehouse_id` | string | none | Direct SQL warehouse ID |
| `sql_warehouse_id_env` | string | none | Environment variable containing the warehouse ID |
| `credential_mode` | string | none | Descriptive credential mode |

Prefer `host_env`, `sql_warehouse_id_env`, and `token_env` over literal secrets
or environment-specific identifiers. If both `host` and `host_env` are set,
DataMuru uses `host` unless it is empty or still contains the starter
placeholder.

See [Authentication](../guides/authentication.md) and
[Execution modes](../guides/execution-modes.md).
