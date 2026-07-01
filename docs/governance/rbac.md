# RBAC Model

Role-based access control is represented in the alpha through `governance/rbac.yml`.

## Current concepts

- Roles
- Permission declarations
- Role inheritance
- Principal assignments
- Domain scoping

## Compilation behavior

The alpha compiler converts:

- roles into `rbac_role` resources
- assignments into `permission_binding` resources

This gives the planning engine a stable way to include access intent in desired state calculations.

## Practical role patterns

### Catalog reader

```yaml
roles:
  catalog_reader:
    permissions:
      - object_type: catalog
        privileges: [USE_CATALOG]
```

Use this for principals that need to see and traverse a catalog but should not
create schemas or tables by default.

### Schema writer

```yaml
roles:
  schema_writer:
    permissions:
      - object_type: schema
        privileges: [USE_SCHEMA, CREATE_TABLE, MODIFY]
```

Use this for a delivery team that owns tables inside a reviewed schema.

### Domain-scoped role with multiple principals

```yaml
assignments:
  - role: schema_writer
    principals:
      - data-engineers
      - service-principal-etl
    scope:
      catalog: finance
      schema: curated
```

Generated plans include the compiled permission binding so reviewers can see
the target object, principal list, and privilege set before any live grant is
applied.

## Supported Databricks grant scope

| Scope | Status | Notes |
| --- | --- | --- |
| Catalog grants | Partial | Supported for selected Unity Catalog privileges. |
| Schema grants | Partial | Supported for selected Unity Catalog privileges. |
| Table, view, function, volume, and column grants | Roadmap | Model carefully, but do not assume live enforcement in `0.5.1a0`. |

Common privilege names include `USE_CATALOG`, `USE_SCHEMA`, `CREATE_SCHEMA`,
`CREATE_TABLE`, `MODIFY`, `SELECT`, `EXECUTE`, `READ_VOLUME`, and
`WRITE_VOLUME`. Provider acceptance still depends on the Databricks object type
and the permissions of the configured principal.

## Why this is useful now

Even before real provider enforcement exists, the RBAC model already provides:

- a stable config contract
- a testable planning surface
- a documentation surface for future contributors and customers
