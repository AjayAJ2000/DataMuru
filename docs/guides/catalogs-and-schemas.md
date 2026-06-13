# Manage catalogs and schemas

## Use Databricks default storage

```yaml
catalogs:
  - name: analytics
    use_default_storage: true
    schemas:
      - raw
      - curated
```

Configure `sql_warehouse_id` or `sql_warehouse_id_env` in the provider. DataMuru
uses the SQL Statements API because the Unity Catalog REST create endpoint may
require an explicit storage root.

## Use an explicit managed location

```yaml
catalogs:
  - name: analytics
    managed_location: abfss://catalog@account.dfs.core.windows.net/analytics
    schemas:
      - name: raw
        managed_location: abfss://catalog@account.dfs.core.windows.net/analytics/raw
```

Your Databricks metastore and storage credential configuration must authorize
the location.

## Mix string and object schemas

Use a string when a schema needs only a name. Use an object when it needs a
managed location.

## Plan the hierarchy

```powershell
datamuru plan --target catalog:analytics
```

DataMuru applies the catalog before schemas and skips schemas if the catalog
fails.

## Avoid system schemas

Do not declare or destroy `information_schema`. Databricks owns it. DataMuru
filters common system schemas during observation and import discovery.
