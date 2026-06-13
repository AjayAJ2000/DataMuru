# Governance Overview

Governance is central to the product identity of DataMuru. Even in the alpha, governance is modeled as a first-class part of the desired state.

## Included in the current alpha

- Taxonomy compilation
- RBAC compilation
- Masking compilation

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
