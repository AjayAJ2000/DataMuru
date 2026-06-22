# Governance Overview

Governance is central to the product identity of DataMuru. Even in the alpha, governance is modeled as a first-class part of the desired state.

## Included in the current alpha

- **Supported:** RBAC intent compiles into permission bindings.
- **Partial:** catalog-level and schema-level Unity Catalog grants can be
  applied in Databricks when the provider runs in `live-apply` with a SQL
  warehouse.
- **Experimental:** taxonomy and masking definitions compile into local
  governance resources.
- **Roadmap:** live column masks, row filters, and broad object-level policy
  enforcement.

## Why this matters early

Starting governance in the bootstrap gives the framework three advantages:

1. Governance concepts become part of the data model, not a post-hoc extension.
2. Provider and plan logic can evolve with governance in mind.
3. Documentation and schemas can establish the language of control early.

## Current enforcement boundary

DataMuru compiles RBAC assignments into live catalog and schema grants when a
SQL warehouse is configured and the provider runs in `live-apply`. Taxonomy,
classification, and masking remain local governance resources in the OSS
alpha. See [Current capabilities and limits](../reference/capabilities.md).

## Example governance intent

```yaml
roles:
  catalog_reader:
    permissions:
      - object_type: catalog
        privileges: [USE_CATALOG]
  schema_writer:
    permissions:
      - object_type: schema
        privileges: [USE_SCHEMA, CREATE_TABLE]

assignments:
  - role: catalog_reader
    principals: [data-analysts]
    scope:
      catalog: analytics
  - role: schema_writer
    principals: [data-engineers]
    scope:
      catalog: analytics
      schema: curated
```

The compiler turns these declarations into stable `permission_binding`
resources. In `state-only` mode they are planned locally. In supported
Databricks `live-apply` flows they become catalog or schema grants.
