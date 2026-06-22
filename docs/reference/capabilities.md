# Current capabilities and limits

This page describes DataMuru OSS `0.4.0a0`. Treat it as the canonical status
reference for current product capability claims.

Status terms used across the docs:

| Status | Meaning |
| --- | --- |
| Supported | Implemented and covered by tests for the stated scope. |
| Partial | Implemented for a bounded subset of providers, resources, or modes. |
| Experimental | Available for evaluation, but APIs, outputs, or behavior may change. |
| Enterprise | Requires DataMuru Enterprise features or commercial activation. |
| Roadmap | Planned or designed, but not implemented in the OSS alpha. |
| Not supported | Not available in the current release. |

## Capability matrix

| Capability | Status | Current scope |
| --- | --- | --- |
| Project initialization | Supported | Generates a local project scaffold and safe default execution mode. |
| Configuration validation | Supported | Root, provider, workspace, environment, and governance configuration. |
| Provider diagnostics | Supported | CLI doctor checks with structured output for configured providers. |
| Local state backend | Supported | JSON state files with no remote locking. |
| Remote state readiness inspection | Experimental | Configuration and planning boundary checks only. |
| Hosted control plane handoff | Experimental | Contract and architecture export, not hosted tenant provisioning. |
| Deterministic plan/apply/destroy | Partial | Local state and supported Databricks resources. |
| Saved plans and targets | Supported | Reviewable plan artifacts and targeted execution. |
| Databricks connectivity | Supported | PAT-based workspace connectivity. |
| Databricks catalogs and schemas | Partial | Observe, create, update planned metadata, and delete supported objects. |
| Databricks Unity Catalog grants | Partial | Catalog and schema grants compiled from RBAC. |
| Workspace discovery/import | Partial | Supported catalog, schema, and group discovery with reviewable YAML. |
| Governance taxonomy and masking | Experimental | Validated and compiled as local intent, no live policy enforcement. |
| Python API | Supported | Selected command engine surfaces and structured results. |
| Enterprise identity lifecycle | Enterprise | Requires Enterprise configuration and Databricks account SCIM support. |
| Production cloud state backends | Roadmap | Names reserved; implementation not complete. |
| Broad multi-workspace orchestration | Roadmap | Not available in the OSS alpha. |
| Transactional rollback | Not supported | Manual recovery and provider cleanup remain required. |

## Local-only modeling

These compile into resources but do not yet install live Databricks behavior:

- workspace provisioning;
- taxonomy and classification enforcement;
- column masking;
- RBAC role objects independent of compiled grants.

## Enterprise boundary

Managed users, groups, service principals, and group memberships require:

- DataMuru Enterprise configuration;
- `features.identity_management: true`;
- Databricks account SCIM support;
- an authorized account principal.

OSS can reference existing principals for Unity Catalog permissions.

## Not yet complete

- production cloud state backends;
- hosted control plane tenant provisioning;
- multi-workspace orchestration;
- AWS and GCP feature parity;
- automatic adoption without explicit targets or fingerprint review;
- ingestion, modeling, observability, and compliance implementations;
- transactional rollback;
- full provider coverage for every PRD resource.

Do not interpret a modeled or documented roadmap capability as a live
implementation.
