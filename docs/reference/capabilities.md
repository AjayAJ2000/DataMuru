# Current capabilities and limits

This page describes DataMuru OSS `0.1.0a0`.

## Implemented

- project initialization;
- configuration validation and provider diagnostics;
- local state backend;
- deterministic plan, target, apply, destroy, and saved-plan workflows;
- PAT-based live workspace connectivity;
- live catalog and schema observation, creation, and deletion;
- catalog creation with managed locations or Databricks default storage;
- live catalog and schema grants compiled from RBAC;
- workspace catalog, schema, and group discovery;
- generated starter workspace YAML;
- Python API and JSON output for selected commands.

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
- multi-workspace orchestration;
- AWS and GCP feature parity;
- automatic adoption without explicit targets or fingerprint review;
- ingestion, modeling, observability, and compliance implementations;
- transactional rollback;
- full provider coverage for every PRD resource.

Do not interpret a modeled or documented roadmap capability as a live
implementation.
