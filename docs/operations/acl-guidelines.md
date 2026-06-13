# ACL And RBAC Guidelines

DataMuru's current Databricks ACL support is intentionally narrow and testable.

## What the alpha slice supports

- grant and revoke for catalog privileges
- grant and revoke for schema privileges
- live grant discovery for declared `permission_binding` resources
- drift-aware planning for missing grants on declared bindings

## What the alpha slice does not support yet

- Databricks Free Edition user provisioning
- Databricks Free Edition group provisioning
- full grant import into state without an explicit YAML declaration
- object-level grants beyond catalog and schema

## Recommended workflow

1. Declare roles and assignments in `governance/rbac.yml`.
2. Point `domains` at the target catalog names.
3. Configure a Databricks SQL warehouse ID in `providers/databricks.yml`.
4. Run `datamuru doctor` first.
5. Run a targeted plan for one binding at a time.
6. Apply the same target only after the plan looks correct.

## Why SQL warehouse configuration matters

DataMuru currently uses Databricks SQL statement execution for:

- `GRANT`
- `REVOKE`
- `SHOW GRANTS`

That means live ACL discovery and apply need either:

- `sql_warehouse_id`, or
- `sql_warehouse_id_env`

in the Databricks provider configuration.

## Safe testing pattern

- use an existing principal in Databricks Free Edition, such as your workspace email
- test one `permission_binding` target at a time
- verify the result in the Databricks catalog or schema Permissions tab
- avoid broad live applies until the workspace declaration is fully curated

## Drift expectations

Current drift behavior is focused on declared bindings:

- if the declared grants already exist live, the plan should show `noop`
- if one or more declared grants are missing, the plan should show `update`
- if a previously managed binding is removed from YAML and still exists in local state, the plan can produce a `destroy`

This keeps the alpha slice predictable for teams adopting brownfield Databricks workspaces gradually.
