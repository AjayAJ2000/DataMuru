# Authenticate to Databricks

DataMuru currently documents PAT authentication for local use. Provider
configuration also recognizes `databricks-cli`, `oauth`, and
`azure-managed-identity`, but live HTTP operations in the alpha are most
thoroughly tested with PAT headers.

## Configure PAT authentication

```yaml
provider:
  cloud: azure
  host_env: DATABRICKS_HOST
  auth_type: pat
  token_env: DATABRICKS_TOKEN
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
  execution_mode: live-readonly
```

Set the variable in the current process:

=== "Windows PowerShell"

    ```powershell
    $env:DATABRICKS_HOST = "https://your-workspace.cloud.databricks.com"
    $env:DATABRICKS_TOKEN = "replace-with-your-token"
    $env:DATABRICKS_SQL_WAREHOUSE_ID = "replace-with-your-warehouse-id"
    ```

=== "macOS or Linux"

    ```bash
    export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
    export DATABRICKS_TOKEN="replace-with-your-token"
    export DATABRICKS_SQL_WAREHOUSE_ID="replace-with-your-warehouse-id"
    ```

## Verify authentication

```powershell
datamuru doctor --config datamuru.yml
```

Doctor checks whether the variable exists and probes the workspace identity
endpoint in live modes.

## Protect credentials

- Never commit a token.
- Prefer short-lived credentials where your Databricks environment supports
  them.
- Use a secret manager in CI.
- Scope permissions to the objects the workflow manages.
- Rotate a token immediately if it appears in logs, screenshots, or Git history.

See [Security and credentials](../operations/security.md).
