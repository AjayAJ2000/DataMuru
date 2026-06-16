# Environment variables

| Variable | Purpose | Required when |
| --- | --- | --- |
| `DATABRICKS_HOST` | Databricks workspace URL | referenced by `host_env` |
| `DATABRICKS_TOKEN` | Databricks PAT | `auth_type: pat` in live modes |
| `DATABRICKS_SQL_WAREHOUSE_ID` | SQL warehouse ID | referenced by `sql_warehouse_id_env` |

The names are configurable through `host_env`, `token_env`, and
`sql_warehouse_id_env`.

Set variables in the process that runs DataMuru. A variable set in another
terminal is not available automatically.

Never store secret values in:

- committed `.env` files;
- YAML configuration;
- saved plans;
- CI logs;
- screenshots or support tickets.
