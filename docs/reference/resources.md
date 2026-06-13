# Resource types and addresses

| Type | Address example | Live alpha behavior |
| --- | --- | --- |
| `workspace` | `workspace:dev` | local-only descriptor |
| `catalog` | `catalog:analytics` | create and delete |
| `schema` | `schema:analytics.raw` | create and delete |
| `permission_binding` | `permission_binding:group:role` | catalog and schema grants |
| `taxonomy` | `taxonomy:enterprise` | local-only descriptor |
| `classification` | `classification:pii` | local-only descriptor |
| `rbac_role` | `rbac_role:reader` | local-only descriptor |
| `column_mask` | `column_mask:partial` | local-only descriptor |
| `user` | `user:person@company.com` | Enterprise identity lifecycle |
| `group` | `group:data-consumers` | existing OSS reference; managed Enterprise lifecycle |
| `service_principal` | `service_principal:etl-app` | Enterprise identity lifecycle |
| `group_membership` | `group_membership:data-consumers:user:person@company.com` | Enterprise identity lifecycle |

Use the full address with `--target`. See
[Targets](../guides/target-resources.md).
