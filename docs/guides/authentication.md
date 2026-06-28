# Authenticate to data providers

## Databricks

DataMuru supports multiple Databricks authentication shapes. PAT auth is useful
for local evaluation. Enterprise pilots should prefer Databricks CLI profiles,
OAuth bearer tokens, or Enterprise credential extensions approved by the
organization.

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

## Use a Databricks CLI profile

If your enterprise laptop already uses the Databricks CLI, DataMuru can read
`.databrickscfg` directly:

```yaml
provider:
  cloud: azure
  auth_type: databricks-cli
  profile: enterprise-dev
  execution_mode: live-readonly
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

Optional overrides:

```powershell
$env:DATABRICKS_CONFIG_FILE="<path-to-your-databrickscfg>"
$env:DATABRICKS_CONFIG_PROFILE="enterprise-dev"
```

Run:

```powershell
databricks auth login --profile enterprise-dev
datamuru doctor --config datamuru.yml
```

The OSS implementation reads host and bearer token values from the profile.
Enterprise extensions can replace token loading with SSO, managed identity,
OAuth M2M, or internal brokered credential flows.

## Enterprise SSO and managed identity

`auth_type: oauth` can use a bearer token supplied through `token_env`.
`auth_type: azure-managed-identity` is reserved for the Enterprise provider
extension because token minting, role assignment, and network policy differ by
customer environment.

## Protect credentials

- Never commit a token.
- Prefer short-lived credentials where your Databricks environment supports
  them.
- Use a secret manager in CI.
- Scope permissions to the objects the workflow manages.
- Rotate a token immediately if it appears in logs, screenshots, or Git history.

See [Security and credentials](../operations/security.md).

## Snowflake Programmatic Access Token

For non-interactive Snowflake discovery, keep all credential values in the
environment and reference only their names in configuration:

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

```powershell
$env:SNOWFLAKE_HOST="https://your-account.snowflakecomputing.com"
$env:SNOWFLAKE_USERNAME="your-user"
$env:SNOWFLAKE_TOKEN="<token-from-secret-store>"
datamuru doctor --config datamuru.yml
```

`doctor` reports whether the named PAT variable is available but never emits
its value. The Snowflake user must satisfy Snowflake's network-policy
requirement. DataMuru does not generate PATs or manage network policies.

See [Snowflake provider](../reference/snowflake-provider.md) for account
resolution, revocation, and bounded discovery guidance.
