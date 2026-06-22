# Governance Overview

Governance is central to the product identity of DataMuru. Even in the alpha, governance is modeled as a first-class part of the desired state.

## Status summary

| Area | Current status |
| --- | --- |
| RBAC roles and permission bindings | Partial: compiled into plan resources, with live catalog/schema grants where supported |
| Catalog and schema Unity Catalog grants | Partial: live through Databricks when a SQL warehouse and permissions are available |
| Taxonomy and classification | Roadmap: validated and compiled as local governance intent |
| Column masking | Roadmap: local intent only; no live Databricks column-mask installation yet |
| Managed account identities | Enterprise: requires Enterprise config and Databricks account SCIM |

## Why this matters early

Starting governance in the bootstrap gives the framework three advantages:

1. Governance concepts become part of the data model, not a post-hoc extension.
2. Provider and plan logic can evolve with governance in mind.
3. Documentation and schemas can establish the language of control early.

## Current enforcement boundary

DataMuru compiles RBAC assignments into live catalog and schema grants when a
SQL warehouse is configured and the provider runs in `live-apply`. Taxonomy,
classification, and masking remain local governance resources in the OSS alpha.
See [Current capabilities and limits](../reference/capabilities-limits.md).
