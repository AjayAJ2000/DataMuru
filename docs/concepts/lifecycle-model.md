# Lifecycle Model

DataMuru separates resource intent from provider execution. That distinction is
important for understanding why some resources are live-managed today while
others are modeled for governance or future provider behavior.

## Resource lifecycle states

| State | Meaning | Example |
| --- | --- | --- |
| Declared | YAML describes the desired resource. | A catalog in `workspaces/*.yml`. |
| Planned | DataMuru compared desired state with local and observed state. | `+ catalog:dm_sales`. |
| Applied locally | State changed without provider mutation. | Taxonomy or RBAC role metadata. |
| Applied live | Provider API or SQL changed the platform. | Catalog, schema, or grant creation. |
| Observed live | Provider read existing platform state. | Existing catalog detected in Databricks. |
| Adopted | Existing live resource was recorded into state after explicit review. | Imported catalog accepted into local state. |
| Destroyed | DataMuru removed a managed resource when explicitly confirmed. | Test schema deleted. |

## Why local-only resources exist

Some resources are useful before they have live provider effects. For example,
taxonomy, classification, masking definitions, and RBAC role declarations help
DataMuru reason about governance intent even when the current provider adapter
only applies a subset of that intent.

Local-only resources are not fake. They are part of the declared contract and
can influence compiled resources, validation, and future provider behavior.

## Live resources

The current alpha can apply selected Databricks resources:

- catalogs;
- schemas;
- Unity Catalog grants compiled from RBAC assignments;
- Enterprise identity resources when account SCIM capability is available.

Live resources require the correct execution mode and provider capability.
`live-readonly` observes; `live-apply` mutates supported resources.

## Adoption versus creation

Creation means DataMuru changes the provider to match declared config.

Adoption means DataMuru records an existing provider resource into state only
after explicit target review. Adoption is intentionally conservative:

- it requires explicit targets;
- it compares fingerprints;
- it reports conflicts;
- it does not mutate Databricks.

Use adoption for brownfield resources. Use apply for greenfield resources.

## Failure model

Apply is not globally transactional. A parent resource can fail and cause
dependent child resources to be skipped. DataMuru reports structured failure
metadata so automation and operators can identify the recovery path.

Example:

```text
FAILED schema:dm_sales.raw: DMR-APPLY-1001 Skipped because parent catalog 'dm_sales' failed earlier in this apply.
```

Fix the parent issue, rerun `plan`, and apply the narrow target again.
