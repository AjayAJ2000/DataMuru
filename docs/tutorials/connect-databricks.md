# Connect a Databricks workspace

This tutorial verifies a real Databricks connection without allowing DataMuru
to mutate the workspace.

## Prerequisites

- an installed DataMuru package;
- a Databricks workspace URL;
- a personal access token with permission to read the workspace;
- one workspace YAML file in the project.

## Set the token

=== "Windows PowerShell"

    ```powershell
    $env:DATABRICKS_TOKEN = "replace-with-your-token"
    ```

=== "macOS or Linux"

    ```bash
    export DATABRICKS_TOKEN="replace-with-your-token"
    ```

Do not write the token into YAML, shell history, screenshots, or issue reports.

## Configure read-only execution

Update `providers/databricks.yml`:

```yaml
provider:
  cloud: azure
  execution_mode: live-readonly
  host: https://your-workspace.cloud.databricks.com
  auth_type: pat
  token_env: DATABRICKS_TOKEN
  connect_timeout_seconds: 10
```

Replace the host with the exact workspace origin. Do not include a path such as
`/sql/warehouses`.

## Validate before connecting

```powershell
datamuru validate --config datamuru.yml
```

Validation checks the file tree and field combinations. It does not prove that
the token can access Databricks.

## Run provider diagnostics

```powershell
datamuru doctor --config datamuru.yml
```

A successful report includes:

- a valid cloud and host;
- an available token environment variable;
- `live-readonly` execution mode;
- at least one workspace declaration;
- a successful connectivity probe and current user.

If connectivity fails, use [Troubleshooting](../guides/troubleshooting.md).

## Observe a plan

```powershell
datamuru plan --config datamuru.yml
```

In live modes, DataMuru observes supported desired resources before comparing
them with configuration. Existing catalogs and schemas that match the desired
configuration should appear as no-op rather than create actions.

## Prove that mutation is blocked

Do not run this against important resources. With a unique test declaration,
an apply in `live-readonly` fails with a structured provider error:

```powershell
datamuru apply --config datamuru.yml --target catalog:unique_test_name --auto-approve
```

The read-only guard is intentional. Switch to `live-apply` only after reviewing
[Choose an execution mode](../guides/execution-modes.md).
