# Schemas and Config Files

The repository currently publishes starter schema artifacts under `schemas/`.

## Included schema files

- `datamuru.schema.json`
- `workspace.schema.json`
- `taxonomy.schema.json`
- `rbac.schema.json`

## Current role of schemas

In this alpha, schemas act as:

- published contract artifacts
- a documentation surface for config shape
- a bridge between editor tooling and the runtime validator

The runtime validator is stricter than basic shape validation. It also catches
cross-file and product-safety issues, including duplicate environments,
duplicate catalogs and schemas, workspace/provider cloud mismatches,
system-owned schema declarations, and RBAC assignments that reference unknown
roles.

## Related config files

The runtime starter config set includes:

- `datamuru.yml`
- `environments/dev.yml`
- `providers/databricks.yml`
- `workspaces/alpha-dev.yml`
- `governance/taxonomy.yml`
- `governance/rbac.yml`
- `governance/masking.yml`

## Managed identities

Enterprise projects can declare managed identities under `workspace.principals`.

```yaml
workspace:
  name: enterprise-platform
  cloud: azure
  region: eastus2
  principals:
    users:
      - email: analyst@your-company.com
        lifecycle: managed
        allow_delete: false
    groups:
      - name: data-consumers
        lifecycle: managed
        members:
          users:
            - analyst@your-company.com
    service_principals:
      - name: sp-data-pipelines
        lifecycle: managed
```

Managed identities require `features.identity_management: true`. String entries remain backward-compatible references.

## Databricks provider runtime keys

The current Databricks provider config includes operational keys that matter for package users:

- `cloud`
- `credential_mode`
- `execution_mode`
- `auth_type`
- `token_env`
- `host`
- `connect_timeout_seconds`

### `execution_mode`

Current alpha values:

- `state-only`
  Default local modeling mode. No live probe, no live mutation.
- `live-readonly`
  Enables safe connectivity probing in `doctor`, allows live observation of workspace, groups, catalogs, and schemas during planning, but still blocks mutations.
- `live-apply`
  Enables supported live mutations. The current surface includes Unity Catalog catalogs and schemas, ACL permission bindings, and Enterprise identity resources when account SCIM capability is available.

## Workspace catalog and schema options

Catalog entries support:

- `name`
- `managed_location`
- `schemas`

Schema entries support either:

- a simple string such as `raw`
- or a mapping with:
  - `name`
  - `managed_location`

Example:

```yaml
workspace:
  name: alpha-dev
  cloud: azure
  region: eastus2
  catalogs:
    - name: alpha_marketing
      managed_location: abfss://catalog-root@storageaccount.dfs.core.windows.net/alpha_marketing
      schemas:
        - raw
        - name: curated
          managed_location: abfss://schema-root@storageaccount.dfs.core.windows.net/alpha_marketing/curated
```

## Product expectation

For an international SaaS-grade product, published schemas should evolve in lockstep with:

- docs
- validation behavior
- examples
- release notes
