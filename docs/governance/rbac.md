# RBAC Model

Role-based access control is represented in the alpha through `governance/rbac.yml`.

## Current concepts

- Roles
- Permission declarations
- Role inheritance
- Principal assignments
- Domain scoping

## Example roles

Catalog reader:

```yaml
roles:
  catalog_reader:
    permissions:
      - scope: catalog
        privileges:
          - USE_CATALOG
```

Schema writer:

```yaml
roles:
  schema_writer:
    permissions:
      - scope: schema
        privileges:
          - USE_SCHEMA
          - CREATE_TABLE
```

Domain-scoped analyst role with multiple principals:

```yaml
assignments:
  - role: catalog_reader
    principals:
      - group:data-analysts
      - service_principal:reporting-job
    scope:
      catalog: analytics

  - role: schema_writer
    principals:
      - group:analytics-engineers
    scope:
      catalog: analytics
      schema: mart
```

## Supported Databricks privilege names

The current Databricks grant compiler is intended for catalog-level and
schema-level Unity Catalog permissions, including common privileges such as:

- `USE_CATALOG`
- `USE_SCHEMA`
- `CREATE_SCHEMA`
- `CREATE_TABLE`
- `SELECT`
- `MODIFY`

Object-level table, view, function, volume, and column grants are not supported
as live provider operations in the current alpha. Model them as roadmap
requirements and track them outside DataMuru until provider support lands.

## Compilation behavior

The alpha compiler converts:

- roles into `rbac_role` resources
- assignments into `permission_binding` resources

This gives the planning engine a stable way to include access intent in desired state calculations.

Example compiled resource addresses include:

```text
rbac_role:catalog_reader
permission_binding:analytics.catalog_reader.group:data-analysts
permission_binding:analytics.mart.schema_writer.group:analytics-engineers
```

## Why this is useful now

Even before real provider enforcement exists, the RBAC model already provides:

- a stable config contract
- a testable planning surface
- a documentation surface for future contributors and customers

For the full status matrix, see
[Current capabilities and limits](../reference/capabilities-limits.md).
