# Workspace configuration

Each `workspaces/*.yml` file must contain a top-level `workspace` mapping.

## Workspace fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Logical workspace name |
| `cloud` | enum | yes | `azure`, `aws`, or `gcp` |
| `region` | string | yes | Provider region label |
| `tier` | string | no | Informational workspace tier |
| `catalogs` | list | no | Catalog declarations |
| `principals` | mapping | no | User, group, and service-principal declarations |

## Catalogs

A catalog may be a string in internal normalization or an object:

```yaml
- name: analytics
  managed_location: abfss://container@account.dfs.core.windows.net/analytics
  use_default_storage: false
  schemas:
    - raw
    - name: curated
      managed_location: abfss://container@account.dfs.core.windows.net/analytics/curated
```

Use either `managed_location` or `use_default_storage` according to your
Databricks setup.

## Principals

Principals must be nested under `workspace`.

String entries are existing references:

```yaml
principals:
  groups:
    - existing-data-consumers
```

Object entries support lifecycle metadata:

```yaml
principals:
  users:
    - email: analyst@company.com
      display_name: Data Analyst
      lifecycle: managed
      allow_delete: false
```

Lifecycle values are `existing`, `managed`, and `external`. Managed lifecycle is
an Enterprise feature and requires account SCIM capability.
