# Use Databricks Free Edition

Databricks Free Edition is suitable for learning and limited integration tests.
It is not equivalent to a full enterprise Databricks account.

Because Databricks capabilities and quotas can change, review the current
[Free Edition documentation](https://docs.databricks.com/aws/en/getting-started/free-edition)
and [limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
before testing.

## What to test

Free Edition can be useful for:

- PAT-based workspace connectivity;
- catalog and schema discovery;
- catalog and schema creation when your workspace permits it;
- default-storage catalog creation through a SQL warehouse;
- Unity Catalog grants supported by the workspace;
- import discovery and YAML generation.

Do not rely on Free Edition for:

- multi-workspace orchestration;
- account-console administration;
- enterprise SSO, SCIM, or networking;
- production scale, quotas, or service commitments.

## Configure the provider

```yaml
provider:
  cloud: azure
  execution_mode: live-readonly
  host: https://your-workspace.cloud.databricks.com
  auth_type: pat
  token_env: DATABRICKS_TOKEN
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

The hostname can contain `cloud.databricks.com` even when the provider cloud is
Azure. Use the actual workspace URL shown by Databricks.

## Test in stages

### 1. Validate locally

```powershell
datamuru validate --config datamuru.yml
```

### 2. Verify read-only connectivity

```powershell
datamuru doctor --config datamuru.yml
datamuru import discover --config datamuru.yml
```

### 3. Create a unique test catalog

Switch to `live-apply` and use a name that cannot collide with important
resources:

```yaml
catalogs:
  - name: dm_free_tutorial_01
    use_default_storage: true
    schemas:
      - bronze
      - silver
```

```powershell
datamuru plan --target catalog:dm_free_tutorial_01
datamuru apply --target catalog:dm_free_tutorial_01 --auto-approve
datamuru plan --target catalog:dm_free_tutorial_01
```

## Understand default storage

The Unity Catalog REST API can reject catalog creation when the metastore has no
storage root. `use_default_storage: true` makes DataMuru submit `CREATE CATALOG`
through a configured SQL warehouse, allowing Databricks to select account
default storage where available.

## Identity limitation

Use existing users and groups for ACL assignments. Managed identity lifecycle
is an Enterprise feature and requires account SCIM capability. DataMuru probes
capability when managed identities are declared; edition configuration alone
cannot create an unavailable Databricks API.

## Clean up

Confirm that the catalog contains no needed data, then:

```powershell
datamuru destroy --target catalog:dm_free_tutorial_01 --confirm-destroy
```
