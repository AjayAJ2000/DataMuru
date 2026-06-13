# Manage Unity Catalog permissions

DataMuru compiles roles and assignments from `governance/rbac.yml` into
permission-binding resources.

## Define a role

```yaml
rbac:
  roles:
    - id: curated_reader
      name: Curated Reader
      permissions:
        - resource_type: catalog
          resource_pattern: "*"
          privilege: USE CATALOG
        - resource_type: schema
          resource_pattern: "*.curated"
          privilege: SELECT
```

## Assign the role

```yaml
  assignments:
    - principal: data-consumers
      type: group
      roles:
        - curated_reader
      domains:
        - analytics
```

## Configure a SQL warehouse

Live ACL discovery and application require a SQL warehouse ID:

```yaml
sql_warehouse_id_env: DATABRICKS_SQL_WAREHOUSE_ID
```

## Plan one binding

```powershell
datamuru plan --target permission_binding:data-consumers:curated_reader
```

## Apply and verify

```powershell
datamuru apply --target permission_binding:data-consumers:curated_reader --auto-approve
datamuru plan --target permission_binding:data-consumers:curated_reader
```

The second plan should be stable after live grants match the compiled role.

Current live ACL support covers catalog and schema grants. Use exact
Databricks-supported privilege names.
