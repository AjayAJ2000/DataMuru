# Provision a catalog and schemas

This tutorial creates a real Unity Catalog catalog and schemas. Use a unique,
non-production name.

!!! danger "Live cloud changes"
    The steps use `live-apply`. Confirm the target workspace and catalog name
    before running apply.

## Prerequisites

- successful `datamuru doctor` in `live-readonly`;
- permission to create catalogs and schemas;
- a running SQL warehouse and its ID if using Databricks default storage.

## Configure the SQL warehouse

Set the warehouse ID without storing it in source control:

```powershell
$env:DATABRICKS_SQL_WAREHOUSE_ID = "replace-with-warehouse-id"
```

Add the environment variable name to `providers/databricks.yml`:

```yaml
provider:
  cloud: azure
  execution_mode: live-apply
  host_env: DATABRICKS_HOST
  auth_type: pat
  token_env: DATABRICKS_TOKEN
  sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

## Declare the catalog

```yaml
workspace:
  name: example-dev
  cloud: azure
  region: eastus2
  catalogs:
    - name: dm_tutorial_analytics
      use_default_storage: true
      schemas:
        - bronze
        - silver
        - gold
```

`use_default_storage: true` creates the catalog through the Databricks SQL
Statements API. To use explicit cloud storage instead, see
[Manage catalogs and schemas](../guides/catalogs-and-schemas.md).

## Diagnose requirements

```powershell
datamuru validate --config datamuru.yml
datamuru doctor --config datamuru.yml
```

Doctor should report that a SQL warehouse ID is configured for default-storage
catalog creation.

## Plan the related resources

```powershell
datamuru plan --config datamuru.yml --target catalog:dm_tutorial_analytics
```

A catalog target includes schemas whose addresses begin with
`schema:dm_tutorial_analytics.`.

## Apply

```powershell
datamuru apply --config datamuru.yml --target catalog:dm_tutorial_analytics --auto-approve
```

Expected result: one catalog and three schemas are applied. DataMuru skips child
schemas if catalog creation fails.

## Verify

1. Open Catalog Explorer in Databricks.
2. Confirm the catalog and schemas exist.
3. Run the plan again.

```powershell
datamuru plan --config datamuru.yml --target catalog:dm_tutorial_analytics
```

The second plan should show no required changes.

## Clean up

Review dependencies before destroying a catalog. DataMuru does not assume that
dropping data-bearing resources is safe.

```powershell
datamuru destroy --config datamuru.yml --target catalog:dm_tutorial_analytics --confirm-destroy
```
