# Current capabilities and limits

This page is the canonical capability status reference for DataMuru OSS
`0.4.0a0`. Other documentation should link here instead of restating full
capability matrices.

Status terms:

- **Supported**: implemented and covered by normal tests for the alpha surface.
- **Partial**: implemented for a bounded provider, resource type, or mode.
- **Experimental**: available for evaluation with extra review.
- **Roadmap**: planned or modeled but not live behavior.
- **Enterprise**: requires Enterprise configuration, extension, or hosted
  workflow.
- **Not supported**: intentionally unavailable in the current alpha.

## Core workflow

| Capability | Status | Notes |
| --- | --- | --- |
| Project initialization | Supported | `datamuru init` creates a local starter project. |
| Configuration validation | Supported | Includes cross-file and edition-aware validation. |
| Provider diagnostics | Supported | `doctor` checks supported provider readiness. |
| Local JSON state | Supported | Default OSS backend. Do not commit state files. |
| Remote state backends | Roadmap | `s3`, `azure_blob`, and `gcs` are recognized contracts only. |
| State backend readiness inspection | Supported | `datamuru state inspect` reports local/remote posture. |
| Plan, target, apply, destroy | Supported | Deterministic engine with explicit destructive confirmation. |
| Saved plans | Supported | Includes stale-configuration checks. |
| Transactional rollback | Not supported | Operators must plan rollback/cleanup manually. |

## Databricks provider

| Capability | Status | Notes |
| --- | --- | --- |
| PAT-based workspace connectivity | Supported | Prefer `host_env`, `token_env`, and `sql_warehouse_id_env`. |
| CLI profile authentication | Partial | Supports Databricks CLI profiles where configured. |
| Catalog observation/create/delete | Partial | Supported for selected Unity Catalog catalog workflows. |
| Schema observation/create/delete | Partial | Supported for selected schema workflows. |
| Default-storage catalog creation | Partial | Requires SQL warehouse ID and workspace support. |
| Unity Catalog grants from RBAC | Partial | Catalog-level and schema-level grants are supported where provider allows. |
| Object-level table/view/volume grants | Not supported | Modeled as future scope; do not claim live enforcement. |
| Broad Databricks object coverage | Not supported | DataMuru does not manage every Databricks object. |

## Import and adoption

| Capability | Status | Notes |
| --- | --- | --- |
| Workspace catalog/schema discovery | Supported | Use scoped `--catalog` filters for safer enterprise imports. |
| Grant discovery | Partial | Requires SQL warehouse and configured scan budgets. |
| Enterprise review suite generation | Supported | Writes review YAML for workspace, RBAC, taxonomy, and masking. |
| Explicit targeted adoption | Supported | `import adopt --target ...` can write local state after exact fingerprint review. |
| Automatic broad ownership adoption | Not supported | DataMuru does not automatically adopt every discovered object. |

## Governance

| Capability | Status | Notes |
| --- | --- | --- |
| Taxonomy declarations | Partial | Validated and compiled as governance intent. |
| RBAC roles and permission bindings | Partial | Compiled into plan resources; grants are live for supported catalog/schema scopes. |
| Multiple principal bindings | Partial | Existing principals can be referenced for supported grants. |
| Domain-scoped roles | Partial | Modeled in YAML and planning; live effect depends on compiled grants. |
| Classification declarations | Roadmap | Local governance intent, not live provider enforcement. |
| Column masking definitions | Roadmap | Compiled locally; live Databricks column masks are not installed. |

## Snowflake and migration

| Capability | Status | Notes |
| --- | --- | --- |
| Snowflake state-only modeling | Experimental | Provider-neutral planning scaffold. |
| Snowflake live-readonly discovery | Experimental | Requires `datamuru[snowflake]`. |
| Databricks-to-Snowflake mapping drafts | Experimental | Reviewable contract only; no data movement. |
| Snowflake live apply | Not supported | Roadmap/provider-extension scope. |

## Enterprise boundary

| Capability | Status | Notes |
| --- | --- | --- |
| Enterprise activation readiness check | Enterprise | Local preflight; does not call a license server. |
| Activation handoff bundle export | Enterprise | Redacted JSON artifact. |
| Activation audit evidence export | Enterprise | Redacted audit/onboarding evidence artifact. |
| Hosted control plane contract | Enterprise | Handoff contract only. |
| Hosted control plane architecture export | Enterprise | Reference architecture artifact only. |
| Tenant provisioning | Roadmap | Not implemented in OSS. |
| Purchase/license activation flow | Roadmap | Remaining 0.5 milestone scope. |
| Managed account identities | Enterprise | Requires Enterprise configuration and Databricks account SCIM. |
| Full multi-workspace orchestration | Roadmap | Not available in the OSS alpha. |
